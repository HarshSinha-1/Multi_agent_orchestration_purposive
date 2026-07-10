from __future__ import annotations
import os
import time
import uuid
from typing import Any, Literal, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field, model_validator
from langgraph.graph import END, START, StateGraph

from orchestrator.groq_client import groq_client
from shared.utils.logging import get_logger

logger = get_logger(__name__)

# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class AgentMetadata(BaseModel):
    processing_time: float = Field(..., ge=0.0)
    confidence_score: float = Field(..., ge=0.0, le=1.0)

AgentStatus = Literal["COMPLETED", "FAILED", "NEEDS_HUMAN"]

class AgentResponse(BaseModel):
    agent_id: str
    status: AgentStatus
    data: dict[str, Any] = Field(default_factory=dict)
    metadata: AgentMetadata

    @model_validator(mode="after")
    def data_required_on_completed(self) -> "AgentResponse":
        if self.status == "COMPLETED" and not self.data:
            raise ValueError("'data' must be non-empty when status is COMPLETED")
        return self

# ── State Graph TypedDict ─────────────────────────────────────────────────────

class OrchestratorState(TypedDict):
    query: str
    domain: Literal["hr", "it", "sales", "executive"]
    response: Optional[AgentResponse]
    trace: list[str]

# ── Helper to build response ──────────────────────────────────────────────────

def _build_response(
    agent_id: str,
    status: AgentStatus,
    data: dict[str, Any],
    processing_time: float,
    confidence_score: float,
) -> AgentResponse:
    return AgentResponse(
        agent_id=agent_id,
        status=status,
        data=data,
        metadata=AgentMetadata(
            processing_time=processing_time,
            confidence_score=confidence_score,
        ),
    )

# ── Node Implementations ──────────────────────────────────────────────────────

def hr_node(state: OrchestratorState) -> dict:
    """Processes HR-related chat requests using Groq."""
    t0 = time.perf_counter()
    logger.info("Executing HR Orchestrator Node...")
    
    system_prompt = (
        "You are the HR Specialist Agent. You manage recruitment, resume screening, and job inquiries. "
        "Provide a detailed, helpful, and professional response to the user query. "
        "Keep your output structured, clear, and focused on HR topics. If the user asks to screen a candidate, "
        "give details about the process."
    )
    
    messages = [{"role": "user", "content": state["query"]}]
    content = groq_client.chat_completion(messages, system_prompt=system_prompt)
    
    response = _build_response(
        agent_id="hr_agent",
        status="COMPLETED",
        data={"answer": content},
        processing_time=time.perf_counter() - t0,
        confidence_score=0.9
    )
    return {
        "response": response,
        "trace": state.get("trace", []) + ["hr_node"]
    }

def it_node(state: OrchestratorState) -> dict:
    """Processes IT-related chat requests using Groq."""
    t0 = time.perf_counter()
    logger.info("Executing IT Orchestrator Node...")
    
    system_prompt = (
        "You are the IT Support & Incident Resolution Agent. You triage tickets, analyze log errors, and provide "
        "root-cause analysis (RCA) recommendations. Keep your output professional and technical, offering step-by-step "
        "troubleshooting or escalation info where needed."
    )
    
    messages = [{"role": "user", "content": state["query"]}]
    content = groq_client.chat_completion(messages, system_prompt=system_prompt)
    
    response = _build_response(
        agent_id="it_agent",
        status="COMPLETED",
        data={"answer": content},
        processing_time=time.perf_counter() - t0,
        confidence_score=0.92
    )
    return {
        "response": response,
        "trace": state.get("trace", []) + ["it_node"]
    }

def sales_node(state: OrchestratorState) -> dict:
    """Processes Sales-related chat requests using Groq."""
    t0 = time.perf_counter()
    logger.info("Executing Sales Orchestrator Node...")
    
    system_prompt = (
        "You are the Sales and Proposals Agent. You assist with lead management, proposal generation, and client insights. "
        "Keep your output persuasive, client-centric, and clear, with clear calls-to-action or next steps."
    )
    
    messages = [{"role": "user", "content": state["query"]}]
    content = groq_client.chat_completion(messages, system_prompt=system_prompt)
    
    response = _build_response(
        agent_id="sales_agent",
        status="COMPLETED",
        data={"answer": content},
        processing_time=time.perf_counter() - t0,
        confidence_score=0.88
    )
    return {
        "response": response,
        "trace": state.get("trace", []) + ["sales_node"]
    }

def executive_node(state: OrchestratorState) -> dict:
    """Processes Executive-related requests using Groq, utilizing aggregated metrics."""
    t0 = time.perf_counter()
    logger.info("Executing Executive Orchestrator Node...")
    
    # Query current metrics from the database for rich context
    from sqlmodel import Session, select
    from shared.db import engine
    from agents.executive_agent.models import KPISnapshot
    
    metrics_summary = "No metrics snapshot available yet."
    with Session(engine) as session:
        snapshots = session.exec(select(KPISnapshot)).all()
        if snapshots:
            metrics_summary = "\n".join([
                f"- {s.source_agent.upper()} Metric '{s.metric_name}': {s.metric_value} (as of {s.snapshot_date})"
                for s in snapshots
            ])
            
    system_prompt = (
        "You are the Executive Decisions Agent. You synthesize KPIs and trend reports to answer strategic questions. "
        "Use the current dashboard metrics provided below to formulate your answers. Make your insights concise, "
        "analytical, and actionable for senior leadership.\n\n"
        f"### Current Dashboard Metrics:\n{metrics_summary}"
    )
    
    messages = [{"role": "user", "content": state["query"]}]
    content = groq_client.chat_completion(messages, system_prompt=system_prompt)
    
    response = _build_response(
        agent_id="executive_agent",
        status="COMPLETED",
        data={"answer": content},
        processing_time=time.perf_counter() - t0,
        confidence_score=0.95
    )
    return {
        "response": response,
        "trace": state.get("trace", []) + ["executive_node"]
    }

# ── Router function ───────────────────────────────────────────────────────────

def router(state: OrchestratorState) -> str:
    """Routes to the node matching the selected domain."""
    domain = state.get("domain", "hr")
    if domain == "hr":
        return "hr_node"
    elif domain == "it":
        return "it_node"
    elif domain == "sales":
        return "sales_node"
    elif domain == "executive":
        return "executive_node"
    return "hr_node"

# ── Graph Construction ────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(OrchestratorState)
    
    # Add nodes
    graph.add_node("hr_node", hr_node)
    graph.add_node("it_node", it_node)
    graph.add_node("sales_node", sales_node)
    graph.add_node("executive_node", executive_node)
    
    # Conditional routing from START
    graph.add_conditional_edges(
        START,
        router,
        {
            "hr_node": "hr_node",
            "it_node": "it_node",
            "sales_node": "sales_node",
            "executive_node": "executive_node"
        }
    )
    
    # Connect nodes to END
    graph.add_edge("hr_node", END)
    graph.add_edge("it_node", END)
    graph.add_edge("sales_node", END)
    graph.add_edge("executive_node", END)
    
    return graph.compile()

# Build the compiled graph once
app = build_graph()

def run_pipeline(query: str, domain: Literal["hr", "it", "sales", "executive"]) -> AgentResponse:
    """Runs the multi-agent graph orchestration pipeline for a given query and domain."""
    initial_state: OrchestratorState = {
        "query": query,
        "domain": domain,
        "response": None,
        "trace": []
    }
    final_state = app.invoke(initial_state)
    return final_state["response"]
