from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class Lead(SQLModel, table=True):
    lead_id: str = Field(primary_key=True)
    customer_name: str
    needs_summary: str
    budget_range: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Proposal(SQLModel, table=True):
    proposal_id: str = Field(primary_key=True)
    lead_id: str = Field(foreign_key="lead.lead_id")
    pricing_tier: str       # Enterprise, Standard, Basic
    estimated_value: float  # Value in USD
    key_points: str         # Comma-separated list of highlights
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class Insight(SQLModel, table=True):
    insight_id: str = Field(primary_key=True)
    lead_id: str = Field(foreign_key="lead.lead_id")
    sentiment: str          # Positive, Neutral, Negative
    key_needs: str          # Bullet points or description
    generated_at: datetime = Field(default_factory=datetime.utcnow)
