import pytest
from sqlmodel import Session
from agents.sales_agent.service import ingest_lead, get_proposal

def test_ingest_lead(session: Session):
    lead = ingest_lead(
        session=session,
        customer_name="Globex Corp",
        needs_summary="Requires automated supply chain dashboard integration.",
        budget_range="$50,000 - $100,000"
    )
    assert lead.lead_id.startswith("lead_")
    assert lead.customer_name == "Globex Corp"
    assert lead.needs_summary == "Requires automated supply chain dashboard integration."

def test_get_proposal_not_found(session: Session):
    p = get_proposal(session, "prop_dummy")
    assert p is None
