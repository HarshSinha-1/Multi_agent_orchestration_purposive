"""
Anti-Gravity Multi-Agent Orchestration System
=============================================
Lead Architect: LangGraph Stateful Workflow
Agents: HR | IT | Sales | Executive
State enforced via Pydantic v2 + TypedDict
LangSmith tracing enabled via environment variables
"""

from __future__ import annotations

import os
import time
import uuid
from typing import Annotated, Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator
from typing_extensions import TypedDict

# ── LangGraph core ────────────────────────────────────────────────────────────
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages  # noqa: F401  (available for future use)

# ── LangSmith tracing (set env vars before running) ───────────────────────────
# export LANGCHAIN_TRACING_V2=true
# export LANGCHAIN_API_KEY=<your-key>
# export LANGCHAIN_PROJECT="anti-gravity-orchestrator"
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")   # flip to "true" when ready
os.environ.setdefault("LANGCHAIN_PROJECT", "anti-gravity-orchestrator")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  1.  PYDANTIC SCHEMAS  –  Communication Protocol (JSON Schema)             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class AgentMetadata(BaseModel):
    """Metadata envelope attached to every agent response."""
    processing_time: float = Field(..., ge=0.0, description="Wall-clock seconds")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="0.0 – 1.0")


AgentStatus = Literal["COMPLETED", "FAILED", "NEEDS_HUMAN"]


class AgentResponse(BaseModel):
    """
    Universal communication protocol.
    Every agent node MUST return a dict that validates against this model.
    """
    agent_id: str = Field(..., description="Unique identifier for this agent run")
    status: AgentStatus
    data: dict[str, Any] = Field(default_factory=dict)
    metadata: AgentMetadata

    @model_validator(mode="after")
    def data_required_on_completed(self) -> "AgentResponse":
        if self.status == "COMPLETED" and not self.data:
            raise ValueError("'data' must be non-empty when status is COMPLETED")
        return self


# ── Domain-specific data schemas (nested inside AgentResponse.data) ───────────

class HRData(BaseModel):
    candidate_id: str
    name: str
    skills: list[str] = Field(default_factory=list)
    experience_years: float = Field(ge=0)
    education_level: str
    fit_score: float = Field(ge=0.0, le=1.0)


class ITData(BaseModel):
    incident_id: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    root_cause: str
    affected_systems: list[str] = Field(default_factory=list)
    recommended_action: str
    mttr_estimate_hours: float = Field(ge=0)


class SalesData(BaseModel):
    lead_id: str
    company_name: str
    proposal_summary: str
    estimated_deal_value: float = Field(ge=0)
    next_steps: list[str] = Field(default_factory=list)
    close_probability: float = Field(ge=0.0, le=1.0)


