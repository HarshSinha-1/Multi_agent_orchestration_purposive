import pytest
from unittest.mock import patch, MagicMock
from sqlmodel import Session
from datetime import datetime

from agents.hr_agent.models import Job, Candidate
from orchestrator.tools.notion_tool import sync_job_to_notion, sync_candidate_to_notion

def test_sync_new_job_to_notion(session: Session):
    # Create local job
    job = Job(
        job_id="JOB-PY-TEST",
        title="Test Backend Dev",
        department="Engineering",
        full_jd_text="Python testing text",
        created_at=datetime.utcnow()
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    # Mock direct API inside NotionMCPClient
    mock_response = {
        "id": "new_notion_page_123",
        "url": "https://notion.so/new_notion_page_123"
    }

    with patch('mcp.notion_mcp_client.NotionMCPClient._execute_direct_api', return_value=mock_response) as mock_api:
        sync_res = sync_job_to_notion(job)
        assert sync_res["status"] == "created"
        assert sync_res["page_id"] == "new_notion_page_123"
        assert sync_res["url"] == "https://notion.so/new_notion_page_123"
        mock_api.assert_called_once()

def test_sync_existing_job_to_notion(session: Session):
    # Create local job with an existing notion_page_id
    job = Job(
        job_id="JOB-PY-TEST-2",
        title="Test Backend Dev 2",
        department="Engineering",
        full_jd_text="Python testing text",
        created_at=datetime.utcnow(),
        notion_page_id="existing_notion_page_456"
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    mock_response = {
        "id": "existing_notion_page_456",
        "url": "https://notion.so/existing_notion_page_456"
    }

    with patch('mcp.notion_mcp_client.NotionMCPClient._execute_direct_api', return_value=mock_response) as mock_api:
        sync_res = sync_job_to_notion(job)
        assert sync_res["status"] == "updated"
        assert sync_res["page_id"] == "existing_notion_page_456"
        mock_api.assert_called_once()
        assert mock_api.call_args[0][0] == "notion_update_page_properties"

def test_sync_candidate_to_notion(session: Session):
    # Create candidate
    cand = Candidate(
        candidate_id="CAND-TEST-001",
        job_id="JOB-PY-TEST",
        name="John Doe",
        resume_text="Excellent Python skills.",
        match_score=0.95,
        skills="Python,Testing",
        missing_skills="Docker",
        recommendation="shortlist",
        summary="Outstanding test candidate.",
        created_at=datetime.utcnow()
    )
    session.add(cand)
    session.commit()
    session.refresh(cand)

    mock_response = {
        "id": "cand_notion_page_789",
        "url": "https://notion.so/cand_notion_page_789"
    }

    with patch('mcp.notion_mcp_client.NotionMCPClient._execute_direct_api', return_value=mock_response) as mock_api:
        sync_res = sync_candidate_to_notion(cand)
        assert sync_res["status"] == "created"
        assert sync_res["page_id"] == "cand_notion_page_789"
        mock_api.assert_called_once()

def test_fetch_job_from_notion():
    from orchestrator.tools.notion_tool import fetch_job_from_notion

    mock_query_response = {
        "results": [
            {
                "id": "notion_page_abc123",
                "properties": {
                    "job_title": {
                        "rich_text": [{"text": {"content": "Notion Software Engineer"}}]
                    },
                    "department": {
                        "select": {"name": "Engineering"}
                    },
                    "full_jd_text": {
                        "rich_text": [{"text": {"content": "Notion JDs are fetched and mapped properly."}}]
                    }
                }
            }
        ]
    }

    with patch('mcp.notion_mcp_client.NotionMCPClient._execute_direct_api', return_value=mock_query_response) as mock_api:
        job_data = fetch_job_from_notion("JOB-PY-TEST")
        assert job_data is not None
        assert job_data["title"] == "Notion Software Engineer"
        assert job_data["department"] == "Engineering"
        assert job_data["full_jd_text"] == "Notion JDs are fetched and mapped properly."
        assert job_data["notion_page_id"] == "notion_page_abc123"
        mock_api.assert_called_once()

def test_list_jobs_from_notion(session: Session):
    from agents.hr_agent.service import list_jobs

    mock_query_response = {
        "results": [
            {
                "id": "notion_page_1",
                "properties": {
                    "job_id": {
                        "title": [{"text": {"content": "JOB-MAPPED-1"}}]
                    },
                    "job_title": {
                        "rich_text": [{"text": {"content": "Notion Product Manager"}}]
                    },
                    "department": {
                        "select": {"name": "Product"}
                    },
                    "full_jd_text": {
                        "rich_text": [{"text": {"content": "Manage products."}}]
                    }
                }
            }
        ]
    }

    with patch('mcp.notion_mcp_client.NotionMCPClient._execute_direct_api', return_value=mock_query_response) as mock_api:
        jobs = list_jobs(session)
        assert len(jobs) == 1
        assert jobs[0].job_id == "JOB-MAPPED-1"
        assert jobs[0].title == "Notion Product Manager"
        assert jobs[0].department == "Product"
        assert jobs[0].full_jd_text == "Manage products."
        assert jobs[0].notion_page_id == "notion_page_1"
        mock_api.assert_called_once()


