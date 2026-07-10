# Enterprise Multi-Agent System (Prototype)

A modular, multi-agent platform where specialized AI agents automate core business functions — Human Resources, IT Operations, Sales, and Executive Reporting — and feed their outputs into a shared data layer that powers cross-functional insights.

> **Prototype scope:** The current phase focuses on building a working chatbot prototype run locally. The API Gateway is intentionally omitted at this stage — agents are reached directly. **Groq API** powers all LLM calls.

---

## 1. Project Overview

| Agent | Core Responsibilities | Primary Consumers |
|---|---|---|
| **HR Agent** | Recruitment, Resume Screening | Hiring Managers, Executive Agent |
| **IT Agent** | Incident Resolution, Root Cause Analysis | IT Ops Team, Executive Agent |
| **Sales Agent** | Proposal Generation, Customer Insights | Sales Reps, Executive Agent |
| **Executive Agent** | KPI Dashboard, Decision Support | Leadership |

Each domain agent is autonomous — it owns its data pipeline and its own database tables. The **Executive Agent** does not own primary data; it reads the outputs (snapshots) of the other three agents and performs **synthesis, prioritization, and strategic advising** rather than tactical work.

> **No API Gateway in prototype:** Agents are called directly from the orchestrator without an intermediate gateway layer. Auth, rate-limiting, and routing will be added in a later production phase.

---

## 2. Architecture Diagram

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        UI[Next.js Chatbot UI<br/>run locally]
    end

    subgraph Agents["Agent Layer (called directly — no gateway)"]
        HR[HR Agent<br/>Recruitment & Resume Screening<br/>Retrieval-Augmented]
        IT[IT Agent<br/>Incident Resolution & RCA<br/>Dual-audience output]
        SALES[Sales Agent<br/>Proposals & Customer Insights]
        EXEC[Executive Agent<br/>KPI Dashboard & Decision Support<br/>Synthesis / Prioritization / Advising]
    end

    subgraph Orch["Orchestration"]
        ORCH[Agent Orchestrator]
        GROQ[Groq API<br/>llama-3.3-70b-versatile / mixtral-8x7b]
    end

    subgraph Data["Data Layer"]
        HRDB[(HR DB<br/>Jobs · Candidates)]
        ITDB[(IT DB<br/>Tickets · RCA Reports)]
        SALESDB[(Sales DB<br/>Leads · Proposals · Insights)]
        ANALYTICS[(Analytics / KPI Warehouse<br/>KPI_SNAPSHOTS)]
        VSTORE[(Vector Store<br/>JDs · Resumes · Tickets · CRM Transcripts)]
    end

    UI --> HR & IT & SALES & EXEC
    HR --> ORCH
    IT --> ORCH
    SALES --> ORCH
    EXEC --> ORCH
    ORCH --> GROQ

    HR --> HRDB
    HR --> VSTORE

    IT --> ITDB
    IT --> VSTORE

    SALES --> SALESDB
    SALES --> VSTORE

    HRDB --> ANALYTICS
    ITDB --> ANALYTICS
    SALESDB --> ANALYTICS
    EXEC --> ANALYTICS
```

> **Future (Production) Architecture:** An API Gateway layer (auth · routing · rate limiting) will be introduced between the Client and Agent layers once the prototype is validated.

**Key design principles**
- **Loose coupling:** Each agent is independently deployable with its own database schema.
- **Shared orchestration:** All agents route LLM calls through a common orchestrator so prompts, model versions, and tool-use policies stay consistent.
- **Groq as the brain:** The orchestrator uses the Groq API for fast, low-latency inference powering all agent reasoning.
- **Single source of truth for KPIs:** The Executive Agent never writes to another agent's database — it only reads aggregated/derived data (snapshots) from the Analytics Warehouse.
- **Vector store reuse:** Job descriptions, resumes, ticket logs, and CRM transcripts are embedded once and reused for both retrieval and semantic analysis.

---

## 3. How Requests Move Through The System

### 3.1 General request lifecycle — Prototype (direct routing)

```mermaid
sequenceDiagram
    participant U as User (Chatbot UI)
    participant AG as Domain Agent (HR/IT/Sales/Exec)
    participant OR as Orchestrator
    participant GQ as Groq API
    participant DB as Domain Database

    U->>AG: Send request (direct call, no gateway)
    AG->>DB: Fetch context (JD, tickets, CRM records, snapshots)
    AG->>OR: Build prompt + attach retrieved context
    OR->>GQ: Send completion / tool-use request
    GQ-->>OR: Structured response (JSON)
    OR-->>AG: Parsed result
    AG->>DB: Persist result
    AG-->>U: Response payload
