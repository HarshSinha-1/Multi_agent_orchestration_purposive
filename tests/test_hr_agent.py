import pytest
from unittest.mock import patch
from sqlmodel import Session
from agents.hr_agent.service import create_job, get_shortlist, get_candidate


def test_create_job(session: Session):
    job = create_job(
        session=session,
        title="Test Backend Developer",
        department="Engineering",
        full_jd_text="Python, FastAPI, Docker"
    )
    assert job.job_id.startswith("job_")
    assert job.title == "Test Backend Developer"
    assert job.department == "Engineering"
    assert job.full_jd_text == "Python, FastAPI, Docker"

def test_get_shortlist_empty(session: Session):
    shortlist = get_shortlist(session, "job_dummy")
    assert shortlist == []

def test_get_candidate_not_found(session: Session):
    c = get_candidate(session, "cand_dummy")
    assert c is None

def test_list_jobs(session: Session):
    from agents.hr_agent.service import list_jobs
    create_job(
        session=session,
        title="Test QA Engineer",
        department="QA",
        full_jd_text="Writing unit tests and integration tests"
    )
    jobs = list_jobs(session)
    assert len(jobs) >= 1
    assert any(j.title == "Test QA Engineer" for j in jobs)

def test_notion_status_endpoint():
    from fastapi.testclient import TestClient
    from main import app
    
    client = TestClient(app)
    
    mock_query_response = {
        "results": [{"id": "mock_page_id"}]
    }
    
    with patch('mcp.notion_mcp_client.NotionMCPClient._execute_direct_api', return_value=mock_query_response) as mock_api:
        response = client.get("/api/v1/hr/notion-status")
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["status"] == "connected"
        mock_api.assert_called_once()


