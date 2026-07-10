import os
from contextlib import asynccontextmanager
from typing import Literal, Optional
from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session

from shared.db import init_db, get_session
from orchestrator.orchestrator import run_pipeline

# Import services
import agents.hr_agent.service as hr_service
import agents.it_agent.service as it_service
import agents.sales_agent.service as sales_service
import agents.executive_agent.service as executive_service

# Import models for types
from agents.hr_agent.models import Job, Candidate
from agents.it_agent.models import Ticket, RCAReport
from agents.sales_agent.models import Lead, Proposal, Insight

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema
    init_db()
    yield

app = FastAPI(
    title="Enterprise Multi-Agent System API",
    version="1.0.0-prototype",
    lifespan=lifespan
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify Vercel domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Base router definitions ---
hr_router = APIRouter(prefix="/api/v1/hr", tags=["HR Agent"])
it_router = APIRouter(prefix="/api/v1/it", tags=["IT Agent"])
sales_router = APIRouter(prefix="/api/v1/sales", tags=["Sales Agent"])
exec_router = APIRouter(prefix="/api/v1/executive", tags=["Executive Agent"])
chat_router = APIRouter(prefix="/api/v1", tags=["Chat Routing"])

# --- Request Schemas ---
class JobCreate(BaseModel):
    title: str
    department: str
    requirements: str

class TicketCreate(BaseModel):
    affected_service: str
    description: str

class TicketRCARequest(BaseModel):
    logs: str

class LeadCreate(BaseModel):
    customer_name: str
    needs_summary: str
    budget_range: str

class ProposalCreate(BaseModel):
    lead_id: str
    product_line: str

class DecisionRequest(BaseModel):
    question: str

class ChatRequest(BaseModel):
    message: str
    agent: Literal["hr", "it", "sales", "executive"]

# --- 1. HR Agent Endpoints ---

@hr_router.post("/jobs", response_model=Job)
def create_job(payload: JobCreate, session: Session = Depends(get_session)):
    return hr_service.create_job(session, payload.title, payload.department, payload.requirements)

@hr_router.post("/resumes/upload", response_model=Candidate)
async def upload_resume(
    file: UploadFile = File(...),
    job_id: str = Form(...),
    session: Session = Depends(get_session)
):
    try:
        content_bytes = await file.read()
        return hr_service.upload_resume(session, content_bytes, file.filename, job_id)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal resume ingestion failure: {e}")

@hr_router.get("/candidates/shortlist", response_model=list[Candidate])
def get_shortlist(job_id: str, session: Session = Depends(get_session)):
    return hr_service.get_shortlist(session, job_id)

@hr_router.get("/candidates/{candidate_id}", response_model=Candidate)
def get_candidate(candidate_id: str, session: Session = Depends(get_session)):
    candidate = hr_service.get_candidate(session, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate

# --- 2. IT Agent Endpoints ---

@it_router.post("/tickets", response_model=Ticket)
def submit_ticket(payload: TicketCreate, session: Session = Depends(get_session)):
    return it_service.submit_ticket(session, payload.affected_service, payload.description)

@it_router.post("/tickets/{ticket_id}/triage", response_model=Ticket)
def triage_ticket(ticket_id: str, session: Session = Depends(get_session)):
    try:
        return it_service.triage_ticket(session, ticket_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))

@it_router.post("/tickets/{ticket_id}/rca", response_model=RCAReport)
def generate_rca(ticket_id: str, payload: TicketRCARequest, session: Session = Depends(get_session)):
    try:
        return it_service.generate_rca(session, ticket_id, payload.logs)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))

@it_router.get("/tickets/{ticket_id}", response_model=Ticket)
def get_ticket(ticket_id: str, session: Session = Depends(get_session)):
    ticket = it_service.get_ticket(session, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@it_router.get("/incidents/known-issues")
def list_known_issues(session: Session = Depends(get_session)):
    return it_service.list_known_issues(session)

# --- 3. Sales Agent Endpoints ---

@sales_router.post("/leads", response_model=Lead)
def ingest_lead(payload: LeadCreate, session: Session = Depends(get_session)):
    return sales_service.ingest_lead(session, payload.customer_name, payload.needs_summary, payload.budget_range)

@sales_router.post("/insights/{lead_id}", response_model=Insight)
def generate_insight(lead_id: str, session: Session = Depends(get_session)):
    try:
        return sales_service.generate_insight(session, lead_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))

@sales_router.post("/proposals/generate", response_model=Proposal)
def generate_proposal(payload: ProposalCreate, session: Session = Depends(get_session)):
    try:
        return sales_service.generate_proposal(session, payload.lead_id, payload.product_line)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))

@sales_router.get("/proposals/{proposal_id}", response_model=Proposal)
def get_proposal(proposal_id: str, session: Session = Depends(get_session)):
    proposal = sales_service.get_proposal(session, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal

# --- 4. Executive Agent Endpoints ---

@exec_router.get("/kpis")
def get_kpis(range: str = "last_30_days", session: Session = Depends(get_session)):
    return executive_service.get_kpis(session, range)

@exec_router.get("/trends")
def get_trends(metric: str, session: Session = Depends(get_session)):
    return executive_service.get_trends(session, metric)

@exec_router.post("/decision-support")
def decision_support(payload: DecisionRequest, session: Session = Depends(get_session)):
    answer = executive_service.decision_support(session, payload.question)
    return {"answer": answer}

# --- 5. Unified Chat routing Endpoint ---

@chat_router.post("/chat")
def unified_chat(payload: ChatRequest):
    """
    Unified chat endpoint. Renders the user queries statefully via the 
    Orchestration Graph under the selected agent's environment.
    """
    try:
        response = run_pipeline(query=payload.message, domain=payload.agent)
        return {
            "agent_id": response.agent_id,
            "status": response.status,
            "answer": response.data.get("answer", ""),
            "processing_time": response.metadata.processing_time,
            "confidence_score": response.metadata.confidence_score
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Orchestration failure: {e}")

# Mount Routers to Application
app.include_router(hr_router)
app.include_router(it_router)
app.include_router(sales_router)
app.include_router(exec_router)
app.include_router(chat_router)

@app.get("/")
def read_root():
    return {"status": "online", "message": "Enterprise Multi-Agent System Prototype running successfully."}
