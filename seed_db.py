"""
seed_db.py — Database Seeder for Enterprise Multi-Agent System

Populates all agent tables with realistic sample data so agents have
reference data to compare inputs against and generate outputs from.

Run from the project root with the venv activated:
    python seed_db.py
"""
import sys
import os
import uuid
from datetime import datetime, timedelta

# Ensure project root is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session
from shared.db import engine, init_db
from agents.hr_agent.models import Job, Candidate
from agents.it_agent.models import Incident, RCAReport
from agents.sales_agent.models import Lead, Proposal, Insight
from agents.executive_agent.models import KPISnapshot


def seed_hr(session: Session):
    print("\n📋 Seeding HR Agent data...")

    # --- Jobs ---
    jobs = [
        Job(
            job_id="JOB-PY-001",
            title="Senior Python Backend Engineer",
            department="Engineering",
            full_jd_text=(
                "Required: Python 3.10+, FastAPI, PostgreSQL/SQLite, REST API design, Git. "
                "Preferred: LangChain/LangGraph, Docker, Redis, asyncio, pytest. "
                "Experience: 4+ years backend development. Soft skills: problem-solving, clear communication, ownership mindset."
            ),
            created_at=datetime.utcnow() - timedelta(days=30),
        ),
        Job(
            job_id="JOB-ML-002",
            title="Machine Learning Engineer",
            department="AI Research",
            full_jd_text=(
                "Required: Python, PyTorch or TensorFlow, Scikit-learn, model training, hyperparameter tuning, Git. "
                "Preferred: MLflow, Hugging Face Transformers, LLM fine-tuning, AWS SageMaker, vector databases. "
                "Experience: 3+ years in ML/AI. Soft skills: curiosity, collaboration, documentation discipline."
            ),
            created_at=datetime.utcnow() - timedelta(days=20),
        ),
        Job(
            job_id="JOB-FE-003",
            title="Frontend Engineer (React/Next.js)",
            department="Product",
            full_jd_text=(
                "Required: React 18+, Next.js, TypeScript, Vanilla CSS / Tailwind, REST API integration. "
                "Preferred: Framer Motion, Figma collaboration, Web Accessibility (WCAG), PWA, Storybook. "
                "Experience: 3+ years frontend. Soft skills: design eye, user empathy, communication."
            ),
            created_at=datetime.utcnow() - timedelta(days=10),
        ),
    ]
    for j in jobs:
        existing = session.get(Job, j.job_id)
        if not existing:
            session.add(j)
    session.commit()
    print(f"   ✅ Inserted {len(jobs)} job records.")

    # --- Candidates ---
    candidates = [
        Candidate(
            candidate_id="CAND-001",
            job_id="JOB-PY-001",
            name="Aisha Patel",
            resume_text=(
                "Aisha Patel — Senior Software Engineer, 5 years experience.\n"
                "Skills: Python, FastAPI, PostgreSQL, Docker, Redis, REST API design, pytest, Git, asyncio.\n"
                "Education: B.Tech Computer Science, IIT Mumbai.\n"
                "Experience: Built microservices for e-commerce at Flipkart (3yr), API development at Razorpay (2yr)."
            ),
            match_score=0.91,
            skills="Python,FastAPI,PostgreSQL,Docker,Redis,REST API,pytest,asyncio",
            missing_skills="LangChain,LangGraph",
            recommendation="shortlist",
            summary="Strong backend background with near-perfect skill match. Minor gap in LangChain tooling, which can be learned on-the-job.",
            created_at=datetime.utcnow() - timedelta(days=25),
        ),
        Candidate(
            candidate_id="CAND-002",
            job_id="JOB-PY-001",
            name="Rohan Mehta",
            resume_text=(
                "Rohan Mehta — Junior Python Developer, 1.5 years experience.\n"
                "Skills: Python, Flask, MySQL, basic REST APIs, Git.\n"
                "Education: BCA, Pune University.\n"
                "Experience: Django web apps at startup (1yr), freelance Python scripting (6 months)."
            ),
            match_score=0.45,
            skills="Python,Flask,MySQL,Git",
            missing_skills="FastAPI,PostgreSQL,Docker,Redis,asyncio,pytest,LangChain",
            recommendation="hold",
            summary="Early-career developer. Python fundamentals are present but lacks depth in required production frameworks and infrastructure tooling.",
            created_at=datetime.utcnow() - timedelta(days=22),
        ),
        Candidate(
            candidate_id="CAND-003",
            job_id="JOB-ML-002",
            name="Priya Sharma",
            resume_text=(
                "Priya Sharma — ML Engineer, 4 years experience.\n"
                "Skills: Python, PyTorch, Scikit-learn, model training, hyperparameter tuning, Hugging Face Transformers, MLflow, Git.\n"
                "Education: M.Tech AI, IISc Bangalore.\n"
                "Experience: NLP models at Amazon (2yr), recommendation systems at Swiggy (2yr)."
            ),
            match_score=0.88,
            skills="Python,PyTorch,Scikit-learn,Hugging Face,MLflow,Git",
            missing_skills="AWS SageMaker,vector databases",
            recommendation="shortlist",
            summary="Excellent ML/NLP background with strong tooling alignment. Minor gap in cloud-based training platforms.",
            created_at=datetime.utcnow() - timedelta(days=14),
        ),
    ]
    for c in candidates:
        existing = session.get(Candidate, c.candidate_id)
        if not existing:
            session.add(c)
    session.commit()
    print(f"   ✅ Inserted {len(candidates)} candidate records.")


