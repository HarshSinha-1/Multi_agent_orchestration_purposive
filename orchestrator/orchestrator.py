from __future__ import annotations
import os
import time
import uuid
from typing import Any, Literal, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field, model_validator
from langgraph.graph import END, START, StateGraph

from sqlmodel import Session
from shared.db import engine
import agents.hr_agent.service as hr_service
import agents.it_agent.service as it_service
import agents.sales_agent.service as sales_service

from orchestrator.groq_client import groq_client
from shared.utils.logging import get_logger

logger = get_logger(__name__)

# ── Intent Detection Schemas ──────────────────────────────────────────────────

class HRIntentDetection(BaseModel):
    intent: Literal["create_job", "none"]
    title: Optional[str] = Field(None, description="Title of the job role to create")
    department: Optional[str] = Field(None, description="Department for the job")
    full_jd_text: Optional[str] = Field(None, description="Detailed job description text for the position")

class ITIntentDetection(BaseModel):
    intent: Literal["submit_incident", "generate_rca", "none"]
    affected_service: Optional[str] = Field(None, description="Service affected by the issue (e.g. checkout-service)")
    description: Optional[str] = Field(None, description="Symptom or description of the incident")
    incident_id: Optional[str] = Field(None, description="Incident ID for log analysis (e.g. inc_abcdef12)")
    logs: Optional[str] = Field(None, description="Error logs for root cause analysis")

class SalesIntentDetection(BaseModel):
    intent: Literal["ingest_lead", "generate_proposal", "none"]
    customer_name: Optional[str] = Field(None, description="Name of lead customer or company")
    industry: Optional[str] = Field(None, description="Industry domain of the client (e.g. FinTech)")
    pain_points: Optional[str] = Field(None, description="Key client problems / pain points to solve")
    budget_range: Optional[str] = Field(None, description="Budget range (e.g. $50,000 - $80,000)")
    previous_interactions: Optional[str] = Field(None, description="Context of past calls or interactions")
    company_offering: Optional[str] = Field(None, description="Services they are interested in (e.g. Migration)")
    lead_id: Optional[str] = Field(None, description="Lead ID to generate a proposal for")
    product_line: Optional[str] = Field(None, description="Specific product line/software name")

# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class AgentMetadata(BaseModel):
    processing_time: float = Field(..., ge=0.0)
    confidence_score: float = Field(..., ge=0.0, le=1.0)

AgentStatus = Literal["COMPLETED", "FAILED", "NEEDS_HUMAN"]

class AgentResponse(BaseModel):
    agent_id: str
    status: AgentStatus
    data: dict[str, Any] = Field(default_factory=dict)
    metadata: AgentMetadata

    @model_validator(mode="after")
    def data_required_on_completed(self) -> "AgentResponse":
        if self.status == "COMPLETED" and not self.data:
            raise ValueError("'data' must be non-empty when status is COMPLETED")
        return self

# ── State Graph TypedDict ─────────────────────────────────────────────────────

class OrchestratorState(TypedDict):
    query: str
    domain: Literal["hr", "it", "sales", "executive"]
    response: Optional[AgentResponse]
    trace: list[str]
    history: Optional[list[dict]]
    job_id: Optional[str]

# ── Helper to build response ──────────────────────────────────────────────────

def _build_response(
    agent_id: str,
    status: AgentStatus,
    data: dict[str, Any],
    processing_time: float,
    confidence_score: float,
) -> AgentResponse:
    return AgentResponse(
        agent_id=agent_id,
        status=status,
        data=data,
        metadata=AgentMetadata(
            processing_time=processing_time,
            confidence_score=confidence_score,
        ),
    )

# ── Node Implementations ──────────────────────────────────────────────────────

def _build_messages_with_history(state: OrchestratorState) -> list[dict]:
    messages = []
    if state.get("history"):
        for msg in state["history"]:
            role = msg.get("role", "user")
            if role == "agent":
                role = "assistant"
            messages.append({"role": role, "content": msg.get("content", "")})
    messages.append({"role": "user", "content": state["query"]})
    return messages