```

> **Note:** In the production version, an API Gateway will sit between the User and the Agent layer, handling authentication, payload validation, and routing.

### 3.2 HR Agent — Retrieval-Augmented Resume Screening

The HR Agent evolves from a passive processor into a **Retrieval-Augmented Agent**. Rather than scoring a resume in isolation, it performs a **dual-lookup**: fetching the full Job Description (JD) from the database and comparing it directly against the candidate's resume text.

```mermaid
flowchart LR
    A[Candidate Resume Submitted] --> B[Fetch Full JD by job_id]
    B --> C[Retrieve Resume Text]
    C --> D[Dual-Lookup Comparison<br/>JD vs Resume]
    D --> E[Skill/Experience/Soft-Skill Match Scoring]
    E --> F{Score >= Threshold?}
    F -->|Yes| G[Add to Shortlist]
    F -->|No| H[Archive as Not Fit]
    G --> I[Notify Hiring Manager]
```

### 3.3 IT Agent — Incident → Root Cause Analysis (Dual-Audience Output)

The IT Agent ingests raw monitoring "signal" (logs, system context, historical incident data) and must produce output that serves **two audiences at once**: a technical diagnostic for the Ops team and an impact metric for Executives.

```mermaid
flowchart LR
    A[Incoming Incident:<br/>raw_logs + system_context] --> B[Correlate Against historical_data_context]
    B --> C[Root Cause Identification]
    C --> D{Auto-remediable?}
    D -->|Yes| E[Suggest Fix/Command<br/>e.g. ALTER TABLE...]
    D -->|No| F[Escalate to Engineer]
    E --> G[Structured Report:<br/>Incident Details + Root Cause + Auto-Remediation]
    F --> G
    G --> H[Store in Incident Knowledge Base]
```

### 3.4 Sales Agent — Proposal Generation & Customer Insights

```mermaid
flowchart LR
    A[Client Profile:<br/>pain_points, budget, past interactions] --> B[Customer Insight Analysis<br/>sentiment / needs / urgency]
    B --> C[Match company_offering to pain_points]
    C --> D[Draft Personalized Proposal]
    D --> E[Pricing/Scope Recommendation]
    E --> F[Deliver to Sales Rep]
```

### 3.5 Executive Agent — Synthesis, Prioritization & Strategic Advising

Unlike the domain agents, the Executive Agent does not do tactical work — it **synthesizes** snapshots from HR, IT, and Sales, **prioritizes** what's urgent, and **advises** leadership on strategic questions.

```mermaid
flowchart LR
    A[hr_snapshot:<br/>Recruitment Velocity, Shortlist size] --> D[Synthesis Engine]
    B[it_snapshot:<br/>MTTR, Active Incidents, System Health] --> D
    C[sales_snapshot:<br/>Pipeline Value, Conversion Probability] --> D
    E[leadership_query] --> D
    D --> F[KPI Dashboard]
    D --> G[Executive Summary]
    D --> H[Decision Support / What-If Scenarios]
    D --> I[Risk Flags]
