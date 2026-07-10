# Enterprise Multi-Agent System (Prototype)

A modular, multi-agent platform where specialized AI agents automate core business functions — Human Resources, IT Operations, Sales, and Executive Reporting — and feed their outputs into a shared data layer that powers cross-functional insights.

> **Prototype scope:** The current phase focuses on building a working chatbot prototype hosted on Vercel. The API Gateway is intentionally omitted at this stage — agents are reached directly. Groq API powers all LLM calls.

---

## 1. Project Overview

| Agent | Core Responsibilities | Primary Consumers |
|---|---|---|
| **HR Agent** | Recruitment, Resume Screening | Hiring Managers, Executive Agent |
| **IT Agent** | Incident Resolution, Root Cause Analysis | IT Ops Team, Executive Agent |
| **Sales Agent** | Proposal Generation, Customer Insights | Sales Reps, Executive Agent |
| **Executive Agent** | KPI Dashboard, Decision Support | Leadership |

Each domain agent is autonomous — it owns its data pipeline and its own database tables. The **Executive Agent** does not own primary data; it aggregates outputs from the other three agents to generate cross-functional KPIs and decision-support recommendations.

> **No API Gateway in prototype:** For the initial prototype, agents are called directly from the orchestrator without an intermediate gateway layer. Auth, rate-limiting, and routing will be added in a later production phase.

---

## 2. Architecture Diagram

### Prototype Architecture

```mermaid
flowchart TB
    subgraph Client["Client Layer (Vercel)"]
        UI[Chatbot Web UI]
    end

    subgraph Agents["Agent Layer"]
        HR[HR Agent<br/>Recruitment & Resume Screening]
        IT[IT Agent<br/>Incident Resolution & RCA]
        SALES[Sales Agent<br/>Proposals & Customer Insights]
        EXEC[Executive Agent<br/>KPI Dashboard & Decision Support]
    end

    subgraph LLM["LLM / Orchestration"]
        ORCH[Agent Orchestrator]
        MODEL[Groq API<br/>Brain Model]
    end

    subgraph Data["Data Layer"]
        HRDB[(HR DB)]
        ITDB[(IT DB)]
        SALESDB[(Sales DB)]
        ANALYTICS[(Analytics / KPI Warehouse)]
        VSTORE[(Vector Store<br/>Resumes · Tickets · Transcripts)]
    end

    subgraph Ext["External Integrations"]
        ATS[ATS / Job Boards]
        ITSM[ITSM / Monitoring Tools]
        CRM[CRM System]
    end

    UI --> HR & IT & SALES & EXEC
    HR --> ORCH
    IT --> ORCH
    SALES --> ORCH
    EXEC --> ORCH
    ORCH --> MODEL

    HR --> HRDB
    HR --> VSTORE
    HR -.pull.-> ATS

    IT --> ITDB
    IT --> VSTORE
    IT -.pull.-> ITSM

    SALES --> SALESDB
    SALES --> VSTORE
    SALES -.pull.-> CRM

    HRDB --> ANALYTICS
    ITDB --> ANALYTICS
    SALESDB --> ANALYTICS
    EXEC --> ANALYTICS
```

> **Future (Production) Architecture:** An API Gateway layer (auth · routing · rate limiting) will be introduced between the Client and Agent layers once the prototype is validated.

**Key design principles**
- **Loose coupling:** Each agent is independently deployable with its own database schema and API surface.
- **Shared orchestration:** All agents route LLM calls through a common orchestrator so prompts, model versions, and tool-use policies stay consistent.
- **Groq as the brain:** The orchestrator uses Groq API for fast, low-latency LLM inference powering all agent reasoning.
- **Single source of truth for KPIs:** The Executive Agent never writes to another agent's database — it only reads aggregated/derived data from the Analytics Warehouse.
- **Vector store reuse:** Resumes, ticket logs, and CRM transcripts are embedded once and reused for both search and semantic analysis.

---

## 3. How Requests Move Through The System

### 3.1 General request lifecycle — Prototype (direct routing)