def hr_node(state: OrchestratorState) -> dict:
    """Processes HR-related chat requests using Groq and handles database jobs creation."""
    t0 = time.perf_counter()
    logger.info("Executing HR Orchestrator Node...")
    
    # 1. Intent Detection
    messages = [{"role": "user", "content": state["query"]}]
    action_context = ""
    try:
        hr_intent = groq_client.structured_chat(
            messages=messages,
            system_prompt="Determine if the user wants to create a new job position. If so, extract the parameters.",
            response_schema=HRIntentDetection
        )
        if hr_intent.intent == "create_job" and hr_intent.title and hr_intent.full_jd_text:
            dept = hr_intent.department or "General"
            with Session(engine) as session:
                job = hr_service.create_job(session, hr_intent.title, dept, hr_intent.full_jd_text)
                action_context = f"\n[DATABASE ACTION: Created job '{job.title}' with ID {job.job_id} in {job.department} department.]"
    except Exception as e:
        logger.error(f"HR Node intent detection failed: {e}")

    # 2. Retrieve job and candidate context if job_id is provided
    job_context = ""
    job_id = state.get("job_id")
    if job_id:
        from orchestrator.tools.notion_tool import fetch_job_from_notion
        notion_job = fetch_job_from_notion(job_id)
        jd_text = ""
        job_title = ""
        if notion_job and notion_job.get("full_jd_text"):
            jd_text = notion_job["full_jd_text"]
            job_title = notion_job.get("title", "")
            logger.info(f"Loaded job JD from Notion for HR chat context: {job_id}")
        else:
            with Session(engine) as session:
                from sqlmodel import select
                from agents.hr_agent.models import Job
                job = session.exec(select(Job).where(Job.job_id == job_id)).first()
                if job:
                    jd_text = job.full_jd_text
                    job_title = job.title
                    logger.info(f"Loaded job JD from DB fallback for HR chat context: {job_id}")
        
        if jd_text:
            job_context += f"\n[Selected Job Context (from live Notion MCP):\nJob ID: {job_id}\nJob Title: {job_title}\nJob Description:\n{jd_text}]\n"
            
        # Also fetch candidates screened for this job to give complete context
        with Session(engine) as session:
            from sqlmodel import select
            from agents.hr_agent.models import Candidate
            candidates = session.exec(select(Candidate).where(Candidate.job_id == job_id)).all()
            if candidates:
                job_context += "\n[Already Screened Candidates for this Job:\n"
                for cand in candidates:
                    job_context += (
                        f"- Name: {cand.name} (ID: {cand.candidate_id})\n"
                        f"  Match Score: {cand.match_score * 100:.0f}%\n"
                        f"  Recommendation: {cand.recommendation.upper()}\n"
                        f"  Skills: {cand.skills}\n"
                        f"  Missing: {cand.missing_skills}\n"
                        f"  Summary: {cand.summary}\n"
                    )
                job_context += "]"

    # 3. Conversational response
    system_prompt = (
        "You are the HR Specialist Agent. You manage recruitment, resume screening, and job inquiries. "
        "Provide a detailed, helpful, and professional response to the user query. "
        "Keep your output structured, clear, and focused on HR topics.\n"
        f"{job_context}"
        f"{action_context}"
    )
    
    messages = _build_messages_with_history(state)
    content = groq_client.chat_completion(messages, system_prompt=system_prompt)
    
    response = _build_response(
        agent_id="hr_agent",
        status="COMPLETED",
        data={"answer": content},
        processing_time=time.perf_counter() - t0,
        confidence_score=0.9
    )
    return {
        "response": response,
        "trace": state.get("trace", []) + ["hr_node"]
    }

