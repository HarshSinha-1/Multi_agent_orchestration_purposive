from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class Incident(SQLModel, table=True):
    incident_id: str = Field(primary_key=True)
    affected_service: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    status: str    # open, in_progress, resolved
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RCAReport(SQLModel, table=True):
    report_id: str = Field(primary_key=True)
    incident_id: str = Field(foreign_key="incident.incident_id")
    root_cause: str
    matched_known_issue: Optional[str] = None
    auto_remediated: bool
    business_impact_summary: str
    recommended_fix: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
