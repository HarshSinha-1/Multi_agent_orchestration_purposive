import pytest
from sqlmodel import Session
from agents.it_agent.service import submit_ticket, get_ticket

def test_submit_ticket(session: Session):
    ticket = submit_ticket(
        session=session,
        affected_service="payment-gateway",
        description="Transaction API timed out with 504 gateway timeout error.",
        severity="HIGH"
    )
    assert ticket.ticket_id.startswith("tkt_")
    assert ticket.status == "open"
    assert ticket.severity == "HIGH"
    assert ticket.affected_service == "payment-gateway"

def test_get_ticket_not_found(session: Session):
    t = get_ticket(session, "tkt_dummy")
    assert t is None
