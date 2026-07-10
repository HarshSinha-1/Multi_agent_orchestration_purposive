import pytest
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