```mermaid
sequenceDiagram
    participant U as User (Chatbot UI)
    participant AG as Domain Agent (HR/IT/Sales/Exec)
    participant OR as Orchestrator
    participant GROQ as Groq API (Brain Model)
    participant DB as Domain Database

    U->>AG: Direct POST /agent/{action}
    AG->>DB: Fetch context (existing records)
    AG->>OR: Build prompt + attach context/tools
    OR->>GROQ: Send completion/tool-use request
    GROQ-->>OR: Structured response (JSON)
    OR-->>AG: Parsed result
    AG->>DB: Persist result (scores, report, proposal, etc.)
    AG-->>U: Response payload
```

> **Note:** In the production version, an API Gateway will sit between the User and the Agent layer, handling authentication, payload validation, and routing.

### 3.2 Example: Resume Screening flow (HR Agent)

```mermaid
flowchart LR
    A[Raw Resume Upload] --> B[Text/PDF Parsing]
    B --> C[Skill & Experience Extraction]
    C --> D[Embedding Generation]
    D --> E[Score Against Job Requirements]
    E --> F{Score >= Threshold?}
    F -->|Yes| G[Add to Shortlist]
    F -->|No| H[Archive as Not Fit]
    G --> I[Notify Hiring Manager]
```

### 3.3 Example: Incident → RCA flow (IT Agent)

```mermaid
flowchart LR
    A[Incoming Ticket / Log Alert] --> B[Triage & Severity Classification]
    B --> C[Pattern Match Against Known Issues]
    C --> D{Auto-remediable?}
    D -->|Yes| E[Execute Runbook / Auto-fix]
    D -->|No| F[Escalate to Engineer]
    E --> G[Root Cause Report]
    F --> G
    G --> H[Store in Incident Knowledge Base]
```

### 3.4 Example: Executive aggregation flow

```mermaid
flowchart LR
    A[HR Metrics: Time-to-Hire, Pipeline] --> D[KPI Synthesis Engine]
    B[IT Metrics: MTTR, Ticket Volume] --> D
    C[Sales Metrics: Pipeline Value, Win Rate] --> D
    D --> E[Trend & Anomaly Detection]
    E --> F[Dashboard Widgets]
    E --> G[Decision-Support Recommendations]
```

---

## 4. Project Structure

```
enterprise-agent-system/
├── README.md
├── .env.example
│
├── agents/
│   ├── hr_agent/
│   │   ├── __init__.py
│   │   ├── service.py            # Recruitment + Resume Screening logic
│   │   ├── prompts/
│   │   │   ├── resume_screening.md
│   │   │   └── job_matching.md
│   │   ├── models.py              # Pydantic/ORM schemas
│   │   └── db.py
│   │
│   ├── it_agent/
│   │   ├── __init__.py
│   │   ├── service.py            # Incident Resolution + RCA logic
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
│       ├── service.py            # KPI aggregation + Decision Support
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
│       ├── parsing.py            # Resume/log/document parsing helpers
│       └── logging.py
│
├── db/
│   ├── migrations/
│   └── schema.sql                # Full DB schema (see Section 7)
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

## 5. API Endpoints

All endpoints are called **directly** from the chatbot UI or orchestrator (no gateway in prototype). Versioning is maintained for forward compatibility.

### 5.1 HR Agent

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/hr/jobs` | Create a new job requisition |
| `POST` | `/api/v1/hr/resumes/upload` | Upload and parse a raw resume |
| `POST` | `/api/v1/hr/resumes/screen` | Screen a resume against a job's requirements |
| `GET` | `/api/v1/hr/candidates/shortlist?job_id=` | Retrieve ranked shortlist for a job |
| `GET` | `/api/v1/hr/candidates/{candidate_id}` | Get candidate detail + score breakdown |

### 5.2 IT Agent

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/it/tickets` | Submit a new incident/ticket |
| `POST` | `/api/v1/it/tickets/{ticket_id}/triage` | Run triage/classification on a ticket |
| `POST` | `/api/v1/it/tickets/{ticket_id}/rca` | Generate root cause analysis report |
| `GET` | `/api/v1/it/tickets/{ticket_id}` | Get ticket status and resolution history |
| `GET` | `/api/v1/it/incidents/known-issues` | List matched known-issue patterns |

### 5.3 Sales Agent

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/sales/leads` | Ingest a new lead/CRM record |
| `POST` | `/api/v1/sales/insights/{lead_id}` | Generate customer insight (sentiment/needs) |
| `POST` | `/api/v1/sales/proposals/generate` | Generate a personalized proposal |
| `GET` | `/api/v1/sales/proposals/{proposal_id}` | Retrieve a generated proposal |

