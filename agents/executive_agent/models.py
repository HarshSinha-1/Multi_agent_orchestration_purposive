from sqlmodel import SQLModel, Field
from typing import Optional

class KPISnapshot(SQLModel, table=True):
    snapshot_id: str = Field(primary_key=True)
    source_agent: str     # hr, it, sales
    metric_name: str      # e.g. open_positions, win_rate
    metric_value: float
    snapshot_date: str    # ISO date string e.g. '2026-07-10'
