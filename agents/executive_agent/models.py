from datetime import date
from sqlmodel import SQLModel, Field

class KPISnapshot(SQLModel, table=True):
    snapshot_id: int = Field(default=None, primary_key=True)
    source_agent: str     # hr, it, sales
    metric_name: str      # e.g. open_positions, win_rate
    metric_value: float
    snapshot_date: date
