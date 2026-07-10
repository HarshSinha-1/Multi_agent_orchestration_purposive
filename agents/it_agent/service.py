import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import Session, select
from pydantic import BaseModel, Field
from agents.it_agent.models import Ticket, RCAReport
from orchestrator.groq_client import groq_client
from orchestrator.tools.embedding_tool import embed_and_store, similarity_search
from shared.utils.logging import get_logger

logger = get_logger(__name__)

# --- Pydantic structures for LLM triage/RCA calls ---
class TriageResult(BaseModel):
    severity: str = Field(..., description="Must be one of: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'")
    reasoning: str = Field(..., description="Reason for this classification")

class RCADiagnosis(BaseModel):
    root_cause: str = Field(..., description="Technical explanation of the error source")
    matched_known_issue: Optional[str] = Field(None, description="Known Issue ID if applicable, e.g. KI-0092")
    auto_remediated: bool = Field(..., description="True if issue was auto-recovered/fixed by runbooks")
    recommended_fix: str = Field(..., description="Recommended manual fix steps")

# --- Service Functions ---

def submit_ticket(session: Session, affected_service: str, description: str, severity: str = "LOW") -> Ticket:
    """Submits a new support incident ticket."""
    ticket_id = f"tkt_{uuid.uuid4().hex[:8]}"
    db_ticket = Ticket(
        ticket_id=ticket_id,
        affected_service=affected_service,
        severity=severity.upper(),
        status="open",
        description=description,
        created_at=datetime.utcnow()
    )
    session.add(db_ticket)
    session.commit()
    session.refresh(db_ticket)
    logger.info(f"Submitted Ticket: {db_ticket.ticket_id} (Service: {db_ticket.affected_service})")
    return db_ticket

def triage_ticket(session: Session, ticket_id: str) -> Ticket:
    """Automates ticket triage: classifies severity based on description using Groq."""
    ticket = session.exec(select(Ticket).where(Ticket.ticket_id == ticket_id)).first()
    if not ticket:
        raise ValueError(f"Ticket with ID {ticket_id} not found.")

    system_prompt = (
        "You are an automated IT triage system. Read the ticket details and determine the severity "
        "('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'). CRITICAL is for outage of core services (e.g. checkout, database down). "
        "HIGH is for performance degradation. MEDIUM is for minor features. LOW is for visual bugs or queries."
    )
    user_prompt = f"Service: {ticket.affected_service}\nDescription: {ticket.description}"
    messages = [{"role": "user", "content": user_prompt}]

    try:
        triage_res = groq_client.structured_chat(
            messages=messages,
            system_prompt=system_prompt,
            response_schema=TriageResult
        )
        ticket.severity = triage_res.severity.upper()
        session.add(ticket)
        session.commit()
        session.refresh(ticket)
        logger.info(f"Triaged Ticket {ticket_id}: Severity set to {ticket.severity}")
    except Exception as e:
        logger.error(f"Error triaging ticket {ticket_id}: {e}")
        # Default to high on failure to be safe
        ticket.severity = "HIGH"
        session.add(ticket)
        session.commit()
        
    return ticket

def generate_rca(session: Session, ticket_id: str, logs: str) -> RCAReport:
    """Indexes logs in ChromaDB, matches past incidents, and generates Root Cause Analysis using Groq."""
    ticket = session.exec(select(Ticket).where(Ticket.ticket_id == ticket_id)).first()
    if not ticket:
        raise ValueError(f"Ticket with ID {ticket_id} not found.")

    # 1. Embed raw logs in ChromaDB collection
    embed_and_store(
        text=logs,
        doc_id=ticket_id,
        collection_name="it_incidents",
        metadata={"affected_service": ticket.affected_service}
    )

    # 2. Similarity search in ChromaDB to find similar past incident reports
    past_incidents = similarity_search(
        query=logs[:1000], # query with log signature
        collection_name="it_incidents",
        n_results=2
    )

    past_context = ""
    if past_incidents:
        past_context = "\n### Similar Past Incidents:\n" + "\n".join([
            f"- Incident {m['id']}: {m['content'][:300]}" for m in past_incidents if m['id'] != ticket_id
        ])

    # 3. Call Groq for structured RCA analysis
    system_prompt = (
        "You are a Site Reliability Engineer (SRE). Review the ticket description, current error logs, "
        "and any similar historical incidents to diagnose the root cause. Explain the cause, decide if "
        "it can be auto-remediated, specify a matched known issue ID if applicable, and offer remediation recommendations."
    )
    user_prompt = (
        f"### Ticket Description:\n{ticket.description}\n\n"
        f"### Affected Service:\n{ticket.affected_service}\n\n"
        f"### Raw Incident Logs:\n{logs}\n"
        f"{past_context}"
    )
    messages = [{"role": "user", "content": user_prompt}]

    try:
        diagnosis = groq_client.structured_chat(
            messages=messages,
            system_prompt=system_prompt,
            response_schema=RCADiagnosis
        )
    except Exception as e:
        logger.error(f"Error diagnosing ticket {ticket_id} via LLM: {e}")
        diagnosis = RCADiagnosis(
            root_cause=f"Unable to diagnose: processing error ({e})",
            matched_known_issue=None,
            auto_remediated=False,
            recommended_fix="Review logs manually."
        )

    # 4. Save RCAReport
    report_id = f"rca_{uuid.uuid4().hex[:8]}"
    db_report = RCAReport(
        report_id=report_id,
        ticket_id=ticket_id,
        root_cause=diagnosis.root_cause,
        matched_known_issue=diagnosis.matched_known_issue,
        auto_remediated=diagnosis.auto_remediated,
        recommended_fix=diagnosis.recommended_fix,
        generated_at=datetime.utcnow()
    )
    session.add(db_report)
    
    # Update Ticket Status
    ticket.status = "resolved" if diagnosis.auto_remediated else "in_progress"
    session.add(ticket)
    
    session.commit()
    session.refresh(db_report)
    logger.info(f"Generated RCA report {db_report.report_id} for ticket {ticket_id}")
    return db_report

def get_ticket(session: Session, ticket_id: str) -> Optional[Ticket]:
    """Retrieves a single ticket by ID."""
    return session.exec(select(Ticket).where(Ticket.ticket_id == ticket_id)).first()

def list_known_issues(session: Session) -> list[dict]:
    """Retrieves list of resolved issues with matching known issue patterns."""
    reports = session.exec(
        select(RCAReport)
        .where(RCAReport.matched_known_issue != None)
        .order_by(RCAReport.generated_at.desc())
    ).all()
    
    known_issues = []
    for r in reports:
        known_issues.append({
            "report_id": r.report_id,
            "ticket_id": r.ticket_id,
            "matched_known_issue": r.matched_known_issue,
            "root_cause": r.root_cause,
            "recommended_fix": r.recommended_fix
        })
    return known_issues