```

---

## 4. Agent Input / Output Contracts

This section defines the exact shape of data flowing into and out of each agent — the contract the orchestrator and downstream consumers rely on.

### 4.1 HR Agent

**Input structure** — the dictionary passed into the HR node performs a dual-lookup: the full JD text and the full resume text are both supplied so the agent compares them directly rather than scoring the resume in isolation.

```python
# The input dictionary passed into the hr_node
input_package = {
    "job_id": "DE-2026-001",
    "full_jd_text": """[...The entire 2-page document containing roles, responsibilities,
    required tech stack, experience, and soft skills...]""",
    "resume_text": "[...The full text of the applicant's resume...]"
}
```

**Output structure**

| Field | Description |
|---|---|
| `candidate_id` | Unique identifier for the candidate |
| `job_id` | The JD this candidate was scored against |
| `match_score` | Overall fit score (0–100) derived from JD vs. resume comparison |
| `skill_matches` | Skills present in both JD and resume |
| `missing_skills` | Skills required by the JD but absent from the resume |
| `recommendation` | `shortlist` / `hold` / `reject` |
| `summary` | Natural-language rationale grounded in the JD comparison |

### 4.2 IT Agent

**Input structure** — the IT Agent needs to see the "signal" from monitoring systems, plus historical context so it can correlate incidents against past resolutions.

```json
{
  "incident_id": "INC-2026-07-10-098",
  "raw_logs": "ERROR: [auth-svc] connection timeout at 08:00:15... [Database] latency spikes > 500ms detected.",
  "system_context": "Production environment, High Traffic period.",
  "historical_data_context": "Similar incident occurred on May 12th; solved by database index optimization."
}
```

**Output structure — dual-audience report.** To serve two masters, the output is structured to provide a **Technical Diagnostic** (for Ops) and an **Impact Metric** (for Executives).

| Section | Target Audience | Content |
|---|---|---|
| **Incident Details** | Ops Team | Severity, timestamp, affected services |
| **Root Cause** | Ops Team | The specific technical trigger (e.g., "Missing index on `user_sessions` table") |
| **Auto-Remediation** | Ops Team | Suggested command/script to fix (e.g., `ALTER TABLE...`) |
| **Impact Metric** | Executives | Business-facing severity/impact summary (e.g., "Checkout downtime, ~$4,200/min revenue at risk") feeding the `it_snapshot` consumed by the Executive Agent |

### 4.3 Sales Agent

**Input structure**

```json
{
  "client_name": "NovaTech Solutions",
  "industry": "FinTech",
  "pain_points": ["High server latency", "Outdated security protocols"],
  "budget": "INR 15,00,000",
  "previous_interactions": "Initial discovery call conducted on July 5th, client expressed interest in scalable cloud infra.",
  "company_offering": "Managed AWS/OCI migration services with AI-driven monitoring."
}
```

**Output structure**

| Field | Description |
|---|---|
| `proposal_id` | Unique identifier for the generated proposal |
| `customer_insight` | Sentiment/needs analysis derived from `pain_points` and `previous_interactions` |
| `pricing_tier` / `estimated_value` | Recommended pricing aligned to `budget` |
| `key_points` | How `company_offering` addresses each pain point |
| `proposal_document_url` | Link to the generated proposal document |
| Primary consumers | Sales Reps (for outreach), Executive Agent (for `sales_snapshot`: pipeline value, conversion probability) |

### 4.4 Executive Agent

**Input structure** — the Executive Agent consumes structured snapshots from the three domain agents alongside a natural-language leadership question, rather than raw operational data.

```json
{
  "system_context": {
    "timestamp": "2026-07-10T11:20:15Z",
    "hr_snapshot": { "_comment": "Output from HR Agent: Recruitment Velocity, Shortlist size" },
    "it_snapshot": { "_comment": "Output from IT Agent: MTTR, Active Incidents, System Health" },
    "sales_snapshot": { "_comment": "Output from Sales Agent: Pipeline Value, Conversion Probability" }
  },
  "leadership_query": "What is the primary risk to our quarterly revenue goal based on current operations?"
}
```

**Output structure**

| Output Component | Format | Description |
|---|---|---|
| **KPI Dashboard** | JSON / UI-ready | A collection of 3–5 "North Star" metrics (e.g., Overall Health Score, Revenue at Risk, Resource Utilization %) |
| **Executive Summary** | Markdown text | A 3-sentence summary of the company's current status |
| **Decision Support** | Bullet points | A list of "what if" scenarios or recommended actions (e.g., "If we delay recruitment, we risk a 15% drop in project delivery") |
| **Risk Flags** | JSON array | Urgent items requiring immediate attention (e.g., IT outages or deal stalls) |

---

## 5. Project Structure

```
enterprise-agent-system/
├── README.md
├── .env.example
│
├── agents/
│   ├── hr_agent/
│   │   ├── __init__.py
│   │   ├── service.py            # Retrieval-augmented Recruitment + Resume Screening
│   │   ├── prompts/
│   │   │   ├── resume_screening.md
│   │   │   └── job_matching.md
│   │   ├── models.py              # Pydantic/ORM schemas
│   │   └── db.py
│   │
│   ├── it_agent/
│   │   ├── __init__.py
│   │   ├── service.py            # Incident Resolution + RCA logic (dual-audience output)
│   │   ├── prompts/
│   │   │   ├── triage.md
│   │   │   └── root_cause_analysis.md
│   │   ├── models.py
│   │   └── db.py
│   │
│   ├── sales_agent/
│   │   ├── __init__.py
│   │   ├── service.py            # Proposal Generation + Customer Insights
│   │   ├── prompts/
│   │   │   ├── proposal_draft.md
│   │   │   └── sentiment_needs_analysis.md
│   │   ├── models.py
│   │   └── db.py
│   │
│   └── executive_agent/
│       ├── __init__.py
│       ├── service.py            # Synthesis, prioritization, strategic advising
│       ├── prompts/
│       │   └── strategic_summary.md
│       ├── models.py
│       └── db.py
│
├── orchestrator/
│   ├── orchestrator.py           # Shared LLM call handler, tool registry
│   ├── tools/
│   │   ├── embedding_tool.py
│   │   └── scoring_tool.py
│   └── groq_client.py            # Groq API client (brain model calls)
│
├── shared/
│   ├── vector_store/
│   │   └── client.py             # Wraps vector DB (e.g., pgvector/Pinecone)
│   ├── analytics/
│   │   └── warehouse.py          # ETL into KPI warehouse
│   └── utils/
│       ├── parsing.py            # JD/resume/log/document parsing helpers
│       └── logging.py
│
├── db/
│   ├── migrations/
│   └── schema.sql                # Full DB schema (see Section 8)
│
├── chatbot_ui/                   # Vercel-hosted Next.js chatbot frontend
│   ├── pages/
│   ├── components/
│   └── vercel.json
│
└── tests/
    ├── hr_agent/
    ├── it_agent/
    ├── sales_agent/
    └── executive_agent/
