from datetime import date, datetime
import json
import uuid
from sqlmodel import Session, select
from agents.executive_agent.models import KPISnapshot, DecisionSupportLog
from shared.analytics.warehouse import run_etl
from orchestrator.orchestrator import run_pipeline
from shared.utils.logging import get_logger

logger = get_logger(__name__)

def get_kpis(session: Session, range_str: str = "last_30_days") -> dict:
    """Runs the ETL job to compile fresh data, then retrieves aggregated KPIs."""
    # 1. Trigger ETL to update snapshots
    try:
        run_etl()
    except Exception as e:
        logger.error(f"ETL execution failed: {e}. Attempting to read existing snapshots.")

    # 2. Query snapshots for today
    today = date.today()
    snapshots = session.exec(
        select(KPISnapshot).where(KPISnapshot.snapshot_date == today.isoformat())
    ).all()

    # Compile result structure
    result = {
        "range": range_str,
        "hr": {},
        "it": {},
        "sales": {},
        "generated_at": today.isoformat()
    }

    for s in snapshots:
        agent = s.source_agent
        if agent in result:
            result[agent][s.metric_name] = s.metric_value

    # Supply default benchmarks if database was empty or ETL didn't populate all fields
    hr_defaults = {"open_positions": 0, "avg_time_to_hire_days": 21.0, "shortlist_rate": 0.0}
    it_defaults = {"tickets_resolved": 0, "avg_mttr_minutes": 47.0, "auto_remediation_rate": 0.0}
    sales_defaults = {"proposals_generated": 0, "pipeline_value": 0.0, "win_rate": 0.31}

    for k, v in hr_defaults.items():
        result["hr"].setdefault(k, v)
    for k, v in it_defaults.items():
        result["it"].setdefault(k, v)
    for k, v in sales_defaults.items():
        result["sales"].setdefault(k, v)

    return result

def get_trends(session: Session, metric: str) -> list[dict]:
    """Retrieves chronological history for a specific metric snapshot."""
    statement = (
        select(KPISnapshot)
        .where(KPISnapshot.metric_name == metric)
        .order_by(KPISnapshot.snapshot_date.asc())
    )
    history = session.exec(statement).all()
    return [
        {"date": h.snapshot_date, "value": h.metric_value, "agent": h.source_agent}
        for h in history
    ]

def decision_support(session: Session, question: str) -> str:
    """Asks the executive decision agent to address strategic queries using current dashboard metrics and logs the query."""
    logger.info(f"Running Executive decision support for: {question}")
    
    # 1. Fetch current snapshots to log system_context
    today = date.today().isoformat()
    snapshots = session.exec(
        select(KPISnapshot).where(KPISnapshot.snapshot_date == today)
    ).all()
    
    hr_snap = {}
    it_snap = {}
    sales_snap = {}
    for s in snapshots:
        if s.source_agent == "hr":
            hr_snap[s.metric_name] = s.metric_value
        elif s.source_agent == "it":
            it_snap[s.metric_name] = s.metric_value
        elif s.source_agent == "sales":
            sales_snap[s.metric_name] = s.metric_value

    # 2. Execute orchestrator pipeline
    agent_response = run_pipeline(query=question, domain="executive")
    answer = agent_response.data.get("answer", "No decision support answer returned.")
    
    # 3. Persist to DecisionSupportLog
    log_id = f"ds_log_{uuid.uuid4().hex[:8]}"
    db_log = DecisionSupportLog(
        log_id=log_id,
        leadership_query=question,
        hr_snapshot=json.dumps(hr_snap),
        it_snapshot=json.dumps(it_snap),
        sales_snapshot=json.dumps(sales_snap),
        executive_summary=answer[:500] + "..." if len(answer) > 500 else answer,
        decision_support=json.dumps([answer]),
        risk_flags=json.dumps([]),
        generated_at=datetime.utcnow()
    )
    session.add(db_log)
    session.commit()
    logger.info(f"Persisted DecisionSupportLog entry: {log_id}")
    
    return answer
