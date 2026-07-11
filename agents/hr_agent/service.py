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
    """Creates a new job position in the database and syncs it to Notion."""
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

    # Sync to Notion via MCP Tool
    try:
        from orchestrator.tools.notion_tool import sync_job_to_notion
        sync_res = sync_job_to_notion(db_job)
        if sync_res.get("status") in ("created", "updated") and sync_res.get("page_id"):
            db_job.notion_page_id = sync_res["page_id"]
            session.add(db_job)
            session.commit()
            session.refresh(db_job)
            logger.info(f"Successfully synced Job to Notion: {db_job.notion_page_id}")
    except Exception as e:
        logger.error(f"Failed to sync newly created job to Notion: {e}")

    return db_job

def upload_resume(session: Session, file_bytes: bytes, filename: str, job_id: str) -> Candidate:
    """Parses a resume PDF, embeds it in ChromaDB, scores it, and persists the candidate record."""
    # Retrieve job requirements (Notion first, fallback to DB)
    from orchestrator.tools.notion_tool import fetch_job_from_notion
    notion_job = fetch_job_from_notion(job_id)
    if notion_job and notion_job.get("full_jd_text"):
        jd_to_use = notion_job["full_jd_text"]
        logger.info(f"Using Job description fetched from Notion database for screening.")
    else:
        logger.info(f"Falling back to local database for Job requirements.")
        job = session.exec(select(Job).where(Job.job_id == job_id)).first()
        if not job:
            raise ValueError(f"Job with ID {job_id} not found in Notion or local database.")
        jd_to_use = job.full_jd_text

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
    score_result = score_resume(resume_text, jd_to_use)

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

    # Sync to Notion via MCP Tool
    try:
        from orchestrator.tools.notion_tool import sync_candidate_to_notion
        sync_res = sync_candidate_to_notion(db_candidate)
        if sync_res.get("status") in ("created", "updated") and sync_res.get("page_id"):
            db_candidate.notion_page_id = sync_res["page_id"]
            session.add(db_candidate)
            session.commit()
            session.refresh(db_candidate)
            logger.info(f"Successfully synced Candidate to Notion: {db_candidate.notion_page_id}")
    except Exception as e:
        logger.error(f"Failed to sync newly uploaded candidate to Notion: {e}")

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
        # Retrieve job requirements (Notion first, fallback to DB)
        from orchestrator.tools.notion_tool import fetch_job_from_notion
        notion_job = fetch_job_from_notion(job_id)
        if notion_job and notion_job.get("full_jd_text"):
            jd_to_use = notion_job["full_jd_text"]
            logger.info(f"Using Job description fetched from Notion database for screening.")
        else:
            logger.info(f"Falling back to local database for Job requirements.")
            job = session.exec(select(Job).where(Job.job_id == job_id)).first()
            if not job:
                raise ValueError(f"Job with ID {job_id} not found in Notion or local database.")
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

    # Sync to Notion via MCP Tool
    try:
        from orchestrator.tools.notion_tool import sync_candidate_to_notion
        sync_res = sync_candidate_to_notion(db_candidate)
        if sync_res.get("status") in ("created", "updated") and sync_res.get("page_id"):
            db_candidate.notion_page_id = sync_res["page_id"]
            session.add(db_candidate)
            session.commit()
            session.refresh(db_candidate)
            logger.info(f"Successfully synced Candidate to Notion on screen: {db_candidate.notion_page_id}")
    except Exception as e:
        logger.error(f"Failed to sync screened candidate to Notion: {e}")

    return db_candidate

def list_jobs(session: Session) -> list[Job]:
    """
    Retrieves all job positions. Queries the Notion database directly via MCP 
    to ensure the roles listed are coming from the live MCP datasource.
    Falls back to local database if Notion query fails or is empty.
    """
    try:
        from mcp.notion_mcp_client import NotionMCPClient
        from mcp.config import NOTION_DATABASE_ID
        
        mcp_client = NotionMCPClient()
        logger.info(f"Fetching live job roles from Notion database {NOTION_DATABASE_ID} via MCP client...")
        res = mcp_client.call_tool("notion_query_database", {"database_id": NOTION_DATABASE_ID})
        results = res.get("results", [])
        
        if results:
            jobs_from_notion = []
            for page in results:
                props = page.get("properties", {})
                
                # Parse job_id (title type in Notion)
                id_list = props.get("job_id", {}).get("title", [])
                job_id = id_list[0].get("text", {}).get("content", "") if id_list else ""
                
                # Parse job_title (rich_text type in Notion)
                title_list = props.get("job_title", {}).get("rich_text", [])
                title = title_list[0].get("text", {}).get("content", "") if title_list else ""
                
                # Parse department (select type in Notion)
                dept_obj = props.get("department", {}).get("select", {})
                department = dept_obj.get("name", "General") if dept_obj else "General"
                
                # Parse full_jd_text (rich_text type in Notion)
                jd_list = props.get("full_jd_text", {}).get("rich_text", [])
                full_jd_text = jd_list[0].get("text", {}).get("content", "") if jd_list else ""
                
                # Parse notion_page_id
                notion_page_id = page.get("id")
                
                if job_id and title:
                    jobs_from_notion.append(Job(
                        job_id=job_id,
                        title=title,
                        department=department,
                        full_jd_text=full_jd_text,
                        notion_page_id=notion_page_id
                    ))
            
            if jobs_from_notion:
                logger.info(f"Loaded {len(jobs_from_notion)} live jobs directly from Notion MCP.")
                return jobs_from_notion

    except Exception as e:
        logger.error(f"Failed to query live jobs from Notion MCP: {e}. Falling back to local database.")

    logger.info("Using local SQLite database fallback for job roles list.")
    return list(session.exec(select(Job)).all())


