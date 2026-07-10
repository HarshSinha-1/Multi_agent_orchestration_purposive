import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import Session, select
from pydantic import BaseModel, Field
from agents.sales_agent.models import Lead, Proposal, Insight
from orchestrator.groq_client import groq_client
from orchestrator.tools.scoring_tool import score_lead
from shared.utils.logging import get_logger

logger = get_logger(__name__)

# --- Pydantic structures for LLM calls ---
class SentimentAnalysisResult(BaseModel):
    sentiment: str = Field(..., description="Must be one of: 'Positive', 'Neutral', 'Negative'")
    key_needs: list[str] = Field(default_factory=list, description="Primary requirements extracted from context")

class ProposalDraftResult(BaseModel):
    pricing_tier: str = Field(..., description="pricing tier, e.g. Enterprise, Standard, Basic")
    estimated_value: float = Field(..., description="numerical estimated contract value in USD")
    key_points: list[str] = Field(default_factory=list, description="key deliverables or summary points")

# --- Service Functions ---

def ingest_lead(
    session: Session, 
    customer_name: str, 
    industry: str, 
    pain_points: str, 
    budget_range: str, 
    previous_interactions: str, 
    company_offering: str
) -> Lead:
    """Ingests a new sales lead from CRM system."""
    lead_id = f"lead_{uuid.uuid4().hex[:8]}"
    db_lead = Lead(
        lead_id=lead_id,
        customer_name=customer_name,
        industry=industry,
        pain_points=pain_points,
        budget_range=budget_range,
        previous_interactions=previous_interactions,
        company_offering=company_offering,
        created_at=datetime.utcnow()
    )
    session.add(db_lead)
    session.commit()
    session.refresh(db_lead)
    logger.info(f"Ingested Lead: {db_lead.customer_name} ({db_lead.lead_id})")
    return db_lead

def generate_insight(session: Session, lead_id: str) -> Insight:
    """Performs sentiment analysis and key needs extraction on a sales lead using Groq."""
    lead = session.exec(select(Lead).where(Lead.lead_id == lead_id)).first()
    if not lead:
        raise ValueError(f"Lead with ID {lead_id} not found.")

    needs_summary = (
        f"Industry: {lead.industry}\n"
        f"Pain Points: {lead.pain_points}\n"
        f"Previous Interactions: {lead.previous_interactions}\n"
        f"Company Offering: {lead.company_offering}"
    )

    system_prompt = (
        "You are a sales intelligence agent. Analyze the provided needs context of a customer. "
        "Determine the overall customer sentiment ('Positive', 'Neutral', or 'Negative') and extract "
        "a bulleted list of their primary needs."
    )
    user_prompt = f"Customer Name: {lead.customer_name}\nContext:\n{needs_summary}"
    messages = [{"role": "user", "content": user_prompt}]

    try:
        analysis = groq_client.structured_chat(
            messages=messages,
            system_prompt=system_prompt,
            response_schema=SentimentAnalysisResult
        )
        sentiment = analysis.sentiment
        key_needs = "\n".join([f"- {need}" for need in analysis.key_needs])
    except Exception as e:
        logger.error(f"Error analyzing lead insight {lead_id}: {e}")
        sentiment = "Neutral"
        key_needs = f"- Focus on general pain points: {lead.pain_points}"

    insight_id = f"ins_{uuid.uuid4().hex[:8]}"
    db_insight = Insight(
        insight_id=insight_id,
        lead_id=lead_id,
        sentiment=sentiment,
        key_needs=key_needs,
        generated_at=datetime.utcnow()
    )
    session.add(db_insight)
    session.commit()
    session.refresh(db_insight)
    logger.info(f"Generated Insight {db_insight.insight_id} for Lead {lead_id}")
    return db_insight

def generate_proposal(session: Session, lead_id: str, product_line: str) -> Proposal:
    """Uses lead scoring tool and Groq structured chat to generate a personalized proposal document."""
    lead = session.exec(select(Lead).where(Lead.lead_id == lead_id)).first()
    if not lead:
        raise ValueError(f"Lead with ID {lead_id} not found.")

    needs_summary = (
        f"Industry: {lead.industry}\n"
        f"Pain Points: {lead.pain_points}\n"
        f"Previous Interactions: {lead.previous_interactions}\n"
        f"Company Offering: {lead.company_offering}"
    )

    # 1. Evaluate lead value and tier using scoring tool
    scoring = score_lead(needs_summary, lead.budget_range)

    # 2. Use Groq to draft specific proposal deliverables/key points
    system_prompt = (
        "You are a business proposal writer. Based on the customer's needs and recommended tier, "
        "generate key delivery points for a proposal. Output the pricing tier, estimated value, and key points."
    )
    user_prompt = (
        f"Customer: {lead.customer_name}\n"
        f"Needs Context:\n{needs_summary}\n"
        f"Product Line: {product_line}\n"
        f"Recommended Tier: {scoring.recommended_tier}\n"
        f"Calculated Close Probability: {scoring.close_probability:.2%}"
    )
    messages = [{"role": "user", "content": user_prompt}]

    try:
        draft = groq_client.structured_chat(
            messages=messages,
            system_prompt=system_prompt,
            response_schema=ProposalDraftResult
        )
        pricing_tier = draft.pricing_tier
        estimated_value = draft.estimated_value
        key_points = ",".join(draft.key_points)
    except Exception as e:
        logger.error(f"Error drafting proposal for lead {lead_id}: {e}")
        pricing_tier = scoring.recommended_tier
        estimated_value = scoring.estimated_deal_value
        key_points = "Automated system setup,Initial setup consulting,12 weeks implementation"

    proposal_id = f"prop_{uuid.uuid4().hex[:8]}"
    db_proposal = Proposal(
        proposal_id=proposal_id,
        lead_id=lead_id,
        pricing_tier=pricing_tier,
        estimated_value=estimated_value,
        key_points=key_points,
        generated_at=datetime.utcnow()
    )
    session.add(db_proposal)
    session.commit()
    session.refresh(db_proposal)
    logger.info(f"Generated Proposal {db_proposal.proposal_id} for Lead {lead_id} valued at ${db_proposal.estimated_value}")
    return db_proposal

def get_proposal(session: Session, proposal_id: str) -> Optional[Proposal]:
    """Retrieves a proposal by ID."""
    return session.exec(select(Proposal).where(Proposal.proposal_id == proposal_id)).first()