class ExecutiveSummary(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: str
    hr_highlights: str
    it_highlights: str
    sales_highlights: str
    overall_health_score: float = Field(ge=0.0, le=1.0)
    recommendations: list[str] = Field(default_factory=list)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  2.  GLOBAL STATE  –  Single Source of Truth (TypedDict)                  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class AntiGravityState(TypedDict):
    """
    Master state object shared across all nodes.
    Each field maps to a validated Pydantic model (or None until populated).
    """
    hr_data:           Optional[AgentResponse]
    it_data:           Optional[AgentResponse]
    sales_data:        Optional[AgentResponse]
    executive_summary: Optional[AgentResponse]
    # Optional audit trail – append-only list of node names visited
    trace:             list[str]


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  3.  AGENT NODE IMPLEMENTATIONS                                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def _build_response(
    agent_id: str,
    status: AgentStatus,
    data: dict[str, Any],
    processing_time: float,
    confidence_score: float,
) -> AgentResponse:
    """Helper: constructs and validates the universal AgentResponse envelope."""
    return AgentResponse(
        agent_id=agent_id,
        status=status,
        data=data,
        metadata=AgentMetadata(
            processing_time=processing_time,
            confidence_score=confidence_score,
        ),
    )


# ── HR Node ──────────────────────────────────────────────────────────────────

def hr_node(state: AntiGravityState) -> dict:
    """
    HR Agent: Extracts candidate features from resumes.

    TODO (Production):
      • Replace stub data with real resume parsing via LangChain document loader.
      • Use structured output from an LLM (e.g. ChatOpenAI with .with_structured_output(HRData)).
      • Connect to your ATS / HRMS API for live candidate records.
    """
    t0 = time.perf_counter()

    # ── Stub: simulate candidate feature extraction ───────────────────────────
    hr_payload = HRData(
        candidate_id="CAND-2024-001",
        name="Priya Sharma",
        skills=["Python", "LangGraph", "Milvus", "FastAPI", "Docker"],
        experience_years=3.5,
        education_level="B.Tech – Computer Science",
        fit_score=0.87,
    )

    response = _build_response(
        agent_id="hr_agent",
        status="COMPLETED",
        data=hr_payload.model_dump(),
        processing_time=time.perf_counter() - t0,
        confidence_score=0.87,
    )

    return {
        "hr_data": response,
        "trace": state.get("trace", []) + ["hr_node"],
    }


# ── IT Node ───────────────────────────────────────────────────────────────────

def it_node(state: AntiGravityState) -> dict:
    """
    IT Agent: Root-Cause Analysis (RCA) on incident reports.

    TODO (Production):
      • Ingest incident logs via vector DB (Milvus / Chroma) with RAG.
      • Use similarity search over historical incidents for pattern matching.
      • Trigger PagerDuty / Jira tickets programmatically on CRITICAL severity.
    """
    t0 = time.perf_counter()

    # ── Stub: simulate RCA engine output ─────────────────────────────────────
    it_payload = ITData(
        incident_id="INC-20240701-042",
        severity="HIGH",
        root_cause="Memory leak in microservice `auth-svc` (v2.3.1) due to unclosed DB connections",
        affected_systems=["auth-svc", "api-gateway", "session-cache"],
        recommended_action="Roll back to auth-svc v2.2.9; patch connection pool config in v2.3.2",
        mttr_estimate_hours=4.5,
    )

    response = _build_response(
        agent_id="it_agent",
        status="COMPLETED",
        data=it_payload.model_dump(),
        processing_time=time.perf_counter() - t0,
        confidence_score=0.91,
    )

    return {
        "it_data": response,
        "trace": state.get("trace", []) + ["it_node"],
    }


# ── Sales Node ────────────────────────────────────────────────────────────────

def sales_node(state: AntiGravityState) -> dict:
    """
    Sales Agent: Proposal generation from CRM context.

    TODO (Production):
      • Pull lead data from Salesforce / HubSpot CRM API.
      • Use a prompt template + LLM to draft personalised proposals.
      • Score leads with a fine-tuned classifier trained on historical deal data.
    """
    t0 = time.perf_counter()

    # ── Stub: simulate CRM-backed proposal ───────────────────────────────────
    sales_payload = SalesData(
        lead_id="LEAD-SF-00892",
        company_name="NovaTech Solutions Pvt. Ltd.",
        proposal_summary=(
            "End-to-end AI platform deployment covering RAG-based knowledge management, "
            "agentic workflow automation, and real-time analytics dashboard."
        ),
        estimated_deal_value=1_250_000.00,
        next_steps=[
            "Schedule technical deep-dive with CTO (Week 1)",
            "Submit formal RFP response by Week 2",
            "Proof-of-concept delivery by Week 4",
        ],
        close_probability=0.73,
    )

    response = _build_response(
        agent_id="sales_agent",
        status="COMPLETED",
        data=sales_payload.model_dump(),
        processing_time=time.perf_counter() - t0,
        confidence_score=0.73,
    )

    return {
        "sales_data": response,
        "trace": state.get("trace", []) + ["sales_node"],
    }


# ── Executive Node ────────────────────────────────────────────────────────────

def executive_node(state: AntiGravityState) -> dict:
    """
    Executive Agent: Aggregates all agent outputs into a BI report.

    TODO (Production):
      • Feed the three AgentResponse payloads into an LLM summariser.
      • Output to Notion / Confluence / PDF via API.
      • Compute overall_health_score with a weighted formula over confidence scores.
    """
    t0 = time.perf_counter()

    hr_resp    = state.get("hr_data")
    it_resp    = state.get("it_data")
    sales_resp = state.get("sales_data")

    # Guard: require all upstream agents to have completed
    for label, resp in [("HR", hr_resp), ("IT", it_resp), ("Sales", sales_resp)]:
        if resp is None or resp.status != "COMPLETED":
            return {
                "executive_summary": _build_response(
                    agent_id="executive_agent",
                    status="FAILED",
                    data={"reason": f"{label} agent did not complete successfully"},
                    processing_time=time.perf_counter() - t0,
                    confidence_score=0.0,
                ),
                "trace": state.get("trace", []) + ["executive_node"],
            }

    # Weighted health score: HR 30% | IT 40% | Sales 30%
    health = (
        hr_resp.metadata.confidence_score    * 0.30
        + it_resp.metadata.confidence_score  * 0.40
        + sales_resp.metadata.confidence_score * 0.30
    )

    hr_d    = hr_resp.data
    it_d    = it_resp.data
    sales_d = sales_resp.data

    summary = ExecutiveSummary(
        generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        hr_highlights=(
            f"Top candidate: {hr_d['name']} | Fit Score: {hr_d['fit_score']:.0%} | "
            f"Key skills: {', '.join(hr_d['skills'][:3])}"
        ),
        it_highlights=(
            f"Active Incident [{it_d['severity']}]: {it_d['root_cause'][:80]}… | "
            f"Est. MTTR: {it_d['mttr_estimate_hours']}h"
        ),
        sales_highlights=(
            f"Pipeline Lead: {sales_d['company_name']} | "
            f"Deal: ₹{sales_d['estimated_deal_value']:,.0f} | "
            f"Close Prob: {sales_d['close_probability']:.0%}"
        ),
        overall_health_score=round(health, 3),
        recommendations=[
            f"Fast-track {hr_d['name']} to final interview round.",
            f"Prioritise rollback of auth-svc to resolve INC-20240701-042.",
            f"Assign senior AE to {sales_d['company_name']} for PoC.",
        ],
    )

    response = _build_response(
        agent_id="executive_agent",
        status="COMPLETED",
        data=summary.model_dump(),
        processing_time=time.perf_counter() - t0,
        confidence_score=health,
    )

    return {
        "executive_summary": response,
        "trace": state.get("trace", []) + ["executive_node"],
    }


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  4.  GRAPH DEFINITION  –  StateGraph wiring                               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def build_graph() -> StateGraph:
    """
    Constructs and compiles the Anti-Gravity StateGraph.

    Flow:
        START → hr_node ─┐
                it_node  ├─→ executive_node → END
               sales_node┘

    Note: HR, IT, Sales run sequentially here for simplicity.
    TODO: Wrap them in Send() / asyncio.gather() for true parallel fan-out.
    """
    graph = StateGraph(AntiGravityState)

    # Register nodes
    graph.add_node("hr_node",        hr_node)
    graph.add_node("it_node",        it_node)
    graph.add_node("sales_node",     sales_node)
    graph.add_node("executive_node", executive_node)

    # Wire edges: sequential pipeline
    graph.add_edge(START,            "hr_node")
    graph.add_edge("hr_node",        "it_node")
    graph.add_edge("it_node",        "sales_node")
    graph.add_edge("sales_node",     "executive_node")
    graph.add_edge("executive_node", END)

    return graph.compile()


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  5.  ENTRY POINT                                                           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def main() -> None:
    import json

    app = build_graph()

    # Print Mermaid diagram to stdout (paste at https://mermaid.live)
    print("-" * 60)
    print("GRAPH TOPOLOGY (Mermaid)")
    print("-" * 60)
    print(app.get_graph().draw_mermaid())
    print("-" * 60)

    # Initial state -- all agent slots are empty
    initial_state: AntiGravityState = {
        "hr_data":           None,
        "it_data":           None,
        "sales_data":        None,
        "executive_summary": None,
        "trace":             [],
    }

    print("\n[LAUNCH]  Invoking Anti-Gravity Orchestrator ...\n")
    final_state: AntiGravityState = app.invoke(initial_state)

    print("[OK]  Execution complete.")
    print(f"      Nodes visited: {' -> '.join(final_state['trace'])}\n")

    exec_summary = final_state["executive_summary"]
    if exec_summary and exec_summary.status == "COMPLETED":
        print("[REPORT]  EXECUTIVE SUMMARY")
        print("-" * 60)
        print(json.dumps(exec_summary.data, indent=2, default=str))
    else:
        print("[ERROR]  Executive node did not complete.")

    print("\n[STATE]  Full final state (agent_id + status only):")
    for key in ("hr_data", "it_data", "sales_data", "executive_summary"):
        resp: Optional[AgentResponse] = final_state.get(key)  # type: ignore
        if resp:
            print(f"  {key:22s} -> {resp.agent_id:20s} | {resp.status}")


if __name__ == "__main__":
    main()
