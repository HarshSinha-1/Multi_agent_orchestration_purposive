import os
from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./enterprise_agents.db")

# Create engine. For SQLite, we add connect_args to avoid sharing session threads issues.
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

def init_db():
    """Initializes all database tables by importing all SQLModel subclasses."""
    # Import agent models here to register them with SQLModel metadata
    from agents.hr_agent.models import Job, Candidate  # noqa: F401
    from agents.it_agent.models import Ticket, RCAReport  # noqa: F401
    from agents.sales_agent.models import Lead, Proposal, Insight  # noqa: F401
    from agents.executive_agent.models import KPISnapshot  # noqa: F401
    
    SQLModel.metadata.create_all(engine)

def get_session():
    """Dependency generator for database sessions."""
    with Session(engine) as session:
        yield session