def seed_it(session: Session):
    print("\n⚙️  Seeding IT Agent data (historical incidents & RCA reports)...")

    incidents = [
        Incident(
            incident_id="INC-HIST-001",
            affected_service="auth-service",
            severity="HIGH",
            status="resolved",
            description="Users unable to log in. Connection timeouts observed from auth-service to PostgreSQL. Database latency spiking above 500ms.",
            created_at=datetime.utcnow() - timedelta(days=60),
        ),
        Incident(
            incident_id="INC-HIST-002",
            affected_service="checkout-service",
            severity="CRITICAL",
            status="resolved",
            description="Payment processing down. checkout-service returning 503. Root cause traced to OOM on payment pod.",
            created_at=datetime.utcnow() - timedelta(days=45),
        ),
        Incident(
            incident_id="INC-HIST-003",
            affected_service="notification-service",
            severity="MEDIUM",
            status="resolved",
            description="Email notifications delayed by 30+ minutes. RabbitMQ queue backlog growing due to consumer lag.",
            created_at=datetime.utcnow() - timedelta(days=20),
        ),
        Incident(
            incident_id="INC-HIST-004",
            affected_service="data-pipeline",
            severity="HIGH",
            status="resolved",
            description="ETL pipeline failing at transformation step. NullPointerException in sales aggregation job. Data freshness now 6 hours behind SLA.",
            created_at=datetime.utcnow() - timedelta(days=10),
        ),
    ]
    for inc in incidents:
        existing = session.get(Incident, inc.incident_id)
        if not existing:
            session.add(inc)
    session.commit()

    rca_reports = [
        RCAReport(
            report_id="RCA-HIST-001",
            incident_id="INC-HIST-001",
            root_cause="Missing composite index on user_sessions table (user_id, created_at). Full table scan under high concurrency caused latency spike.",
            matched_known_issue="KI-0092: DB latency spike — missing index pattern",
            auto_remediated=False,
            business_impact_summary="Auth latency degrading login success rate; estimated ~$4,200/min revenue at risk during peak traffic.",
            recommended_fix="Run: ALTER TABLE user_sessions ADD INDEX idx_session_lookup (user_id, created_at); Monitor query plan with EXPLAIN ANALYZE.",
            generated_at=datetime.utcnow() - timedelta(days=59),
        ),
        RCAReport(
            report_id="RCA-HIST-002",
            incident_id="INC-HIST-002",
            root_cause="checkout-service pod ran out of memory (OOMKilled) due to memory leak in payment-gateway SDK v2.3.1. No memory limits set on the container.",
            matched_known_issue="KI-0047: OOMKilled pod — missing resource limits",
            auto_remediated=False,
            business_impact_summary="Checkout downtime causing direct revenue blockage; estimated ~$15,000/hr loss.",
            recommended_fix="Set memory limits in k8s manifest: resources.limits.memory=512Mi. Upgrade payment-gateway SDK to v2.4.0 which patches the leak.",
            generated_at=datetime.utcnow() - timedelta(days=44),
        ),
        RCAReport(
            report_id="RCA-HIST-003",
            incident_id="INC-HIST-003",
            root_cause="notification-service consumer scaled down to 1 replica during low-traffic window and was never scaled back up. Queue depth exceeded 10,000 messages.",
            matched_known_issue="KI-0031: RabbitMQ consumer lag — missing autoscaler",
            auto_remediated=True,
            business_impact_summary="Delayed notifications causing customer support ticket spike (low direct financial risk).",
            recommended_fix="Deploy KEDA autoscaler based on queue depth metric. Set minReplicas=2 for notification-service to prevent cold-start lag.",
            generated_at=datetime.utcnow() - timedelta(days=19),
        ),
        RCAReport(
            report_id="RCA-HIST-004",
            incident_id="INC-HIST-004",
            root_cause="Null values introduced by upstream schema change in leads table (industry field made nullable). ETL job failed on non-null assertion in aggregation step.",
            matched_known_issue=None,
            auto_remediated=False,
            business_impact_summary="Stale business analytics reporting. No direct traffic impact.",
            recommended_fix="Add COALESCE(industry, 'Unknown') in ETL transformation. Add schema validation step at pipeline entry to catch upstream changes early.",
            generated_at=datetime.utcnow() - timedelta(days=9),
        ),
    ]
    for r in rca_reports:
        existing = session.get(RCAReport, r.report_id)
        if not existing:
            session.add(r)
    session.commit()
    print(f"   ✅ Inserted {len(incidents)} incidents and {len(rca_reports)} RCA reports.")