def it_node(state: OrchestratorState) -> dict:
    """Processes IT-related chat requests using Groq and handles database incident submission / RCA diagnostics."""
    t0 = time.perf_counter()
    logger.info("Executing IT Orchestrator Node...")
    
    # 1. Intent Detection
    messages = [{"role": "user", "content": state["query"]}]
    action_context = ""
    try:
        it_intent = groq_client.structured_chat(
            messages=messages,
            system_prompt="Determine if the user wants to submit an incident or run root-cause analysis (RCA). Extract parameters.",
            response_schema=ITIntentDetection
        )
        if it_intent.intent == "submit_incident" and it_intent.description:
            service_name = it_intent.affected_service or "General Infrastructure"
            with Session(engine) as session:
                incident = it_service.submit_incident(session, service_name, it_intent.description)
                action_context = f"\n[DATABASE ACTION: Successfully submitted incident '{incident.incident_id}' for service '{incident.affected_service}' with status '{incident.status}'.]"
        elif it_intent.intent == "generate_rca" and it_intent.incident_id and it_intent.logs:
            with Session(engine) as session:
                rca = it_service.generate_rca(session, it_intent.incident_id, it_intent.logs)
                action_context = f"\n[DATABASE ACTION: Generated RCA report '{rca.report_id}' for incident '{rca.incident_id}'. Auto-remediated: {rca.auto_remediated}. Matched: {rca.matched_known_issue}.]"
    except Exception as e:
        logger.error(f"IT Node intent detection failed: {e}")

    # 2. Conversational response
    system_prompt = (
        "You are the IT Support & Incident Resolution Agent. You triage incidents, analyze log errors, and provide "
        "root-cause analysis (RCA) recommendations. Keep your output professional and technical, offering step-by-step "
        "troubleshooting or escalation info where needed.\n"
        f"{action_context}"
    )
    
    messages = _build_messages_with_history(state)
    content = groq_client.chat_completion(messages, system_prompt=system_prompt)
    
    response = _build_response(
        agent_id="it_agent",
        status="COMPLETED",
        data={"answer": content},
        processing_time=time.perf_counter() - t0,
        confidence_score=0.92
    )
    return {
        "response": response,
        "trace": state.get("trace", []) + ["it_node"]
    }

def sales_node(state: OrchestratorState) -> dict:
    """Processes Sales-related chat requests using Groq and handles database lead ingestion / proposal generation."""
    t0 = time.perf_counter()
    logger.info("Executing Sales Orchestrator Node...")
    
    # 1. Intent Detection
    messages = [{"role": "user", "content": state["query"]}]
    action_context = ""
    try:
        sales_intent = groq_client.structured_chat(
            messages=messages,
            system_prompt="Determine if the user wants to ingest a new sales lead or generate a proposal. Extract parameters.",
            response_schema=SalesIntentDetection
        )
        if sales_intent.intent == "ingest_lead" and sales_intent.customer_name and sales_intent.pain_points:
            budget = sales_intent.budget_range or "Not specified"
            industry = sales_intent.industry or "General"
            prev_interactions = sales_intent.previous_interactions or "None"
            offering = sales_intent.company_offering or "General Services"
            with Session(engine) as session:
                lead = sales_service.ingest_lead(
                    session, 
                    sales_intent.customer_name, 
                    industry, 
                    sales_intent.pain_points, 
                    budget, 
                    prev_interactions, 
                    offering
                )
                action_context = f"\n[DATABASE ACTION: Ingested lead '{lead.lead_id}' for customer '{lead.customer_name}'.]"
        elif sales_intent.intent == "generate_proposal" and sales_intent.lead_id:
            prod = sales_intent.product_line or "Cloud Enterprise Services"
            with Session(engine) as session:
                prop = sales_service.generate_proposal(session, sales_intent.lead_id, prod)
                action_context = f"\n[DATABASE ACTION: Generated proposal '{prop.proposal_id}' valued at ${prop.estimated_value} for lead '{prop.lead_id}' under tier '{prop.pricing_tier}'.]"
    except Exception as e:
        logger.error(f"Sales Node intent detection failed: {e}")

    # 2. Conversational response
    system_prompt = (
        "You are the Sales and Proposals Agent. You assist with lead management, proposal generation, and client insights. "
        "Keep your output persuasive, client-centric, and clear, with clear calls-to-action or next steps.\n"
        f"{action_context}"
    )
    
    messages = _build_messages_with_history(state)
    content = groq_client.chat_completion(messages, system_prompt=system_prompt)
    
    response = _build_response(
        agent_id="sales_agent",
        status="COMPLETED",
        data={"answer": content},
        processing_time=time.perf_counter() - t0,
        confidence_score=0.88
    )
    return {
        "response": response,
        "trace": state.get("trace", []) + ["sales_node"]
    }