```

> **Removed from prototype:** `gateway/` directory (auth middleware, rate limiting, gateway routes) — to be added in the production phase.

---

## 6. API Endpoints

All endpoints are called directly from the chatbot UI or orchestrator (no gateway in prototype). Versioning is maintained for forward compatibility.

### 6.1 HR Agent

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/hr/jobs` | Create a new job requisition (stores `full_jd_text`) |
| `POST` | `/api/v1/hr/resumes/upload` | Upload and parse a raw resume |
| `POST` | `/api/v1/hr/resumes/screen` | Dual-lookup screening: fetch JD by `job_id`, compare against `resume_text` |
| `GET` | `/api/v1/hr/candidates/shortlist?job_id=` | Retrieve ranked shortlist for a job |
| `GET` | `/api/v1/hr/candidates/{candidate_id}` | Get candidate detail + score breakdown |

### 6.2 IT Agent

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/it/incidents` | Submit a new incident (`raw_logs`, `system_context`) |
| `POST` | `/api/v1/it/incidents/{incident_id}/triage` | Run triage/classification |
| `POST` | `/api/v1/it/incidents/{incident_id}/rca` | Generate dual-audience RCA report (Incident Details / Root Cause / Auto-Remediation) |
| `GET` | `/api/v1/it/incidents/{incident_id}` | Get incident status and resolution history |
| `GET` | `/api/v1/it/incidents/known-issues` | List matched known-issue patterns from `historical_data_context` |

### 6.3 Sales Agent

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/sales/leads` | Ingest a new lead/client profile |
| `POST` | `/api/v1/sales/insights` | Generate customer insight (sentiment/needs) from client profile |
| `POST` | `/api/v1/sales/proposals/generate` | Generate a personalized proposal from `company_offering` + `pain_points` |
| `GET` | `/api/v1/sales/proposals/{proposal_id}` | Retrieve a generated proposal |