### 5.4 Executive Agent

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/executive/kpis?range=` | Retrieve aggregated KPI dashboard data |
| `GET` | `/api/v1/executive/trends?metric=` | Get trend/time-series data for a metric |
| `POST` | `/api/v1/executive/decision-support` | Get a recommendation for a strategic question |

---

## 6. Examples

### 6.1 HR Agent — Resume Screening

**Request**
```http
POST /api/v1/hr/resumes/screen
Content-Type: application/json
```
```json
{
  "job_id": "job_2031",
  "candidate": {
    "name": "Priya Sharma",
    "resume_text": "5 years experience in backend development with Python, FastAPI, PostgreSQL...",
    "resume_file_url": "s3://resumes/priya_sharma.pdf"
  }
}
```

**Response**
```json
{
  "candidate_id": "cand_8841",
  "job_id": "job_2031",
  "match_score": 87.5,
  "skill_matches": ["Python", "FastAPI", "PostgreSQL", "REST APIs"],
  "missing_skills": ["Kubernetes"],
  "recommendation": "shortlist",
  "summary": "Strong backend engineering background with 5 years relevant experience; minor gap in container orchestration skills.",
  "created_at": "2026-07-10T09:12:00Z"
}
```

### 6.2 IT Agent — Root Cause Analysis

**Request**
```http
POST /api/v1/it/tickets/tkt_5521/rca
Content-Type: application/json
```
```json
{
  "ticket_id": "tkt_5521",
  "logs": [
    "2026-07-10T02:14:00Z ERROR db_connection_pool: timeout after 30s",
    "2026-07-10T02:14:05Z WARN api_gateway: 503 upstream unavailable"
  ],
  "affected_service": "checkout-service"
}
```

**Response**
```json
{
  "ticket_id": "tkt_5521",
  "severity": "high",
  "root_cause": "Database connection pool exhaustion caused by an unclosed transaction leak in the checkout-service payment handler.",
  "matched_known_issue": "KI-0092",
  "recommended_fix": "Apply patch to close DB sessions in payment_handler.py; increase pool size as a short-term mitigation.",
  "auto_remediated": false,
  "escalated_to": "backend-oncall",
  "generated_at": "2026-07-10T02:20:00Z"
}
```

### 6.3 Sales Agent — Proposal Generation

**Request**
```http
POST /api/v1/sales/proposals/generate
Content-Type: application/json
```
```json
{
  "lead_id": "lead_3390",
  "customer_name": "Northwind Traders",
  "needs_summary": "Looking to automate inventory reporting across 12 warehouses.",
  "budget_range": "50000-75000",
  "product_line": "Enterprise Analytics Suite"
}
```

**Response**
```json
{
  "proposal_id": "prop_1187",
  "lead_id": "lead_3390",
  "pricing_tier": "Enterprise",
  "estimated_value": 68000,
  "proposal_document_url": "s3://proposals/prop_1187.pdf",
  "key_points": [
    "Automated multi-warehouse inventory dashboards",
    "Real-time anomaly alerts",
    "12-week implementation timeline"
  ],
  "generated_at": "2026-07-10T10:05:00Z"
}
```

### 6.4 Executive Agent — KPI Dashboard

**Request**
```http
GET /api/v1/executive/kpis?range=last_30_days
```

**Response**
```json
{
  "range": "last_30_days",
  "hr": {
    "open_positions": 14,
    "avg_time_to_hire_days": 21,
    "shortlist_rate": 0.34
  },
  "it": {
    "tickets_resolved": 402,
    "avg_mttr_minutes": 47,
    "auto_remediation_rate": 0.28
  },
  "sales": {
    "proposals_generated": 56,
    "pipeline_value": 1240000,
    "win_rate": 0.31
  },
  "generated_at": "2026-07-10T11:00:00Z"
}
```

---

## 7. Database Structure

Each domain agent owns its own schema; the Executive Agent reads from a derived **Analytics Warehouse** rather than the source tables directly.

```mermaid
erDiagram
    JOBS ||--o{ CANDIDATES : "screened for"
    JOBS {
        string job_id PK
        string title
        string department
        text requirements
        timestamp created_at
    }
    CANDIDATES {
        string candidate_id PK
        string job_id FK
        string name
        text resume_text
        float match_score
        string recommendation
        timestamp created_at
    }

    TICKETS ||--o{ RCA_REPORTS : "generates"
    TICKETS {
        string ticket_id PK
        string affected_service
        string severity
        string status
        timestamp created_at
    }
    RCA_REPORTS {
        string report_id PK
        string ticket_id FK
        text root_cause
        string matched_known_issue
        boolean auto_remediated
        timestamp generated_at
    }

    LEADS ||--o{ PROPOSALS : "generates"
    LEADS ||--o{ INSIGHTS : "generates"
    LEADS {
        string lead_id PK
        string customer_name
        text needs_summary
        string budget_range
        timestamp created_at
    }
    PROPOSALS {
        string proposal_id PK
        string lead_id FK
        string pricing_tier
        float estimated_value
        string document_url
        timestamp generated_at
    }
    INSIGHTS {
        string insight_id PK
        string lead_id FK
        string sentiment
        text key_needs
        timestamp generated_at
    }

    KPI_SNAPSHOTS {
        string snapshot_id PK
        string source_agent
        string metric_name
        float metric_value
        date snapshot_date
    }
```

**Notes**
- `KPI_SNAPSHOTS` is populated by a periodic ETL job that reads from `CANDIDATES`, `TICKETS`, `RCA_REPORTS`, `LEADS`, and `PROPOSALS`, aggregating them into standard metrics (time-to-hire, MTTR, win rate, etc.).
- The Executive Agent's `/kpis` and `/trends` endpoints query `KPI_SNAPSHOTS` exclusively — it never has write access to other agents' tables, preserving domain ownership boundaries.
- Vector embeddings (resumes, ticket logs, CRM transcripts) are stored separately in a vector store, keyed by the same IDs (`candidate_id`, `ticket_id`, `lead_id`) for cross-referencing.

---

## 8. Tech Stack

### Prototype (Current Phase)

| Layer | Technology |
|---|---|
| **Chatbot UI** | Next.js — hosted on **Vercel** |
| **Agent Services** | Python (FastAPI) |
| **LLM / Brain Model** | **Groq API** (fast inference, e.g. `llama-3.3-70b-versatile` or `mixtral-8x7b`) |
| **LLM Orchestration** | Custom orchestrator (`groq_client.py`) with tool-use for structured outputs |
| **Relational DB** | PostgreSQL (one schema per agent) |
| **Vector Store** | pgvector or a managed vector DB |
| **Analytics Warehouse** | PostgreSQL materialized views |
| **Deployment** | Vercel (chatbot UI) + local / cloud VM (agent backend) |

### Production (Future Phase)

| Layer | Technology |
|---|---|
| **API Gateway** | FastAPI / Express.js + JWT auth, rate limiting, routing |
| **Messaging (optional)** | Kafka / RabbitMQ for async ticket/lead ingestion |
| **Deployment** | Docker Compose (dev) → Kubernetes (prod) |

---

## 9. Environment Variables

```env
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

## 10. Next Steps (Prototype)

1. Set up the Groq API client in `orchestrator/groq_client.py`.
2. Scaffold the four agent services with the folder structure in Section 4.
3. Define Pydantic/ORM models matching the schema in Section 7.
4. Implement the orchestrator with a shared prompt-template system per agent.
5. Build and deploy the chatbot UI to Vercel.
6. Wire the ETL job that populates `KPI_SNAPSHOTS` for the Executive Agent.
7. Write integration tests simulating the end-to-end flows in Section 3.

> **Production backlog:** Add API Gateway (auth, rate limiting, routing), Docker/Kubernetes deployment, and role-based access control once the prototype is validated.
