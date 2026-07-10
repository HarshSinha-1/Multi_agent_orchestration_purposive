from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class Job(SQLModel, table=True):
    job_id: str = Field(primary_key=True)
    title: str
    department: str
    requirements: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Candidate(SQLModel, table=True):
    candidate_id: str = Field(primary_key=True)
    job_id: str = Field(foreign_key="job.job_id")
    name: str
    resume_text: str
    match_score: float
    skills: str  # Comma-separated skills
    missing_skills: str  # Comma-separated missing skills
    recommendation: str
    summary: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
