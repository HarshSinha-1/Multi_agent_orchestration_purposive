import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import Session, select
from agents.hr_agent.models import Job, Candidate
from shared.utils.parsing import parse_resume_text
from orchestrator.tools.embedding_tool import embed_and_store
from orchestrator.tools.scoring_tool import score_resume
from shared.utils.logging import get_logger

logger = get_logger(__name__)

def create_job(session: Session, title: str, department: str, full_jd_text: str) -> Job:
    """Creates a new job position in the database."""
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    db_job = Job(
        job_id=job_id,
        title=title,
        department=department,
        full_jd_text=full_jd_text,
        created_at=datetime.utcnow()
    )
    session.add(db_job)
    session.commit()
    session.refresh(db_job)
    logger.info(f"Created Job: {db_job.title} ({db_job.job_id})")
    return db_job

def upload_resume(session: Session, file_bytes: bytes, filename: str, job_id: str) -> Candidate:
    """Parses a resume PDF, embeds it in ChromaDB, scores it, and persists the candidate record."""
    # Retrieve job requirements first
    job = session.exec(select(Job).where(Job.job_id == job_id)).first()
    if not job:
        raise ValueError(f"Job with ID {job_id} not found.")

    # 1. Parse text from PDF resume
    resume_text = parse_resume_text(file_bytes)
    if not resume_text:
        raise ValueError("Could not extract text from the resume.")

    # Extract name from filename or use a default
    candidate_name = filename.split(".")[0].replace("_", " ").title()
    candidate_id = f"cand_{uuid.uuid4().hex[:8]}"

    # 2. Store in ChromaDB vector store
    embed_and_store(
        text=resume_text,
        doc_id=candidate_id,
        collection_name="hr_resumes",
        metadata={"name": candidate_name, "job_id": job_id}
    )

    # 3. Call LLM scoring tool
    score_result = score_resume(resume_text, job.full_jd_text)

    # 4. Save Candidate to SQLite DB
    db_candidate = Candidate(
        candidate_id=candidate_id,
        job_id=job_id,
        name=candidate_name,
        resume_text=resume_text,
        match_score=score_result.match_score,
        skills=",".join(score_result.skill_matches),
        missing_skills=",".join(score_result.missing_skills),
        recommendation=score_result.recommendation,
        summary=score_result.summary,
        created_at=datetime.utcnow()
    )
    session.add(db_candidate)
    session.commit()
    session.refresh(db_candidate)
    logger.info(f"Ingested Candidate: {db_candidate.name} with score {db_candidate.match_score}")
    return db_candidate

def get_shortlist(session: Session, job_id: str) -> list[Candidate]:
    """Retrieves candidates sorted by match score for a job requisition."""
    statement = (
        select(Candidate)
        .where(Candidate.job_id == job_id)
        .order_by(Candidate.match_score.desc())
    )
    return list(session.exec(statement).all())

def get_candidate(session: Session, candidate_id: str) -> Optional[Candidate]:
    """Retrieves a single candidate detail."""
    return session.exec(select(Candidate).where(Candidate.candidate_id == candidate_id)).first()

def screen_resume(session: Session, job_id: str, resume_text: str, full_jd_text: Optional[str] = None) -> Candidate:
    """Performs dual-lookup screening: compares resume text against JD and stores the score in Candidate table."""
    jd_to_use = full_jd_text
    if not jd_to_use:
        job = session.exec(select(Job).where(Job.job_id == job_id)).first()
        if not job:
            raise ValueError(f"Job with ID {job_id} not found.")
        jd_to_use = job.full_jd_text

    candidate_id = f"cand_{uuid.uuid4().hex[:8]}"
    
    # Call LLM scoring tool
    score_result = score_resume(resume_text, jd_to_use)
    
    # Store parsed resume details
    db_candidate = Candidate(
        candidate_id=candidate_id,
        job_id=job_id,
        name="Screened Candidate",
        resume_text=resume_text,
        match_score=score_result.match_score,
        skills=",".join(score_result.skill_matches),
        missing_skills=",".join(score_result.missing_skills),
        recommendation=score_result.recommendation,
        summary=score_result.summary,
        created_at=datetime.utcnow()
    )
    session.add(db_candidate)
    session.commit()
    session.refresh(db_candidate)
    return db_candidate
