-- Enterprise Multi-Agent System (Prototype SQL Schema)
-- Database Engine: SQLite (compatible with PostgreSQL)

-- 1. HR Requisitions & Screening
CREATE TABLE IF NOT EXISTS job (
    job_id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    requirements TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS candidate (
    candidate_id VARCHAR(50) PRIMARY KEY,
    job_id VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    resume_text TEXT NOT NULL,
    match_score REAL NOT NULL,
    skills TEXT NOT NULL,
    missing_skills TEXT NOT NULL,
    recommendation VARCHAR(20) NOT NULL,
    summary TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES job(job_id)
);

-- 2. IT Service Desk & RCA
CREATE TABLE IF NOT EXISTS ticket (
    ticket_id VARCHAR(50) PRIMARY KEY,
    affected_service VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rcareport (
    report_id VARCHAR(50) PRIMARY KEY,
    ticket_id VARCHAR(50) NOT NULL,
    root_cause TEXT NOT NULL,
    matched_known_issue VARCHAR(50),
    auto_remediated BOOLEAN NOT NULL CHECK (auto_remediated IN (0, 1)),
    recommended_fix TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(ticket_id) REFERENCES ticket(ticket_id)
);

-- 3. Sales Leads & Proposals
CREATE TABLE IF NOT EXISTS lead (
    lead_id VARCHAR(50) PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    needs_summary TEXT NOT NULL,
    budget_range VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS proposal (
    proposal_id VARCHAR(50) PRIMARY KEY,
    lead_id VARCHAR(50) NOT NULL,
    pricing_tier VARCHAR(50) NOT NULL,
    estimated_value REAL NOT NULL,
    key_points TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(lead_id) REFERENCES lead(lead_id)
);

CREATE TABLE IF NOT EXISTS insight (
    insight_id VARCHAR(50) PRIMARY KEY,
    lead_id VARCHAR(50) NOT NULL,
    sentiment VARCHAR(20) NOT NULL,
    key_needs TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(lead_id) REFERENCES lead(lead_id)
);

-- 4. Executive Analytics Store
CREATE TABLE IF NOT EXISTS kpisnapshot (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_agent VARCHAR(50) NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    metric_value REAL NOT NULL,
    snapshot_date DATE NOT NULL
);
