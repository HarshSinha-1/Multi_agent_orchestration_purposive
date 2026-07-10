from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class KPISnapshot(SQLModel, table=True):
    snapshot_id: str = Field(primary_key=True)
    source_agent: str     # hr, it, sales
    metric_name: str      # e.g. open_positions, win_rate
    metric_value: float
    snapshot_date: str    # ISO date string e.g. '2026-07-10'

class DecisionSupportLog(SQLModel, table=True):
    log_id: str = Field(primary_key=True)
    leadership_query: str
    hr_snapshot: str
    it_snapshot: str
    sales_snapshot: str
    executive_summary: str
    decision_support: str
    risk_flags: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