def seed_sales(session: Session):
    print("\n💼 Seeding Sales Agent data (leads, insights, proposals)...")

    leads = [
        Lead(
            lead_id="LEAD-001",
            customer_name="NovaTech Solutions",
            industry="FinTech",
            pain_points="High server latency affecting user experience,Outdated security protocols causing compliance risk",
            budget_range="$200,000 - $350,000",
            previous_interactions="Initial discovery call conducted on July 5th, client expressed interest in scalable cloud infra.",
            company_offering="Managed AWS/OCI migration services with AI-driven monitoring.",
            created_at=datetime.utcnow() - timedelta(days=30),
        ),
        Lead(
            lead_id="LEAD-002",
            customer_name="FinCore Analytics",
            industry="Finance",
            pain_points="Current batch ETL causing 4-hour data latency,Outdated batch processes",
            budget_range="$80,000 - $120,000",
            previous_interactions="Follow-up call on July 8th: discussed real-time Kafka streaming architectures.",
            company_offering="Apache Kafka streaming pipeline integration with GDPR audit logging.",
            created_at=datetime.utcnow() - timedelta(days=20),
        ),
        Lead(
            lead_id="LEAD-003",
            customer_name="RetailMax India",
            industry="Retail / E-Commerce",
            pain_points="Manual inventory tracking,Overstock levels exceeding 30%",
            budget_range="$50,000 - $75,000",
            previous_interactions="Email exchange on July 9th regarding SAP ERP integration capability.",
            company_offering="AI-powered inventory forecasting system.",
            created_at=datetime.utcnow() - timedelta(days=10),
        ),
    ]
    for l in leads:
        existing = session.get(Lead, l.lead_id)
        if not existing:
            session.add(l)
    session.commit()

    insights = [
        Insight(
            insight_id="INS-001",
            lead_id="LEAD-001",
            sentiment="Positive",
            key_needs="- Reduce server latency\n- Modernize security compliance\n- Scalable cloud infrastructure for growth\n- Managed migration support",
            generated_at=datetime.utcnow() - timedelta(days=28),
        ),
        Insight(
            insight_id="INS-002",
            lead_id="LEAD-002",
            sentiment="Neutral",
            key_needs="- Real-time streaming pipeline\n- EU data residency (GDPR compliance)\n- Low-latency financial reporting\n- Existing Kafka infrastructure reuse",
            generated_at=datetime.utcnow() - timedelta(days=18),
        ),
    ]
    for i in insights:
        existing = session.get(Insight, i.insight_id)
        if not existing:
            session.add(i)
    session.commit()

    proposals = [
        Proposal(
            proposal_id="PROP-001",
            lead_id="LEAD-001",
            pricing_tier="Enterprise",
            estimated_value=280000.0,
            key_points="Managed AWS/OCI migration,AI-driven infrastructure monitoring,Security compliance audit & hardening,24/7 SRE support (12 months),Phased migration plan",
            generated_at=datetime.utcnow() - timedelta(days=25),
        ),
        Proposal(
            proposal_id="PROP-002",
            lead_id="LEAD-002",
            pricing_tier="Standard",
            estimated_value=95000.0,
            key_points="Apache Kafka streaming pipeline setup,EU-region data residency compliance,Real-time financial dashboard,GDPR data audit tooling,3-month implementation timeline",
            generated_at=datetime.utcnow() - timedelta(days=15),
        ),
    ]
    for p in proposals:
        existing = session.get(Proposal, p.proposal_id)
        if not existing:
            session.add(p)
    session.commit()
    print(f"   ✅ Inserted {len(leads)} leads, {len(insights)} insights, {len(proposals)} proposals.")


