import pytest
from sqlmodel import Session
from agents.executive_agent.service import get_kpis, get_trends

def test_get_kpis_defaults(session: Session):
    kpis = get_kpis(session, "last_7_days")
    assert kpis["range"] == "last_7_days"
    assert "hr" in kpis
    assert "it" in kpis
    assert "sales" in kpis
    
    # Check default fallbacks are present
    assert kpis["hr"]["open_positions"] == 0
    assert kpis["it"]["avg_mttr_minutes"] == 47.0
    assert kpis["sales"]["win_rate"] == 0.31

def test_get_trends_empty(session: Session):
    trends = get_trends(session, "open_positions")
    assert trends == []