def executive_node(state: OrchestratorState) -> dict:
    """Processes Executive-related requests using Groq, utilizing aggregated metrics."""
    t0 = time.perf_counter()
    logger.info("Executing Executive Orchestrator Node...")
    
    # Query current metrics from the database for rich context
    from sqlmodel import Session, select
    from shared.db import engine
    from agents.executive_agent.models import KPISnapshot
    
    metrics_summary = "No metrics snapshot available yet."
    with Session(engine) as session:
        snapshots = session.exec(select(KPISnapshot)).all()
        if snapshots:
            metrics_summary = "\n".join([
                f"- {s.source_agent.upper()} Metric '{s.metric_name}': {s.metric_value} (as of {s.snapshot_date})"
                for s in snapshots
            ])
            
    system_prompt = (
        "You are the Executive Decisions Agent. You synthesize KPIs and trend reports to answer strategic questions. "
        "Use the current dashboard metrics provided below to formulate your answers. Make your insights concise, "
        "analytical, and actionable for senior leadership.\n\n"
        f"### Current Dashboard Metrics:\n{metrics_summary}"
    )
    
    messages = _build_messages_with_history(state)
    content = groq_client.chat_completion(messages, system_prompt=system_prompt)
    
    response = _build_response(
        agent_id="executive_agent",
        status="COMPLETED",
        data={"answer": content},
        processing_time=time.perf_counter() - t0,
        confidence_score=0.95
    )
    return {
        "response": response,
        "trace": state.get("trace", []) + ["executive_node"]
    }

# ── Router function ───────────────────────────────────────────────────────────

def router(state: OrchestratorState) -> str:
    """Routes to the node matching the selected domain."""
    domain = state.get("domain", "hr")
    if domain == "hr":
        return "hr_node"
    elif domain == "it":
        return "it_node"
    elif domain == "sales":
        return "sales_node"
    elif domain == "executive":
        return "executive_node"
    return "hr_node"

# ── Graph Construction ────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(OrchestratorState)
    
    # Add nodes
    graph.add_node("hr_node", hr_node)
    graph.add_node("it_node", it_node)
    graph.add_node("sales_node", sales_node)
    graph.add_node("executive_node", executive_node)
    
    # Conditional routing from START
    graph.add_conditional_edges(
        START,
        router,
        {
            "hr_node": "hr_node",
            "it_node": "it_node",
            "sales_node": "sales_node",
            "executive_node": "executive_node"
        }
    )
    
    # Connect nodes to END
    graph.add_edge("hr_node", END)
    graph.add_edge("it_node", END)
    graph.add_edge("sales_node", END)
    graph.add_edge("executive_node", END)
    
    return graph.compile()

# Build the compiled graph once
app = build_graph()

def run_pipeline(
    query: str, 
    domain: Literal["hr", "it", "sales", "executive"], 
    history: Optional[list[dict]] = None,
    job_id: Optional[str] = None
) -> AgentResponse:
    """Runs the multi-agent graph orchestration pipeline for a given query and domain."""
    initial_state: OrchestratorState = {
        "query": query,
        "domain": domain,
        "response": None,
        "trace": [],
        "history": history,
        "job_id": job_id
    }
    final_state = app.invoke(initial_state)
    return final_state["response"]