def seed_executive(session: Session):
    print("\n📊 Seeding Executive Agent KPI Snapshots...")

    today = datetime.utcnow().date().isoformat()  # e.g. "2026-07-10"
    snapshots = [
        # HR KPIs
        KPISnapshot(snapshot_id=f"kpi_{uuid.uuid4().hex[:8]}", source_agent="hr", metric_name="open_jobs", metric_value=3.0, snapshot_date=today),
        KPISnapshot(snapshot_id=f"kpi_{uuid.uuid4().hex[:8]}", source_agent="hr", metric_name="total_candidates", metric_value=3.0, snapshot_date=today),
        KPISnapshot(snapshot_id=f"kpi_{uuid.uuid4().hex[:8]}", source_agent="hr", metric_name="shortlist_size", metric_value=2.0, snapshot_date=today),
        KPISnapshot(snapshot_id=f"kpi_{uuid.uuid4().hex[:8]}", source_agent="hr", metric_name="avg_match_score", metric_value=0.75, snapshot_date=today),
        KPISnapshot(snapshot_id=f"kpi_{uuid.uuid4().hex[:8]}", source_agent="hr", metric_name="recruitment_velocity_days", metric_value=21.0, snapshot_date=today),

        # IT KPIs
        KPISnapshot(snapshot_id=f"kpi_{uuid.uuid4().hex[:8]}", source_agent="it", metric_name="total_incidents", metric_value=4.0, snapshot_date=today),
        KPISnapshot(snapshot_id=f"kpi_{uuid.uuid4().hex[:8]}", source_agent="it", metric_name="resolved_incidents", metric_value=4.0, snapshot_date=today),
        KPISnapshot(snapshot_id=f"kpi_{uuid.uuid4().hex[:8]}", source_agent="it", metric_name="open_incidents", metric_value=0.0, snapshot_date=today),
        KPISnapshot(snapshot_id=f"kpi_{uuid.uuid4().hex[:8]}", source_agent="it", metric_name="auto_remediation_rate", metric_value=0.25, snapshot_date=today),
        KPISnapshot(snapshot_id=f"kpi_{uuid.uuid4().hex[:8]}", source_agent="it", metric_name="mttr_minutes", metric_value=47.0, snapshot_date=today),

        # Sales KPIs
        KPISnapshot(snapshot_id=f"kpi_{uuid.uuid4().hex[:8]}", source_agent="sales", metric_name="total_leads", metric_value=3.0, snapshot_date=today),
        KPISnapshot(snapshot_id=f"kpi_{uuid.uuid4().hex[:8]}", source_agent="sales", metric_name="proposals_generated", metric_value=2.0, snapshot_date=today),
        KPISnapshot(snapshot_id=f"kpi_{uuid.uuid4().hex[:8]}", source_agent="sales", metric_name="pipeline_value_usd", metric_value=375000.0, snapshot_date=today),
        KPISnapshot(snapshot_id=f"kpi_{uuid.uuid4().hex[:8]}", source_agent="sales", metric_name="avg_deal_value_usd", metric_value=187500.0, snapshot_date=today),
        KPISnapshot(snapshot_id=f"kpi_{uuid.uuid4().hex[:8]}", source_agent="sales", metric_name="win_rate", metric_value=0.31, snapshot_date=today),
    ]
    for s in snapshots:
        session.add(s)
    session.commit()
    print(f"   ✅ Inserted {len(snapshots)} KPI snapshot records.")


if __name__ == "__main__":
    print(">> Enterprise Multi-Agent System -- Database Seeder")
    print("=" * 55)
    print("Initializing database schema...")
    init_db()

    with Session(engine) as session:
        seed_hr(session)
        seed_it(session)
        seed_sales(session)
        seed_executive(session)

    print("\n" + "=" * 55)
    print("[DONE] Database seeding complete!")
    print("\nYou can now open enterprise_agents.db with SQLite Viewer")
    print("to inspect all seeded data before running conversations.")