### 6.4 Executive Agent

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/executive/kpis?range=` | Retrieve the KPI Dashboard (North Star metrics) |
| `GET` | `/api/v1/executive/trends?metric=` | Get trend/time-series data for a metric |
| `POST` | `/api/v1/executive/decision-support` | Submit `system_context` + `leadership_query`, receive Executive Summary, Decision Support, and Risk Flags |

---

## 7. Examples

### 7.1 HR Agent — Retrieval-Augmented Resume Screening

**Request**
```http
POST /api/v1/hr/resumes/screen
Content-Type: application/json
```
```json
{
  "job_id": "DE-2026-001",
  "full_jd_text": "[...The entire 2-page document containing roles, responsibilities, required tech stack, experience, and soft skills...]",
  "resume_text": "[...The full text of the applicant's resume...]"
}
```

**Response**
```json
{
  "candidate_id": "cand_8841",
  "job_id": "DE-2026-001",
  "match_score": 87.5,
  "skill_matches": ["Python", "Airflow", "PostgreSQL", "AWS Glue"],
  "missing_skills": ["Kubernetes"],
  "recommendation": "shortlist",
  "summary": "Strong data engineering background matching most of the JD's required tech stack; minor gap in container orchestration skills.",
  "created_at": "2026-07-10T09:12:00Z"
}
```

### 7.2 IT Agent — Root Cause Analysis (Dual-Audience)

**Request**
```http
POST /api/v1/it/incidents/INC-2026-07-10-098/rca
Content-Type: application/json
```
```json
{
  "incident_id": "INC-2026-07-10-098",
  "raw_logs": "ERROR: [auth-svc] connection timeout at 08:00:15... [Database] latency spikes > 500ms detected.",
  "system_context": "Production environment, High Traffic period.",
  "historical_data_context": "Similar incident occurred on May 12th; solved by database index optimization."
}
```

**Response**
```json
{
  "incident_id": "INC-2026-07-10-098",
  "incident_details": {
    "severity": "high",
    "timestamp": "2026-07-10T08:00:15Z",
    "affected_services": ["auth-svc", "database"]
  },
  "root_cause": "Missing index on user_sessions table causing latency spikes under high traffic, mirroring the May 12th incident.",
  "auto_remediation": {
    "suggested_command": "ALTER TABLE user_sessions ADD INDEX idx_session_lookup (user_id, created_at);",
    "auto_remediated": false,
    "escalated_to": "backend-oncall"
  },
  "impact_metric": {
    "business_summary": "Auth latency degrading login success rate; estimated ~$4,200/min revenue at risk during peak traffic.",
    "matched_known_issue": "May 12th index optimization incident"
  },
  "generated_at": "2026-07-10T08:05:00Z"
}
```

### 7.3 Sales Agent — Proposal Generation & Customer Insight

**Request**
```http
POST /api/v1/sales/proposals/generate
Content-Type: application/json
```
```json
{
  "client_name": "NovaTech Solutions",
  "industry": "FinTech",
  "pain_points": ["High server latency", "Outdated security protocols"],
  "budget": "INR 15,00,000",
  "previous_interactions": "Initial discovery call conducted on July 5th, client expressed interest in scalable cloud infra.",
  "company_offering": "Managed AWS/OCI migration services with AI-driven monitoring."
}
```

**Response**
```json
{
  "proposal_id": "prop_1187",
  "client_name": "NovaTech Solutions",
  "customer_insight": {
    "sentiment": "interested, cost-conscious",
    "key_needs": ["Reduce server latency", "Modernize security compliance", "Scalable cloud infrastructure"],
    "urgency": "medium"
  },
  "pricing_tier": "Growth",
  "estimated_value": 1450000,
  "key_points": [
    "Managed AWS/OCI migration addressing current latency bottlenecks",
    "AI-driven monitoring to proactively flag security/performance issues",
    "Phased migration to fit within INR 15,00,000 budget"
  ],
  "proposal_document_url": "s3://proposals/prop_1187.pdf",
  "generated_at": "2026-07-10T10:05:00Z"
}
```

### 7.4 Executive Agent — Synthesis & Decision Support

**Request**
```http
POST /api/v1/executive/decision-support
Content-Type: application/json
```
```json
{
  "system_context": {
    "timestamp": "2026-07-10T11:20:15Z",
    "hr_snapshot": { "recruitment_velocity_days": 21, "shortlist_size": 8 },
    "it_snapshot": { "mttr_minutes": 47, "active_incidents": 3, "system_health_score": 0.82 },
    "sales_snapshot": { "pipeline_value": 12400000, "conversion_probability": 0.31 }
  },
  "leadership_query": "What is the primary risk to our quarterly revenue goal based on current operations?"
}
```

**Response**
```json
{
  "kpi_dashboard": {
    "overall_health_score": 78,
    "revenue_at_risk": 4300000,
    "resource_utilization_pct": 74,
    "recruitment_velocity_days": 21,
    "active_incidents": 3
  },
  "executive_summary": "Operations are broadly healthy, but 3 active IT incidents are elevating churn risk for FinTech accounts. Sales pipeline remains strong at ₹1.24Cr with a 31% conversion rate. Delayed recruitment could constrain delivery capacity next quarter.",
  "decision_support": [
    "If active incidents aren't resolved within 48 hours, expect a 10-12% dip in customer satisfaction scores for affected accounts.",
    "If recruitment for the DE-2026-001 role slips further, project delivery could drop by 15% next quarter.",
    "Reallocating one IT engineer to the checkout-service incident would likely reduce MTTR by ~20 minutes."
  ],
  "risk_flags": [
    { "type": "it_outage", "severity": "high", "description": "3 active incidents in production during high-traffic period" },
    { "type": "deal_stall", "severity": "medium", "description": "NovaTech proposal pending decision past 5 business days" }
  ],
  "generated_at": "2026-07-10T11:21:00Z"
}
```

---

## 8. Database Structure

Each domain agent owns its own schema; the Executive Agent reads from a derived **Analytics Warehouse** rather than the source tables directly.

```mermaid
erDiagram
    JOBS ||--o{ CANDIDATES : "screened for"
    JOBS {
        string job_id PK
        string title
        string department
        text full_jd_text
        timestamp created_at
    }
    CANDIDATES {
        string candidate_id PK
        string job_id FK
        string name
        text resume_text
        float match_score
        json skill_matches
        json missing_skills
        string recommendation
        timestamp created_at
    }

    INCIDENTS ||--o{ RCA_REPORTS : "generates"
    INCIDENTS {
        string incident_id PK
        text raw_logs
        string system_context
        string severity
        string status
        timestamp created_at
    }
    RCA_REPORTS {
        string report_id PK
        string incident_id FK
        text root_cause
        text auto_remediation_command
        boolean auto_remediated
        text business_impact_summary
        string matched_known_issue
        timestamp generated_at
    }

    LEADS ||--o{ PROPOSALS : "generates"
    LEADS ||--o{ INSIGHTS : "generates"
    LEADS {
        string lead_id PK
        string client_name
        string industry
        json pain_points
        string budget
        text previous_interactions
        timestamp created_at
    }
    PROPOSALS {
        string proposal_id PK
        string lead_id FK
        string pricing_tier
        float estimated_value
        json key_points
        string document_url
        timestamp generated_at
    }
    INSIGHTS {
        string insight_id PK
        string lead_id FK
        string sentiment
        json key_needs
        string urgency
        timestamp generated_at
    }

    KPI_SNAPSHOTS {
        string snapshot_id PK
        string source_agent
        string metric_name
        float metric_value
        date snapshot_date
    }

    DECISION_SUPPORT_LOGS {
        string log_id PK
        text leadership_query
        json hr_snapshot
        json it_snapshot
        json sales_snapshot
        text executive_summary
        json decision_support
        json risk_flags
        timestamp generated_at
    }
```

**Notes**
- `KPI_SNAPSHOTS` is populated by a periodic ETL job that reads from `CANDIDATES`, `INCIDENTS`, `RCA_REPORTS`, `LEADS`, and `PROPOSALS`, aggregating them into standard metrics (recruitment velocity, MTTR, win rate, etc.).
- `DECISION_SUPPORT_LOGS` captures every Executive Agent synthesis call — the snapshots it received, the leadership query, and its recommendations — for auditability.
- The Executive Agent's `/kpis` and `/decision-support` endpoints query `KPI_SNAPSHOTS` and the domain agents' snapshot outputs exclusively — it never has write access to other agents' source tables, preserving domain ownership boundaries.
- Vector embeddings (JDs, resumes, incident logs, CRM transcripts) are stored separately in a vector store, keyed by the same IDs (`job_id`/`candidate_id`, `incident_id`, `lead_id`) for cross-referencing.

---

## 9. Tech Stack

### Prototype (Current Phase)

| Layer | Technology |
|---|---|
| Chatbot UI | Next.js — run locally |
| Agent Services | Python (FastAPI) |
| LLM / Brain Model | Groq API (fast inference — e.g. `llama-3.3-70b-versatile` or `mixtral-8x7b`) |
| LLM Orchestration | Custom orchestrator (`groq_client.py`) with tool-use for structured outputs |
| Relational DB | PostgreSQL (one schema per agent) |
| Vector Store | pgvector or a managed vector DB |
| Analytics Warehouse | PostgreSQL materialized views |
| Deployment | Fully local |

### Production (Future Phase)

| Layer | Technology |
|---|---|
| API Gateway | FastAPI / Express.js + JWT auth, rate limiting, routing |
| Messaging (optional) | Kafka / RabbitMQ for async ticket/lead ingestion |
| Deployment | Docker Compose (dev) → Kubernetes (prod) |

---

## 10. Environment Variables

```bash
# Groq API — brain model
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile        # or mixtral-8x7b, gemma2-9b-it, etc.

# Database
DATABASE_URL=postgresql://user:password@host:5432/enterprise_agents

# Vector Store
VECTOR_STORE_URL=...

# (Future) Auth — not needed for prototype
# JWT_SECRET=...
```

---

## 11. Next Steps (Prototype)

1. Set up the Groq API client in `orchestrator/groq_client.py`.
2. Scaffold the four agent services with the folder structure in Section 5.
3. Implement the HR Agent's dual-lookup retrieval (JD fetch + resume comparison).
4. Implement the IT Agent's dual-audience RCA output (technical diagnostic + impact metric).
5. Implement the Sales Agent's customer-insight + proposal-generation pipeline.
6. Implement the Executive Agent's synthesis logic consuming `hr_snapshot`, `it_snapshot`, and `sales_snapshot`.
7. Define Pydantic/ORM models matching the schema in Section 8.
8. Build and run the chatbot UI locally.
9. Wire the ETL job that populates `KPI_SNAPSHOTS` for the Executive Agent.
10. Write integration tests simulating the end-to-end flows in Section 3.

**Production backlog:** Add API Gateway (auth, rate limiting, routing), Docker/Kubernetes deployment, and role-based access control once the prototype is validated.
