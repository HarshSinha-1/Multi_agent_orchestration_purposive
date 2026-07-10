import pytest
from sqlmodel import Session
from agents.it_agent.service import submit_incident, get_incident

def test_submit_incident(session: Session):
    incident = submit_incident(
        session=session,
        affected_service="payment-gateway",
        description="Transaction API timed out with 504 gateway timeout error.",
        severity="HIGH"
    )
    assert incident.incident_id.startswith("inc_")
    assert incident.status == "open"
    assert incident.severity == "HIGH"
    assert incident.affected_service == "payment-gateway"

def test_get_incident_not_found(session: Session):
    i = get_incident(session, "inc_dummy")
    assert i is None
