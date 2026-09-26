# PROJECT_JANAMKUNDLI.md
# ASIP — AI Society Intelligence Platform
### Complete Engineering History & Life Story of the Project

> **"Janamkundli"** — जैसे जन्मकुंडली में किसी की पूरी life history होती है, वैसे ही यह document ASIP project की पूरी journey है — शुरुआत से लेकर आज तक।

---

## Table of Contents
1. Project Overview
2. Why This Project Exists
3. Technology Stack
4. Project Architecture
5. Request Lifecycle
6. Folder / File Structure
7. Database Design
8. ORM / SQLAlchemy Design
9. Pydantic / Schema Design
10. Router → Service → Repository Pattern
11. Authentication / Authorization
12. Concurrency & Async Design
13. API Documentation
14. Error Handling
15. Development Timeline
16. Decision Log
17. Problems, Bugs & Fixes
18. Failed Approaches
19. Important Concepts We Learned
20. Important Code Flows
21. Current State
22. DO NOT BREAK THESE THINGS
23. New Developer Guide
24. Glossary
25. Final Project Story

---

## 1. Project Overview

### What Is ASIP?

**ASIP** stands for **AI Society Intelligence Platform**. It is an AI-powered operations center for **residential society management** — large apartment complexes common in Indian cities (Lodha, Godrej, DLF societies with multiple towers, hundreds of residents, water tanks, power infrastructure, and maintenance staff).

**Simple language mein:** Ek residential society mein bahut saari problems hoti hain — paani nahi aa raha, light chali gayi, pump overload ho gaya. Normally ek watchman ya maintenance team ko manually check karna padta hai. ASIP is poore process ko automate karta hai — sensors data collect karte hain, AI use analyze karta hai, sahi contractor ko automatically select karta hai, aur residents ko notify karta hai — sab kuch automatically.

### Main Problem It Solves

Traditional residential society management is **reactive** — problems discovered only after residents complain. ASIP makes it **proactive**:
- IoT sensors continuously monitor water pressure, power load, tank levels
- When anomaly detected, multiple AI agents analyze it in parallel
- The system automatically decides severity, impact, recommended action
- Residents notified, contractors dispatched — without human intervention for routine cases

### Who Uses It

| User Type | Role in System |
|-----------|---------------|
| **Admin** | Full system access, all incidents, all tenants |
| **Manager** | Manages incidents, approves contractors, views analytics |
| **Maintenance** | Views work orders, updates repair status |
| **Resident** | Views own notifications, files complaints |
| **Sensor Gateway** | IoT edge device that POSTs sensor readings |
| **Contractor** | Views assigned jobs |

### Current Status (as of July 2025)

- Backend: Fully functional FastAPI + LangGraph multi-agent system
- Frontend: Next.js 14 dashboard with real-time data
- Multi-tenant architecture (one PostgreSQL schema per society)
- 7 AI agents working in a dynamic supervisor-driven graph
- RAG (Retrieval Augmented Generation) memory using ChromaDB
- ML prediction layer with self-correcting learning loop
- Sensor buffer store-and-forward for offline IoT devices
- Resident complaint lifecycle management

### Main Technologies

- **Backend:** Python 3.11, FastAPI, SQLAlchemy 2.0 (async), PostgreSQL
- **AI/ML:** LangGraph, LangChain, OpenAI GPT-4o, Google Gemini, ChromaDB (RAG), scikit-learn
- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, Recharts
- **Infrastructure:** Alembic (migrations), asyncpg, SendGrid, Twilio, Docker

---

## 2. Why This Project Exists

### Original Problem Statement

The project was created to solve a real operational gap in large residential societies in India:

1. **Manual monitoring is unreliable** — A watchman cannot continuously watch 50 sensors across 10 towers
2. **Reactive problem-solving** — Residents complain → maintenance investigates → solution found (hours later)
3. **No institutional memory** — Same water pump failure happens every monsoon; no one remembers the fix
4. **Contractor selection is opaque** — Same contractor called regardless of performance history
5. **Residents have no visibility** — Don't know if complaint was registered or when it will be resolved

### What We Wanted to Achieve

- Sensor-to-resolution in minutes, not hours
- AI-driven root cause analysis — not just alerting, but actual diagnosis
- Evidence-based contractor selection — ranked by past performance, response time, resident feedback
- Resident-facing transparency — real-time status, automatic notifications
- Institutional memory — every incident, fix, and outcome stored and used for future predictions
- Self-improving system — predictions get more accurate as more feedback collected

### Requirements That Changed Over Time

| Original Requirement | How It Changed | Phase |
|---------------------|---------------|-------|
| Single society | Multi-tenant from Phase 2 | Phase 2 |
| Synchronous API | Fully async (asyncpg + SQLAlchemy async) | Phase 1 |
| Simple rule-based detection | LangGraph multi-agent workflow | Phase 2-3 |
| OpenAI only | Dual provider: OpenAI + Google Gemini | Phase 3 |
| Basic notifications | SendGrid (email) + Twilio (SMS) | Phase 3 |
| Manual contractor selection | Thompson Sampling + ML ranking | Phase 4 |
| LLM predictions only | ML model (scikit-learn) + learning loop | Phase 4-5 |
| No offline support | Sensor buffer store-and-forward | Phase 5 |
| No resident portal | Full resident-facing frontend | Phase 5 |

---

## 3. Technology Stack

### Backend

**Python 3.11+**
- Strong async support, rich ML/AI ecosystem
- Type hints for safety across codebase
- Used: Entire backend

**FastAPI**
- Modern ASGI web framework
- Native async, automatic OpenAPI/Swagger docs, dependency injection
- Used: All HTTP endpoints (app/api/)
- Simple explanation: FastAPI ek server hai jo HTTP requests sun'ta hai. Django se fast hai kyunki ye synchronous blocks nahi karta.

**SQLAlchemy 2.0 (Async)**
- Python ORM with full async support
- Mapped column syntax, connection pooling, event listeners
- Used: app/db/models/, app/repositories/, app/db/session.py

**PostgreSQL 15+**
- Schema-level multi-tenancy (one schema per society)
- JSONB for flexible sensor data storage
- UUID primary keys, ENUM types for status fields
- asyncpg driver for non-blocking I/O

**LangGraph**
- Graph-based multi-agent orchestration framework
- Allows directed graph of AI agents with conditional routing and state passing
- Used: app/agents/graph.py — the 7-node agent graph
- Simple explanation: LangGraph ek map jaisi cheez hai jisme har agent ek station hai. Supervisor decide karta hai ki kaun se agents ko chalana hai.

**LangChain**
- Framework for LLM-powered applications
- Prompt templates, output parsers, LLM abstraction (OpenAI and Google)
- Used: All agent files, memory_service.py, fallback.py

**OpenAI GPT-4o / GPT-3.5**
- Primary intelligence for incident classification, root cause analysis, notification drafting
- GPT-3.5-turbo used as Level 2 fallback when GPT-4 fails

**Google Gemini**
- Alternative LLM provider
- Same agent code works with both via LangChain abstraction
- Configured via llm_provider setting

**ChromaDB**
- Open-source vector database for RAG
- Stores embeddings of past incidents for retrieval
- Simple explanation: ChromaDB ek library hai jo past incidents ki "memories" store karta hai embedding format mein. Jab naya incident aata hai, system similar past incidents dhundh leta hai.

**instructor (Python library)**
- Wraps OpenAI/LLM clients to enforce structured JSON output via Pydantic models
- Prevents JSON parsing failures from LLM responses
- Used: app/core/llm/fallback.py

**numpy**
- Thompson Sampling — np.random.beta() for contractor ranking exploration
- Used: app/services/contractor_service.py

**scikit-learn**
- Training the predictive model for outage duration and cost prediction
- Runs as a separate background subprocess (not in main event loop)
- Used: app/ml/training_pipeline.py

**Alembic**
- Database migration tool for SQLAlchemy
- Schema versioning — safe, repeatable database changes
- Simple explanation: Jab bhi database mein koi naya column ya table add karna ho, Alembic ek version-controlled script banata hai.

**Pydantic v2 + pydantic-settings**
- Request/response schema validation
- Settings management via .env files
- Type enforcement at runtime

**SendGrid + Twilio**
- Email and SMS delivery for incident notifications

### Frontend

**Next.js 14 (App Router)**
- React framework with server-side rendering, file-based routing
- Fast page loads, SEO-friendly

**TypeScript**
- Type safety, IDE autocomplete, compile-time bug detection

**Tailwind CSS**
- Utility-first CSS framework for rapid UI development

**Recharts**
- React charting library for incident trend charts and analytics

**Lucide React**
- SVG icon library used throughout the UI

---

## 4. Project Architecture

### High-Level Architecture Diagram

```
                ┌────────────────────────────────────────────┐
                │              FRONTEND                       │
                │        Next.js 14 (App Router)             │
                │  Dashboard | Incidents | Analytics |        │
                │  Complaints | Residence | Sensor Buffer     │
                └──────────────────┬─────────────────────────┘
                                   │ HTTP/REST (JSON)
                                   │
                ┌──────────────────▼─────────────────────────┐
                │           BACKEND — FastAPI                 │
                │                                            │
                │  ┌──────────────────────────────────────┐  │
                │  │    Middleware Stack                   │  │
                │  │  CORSMiddleware → TenantMiddleware    │  │
                │  └──────────────────────────────────────┘  │
                │                                            │
                │  Routers (12 routers):                     │
                │  auth | incidents | dashboard | analytics  │
                │  contractors | complaints | notifications  │
                │  feedback | predict | sensor-buffer | ...  │
                └──────────────────┬─────────────────────────┘
                                   │
                ┌──────────────────▼─────────────────────────┐
                │           SERVICE LAYER                     │
                │                                            │
                │  WorkflowService ─── LangGraph Pipeline    │
                │       monitoring_agent                     │
                │       supervisor_decider                   │
                │       infrastructure_agent                 │
                │       impact_analysis_agent                │
                │       contractor_agent                     │
                │       communication_agent                  │
                │       decision_agent                       │
                │       supervisor_agent (aggregator)        │
                │                                            │
                │  contractor_service | feedback_service     │
                │  learning_service | predictive_service     │
                │  memory_service | complaint_service        │
                └──────────────────┬─────────────────────────┘
                                   │
                ┌──────────────────▼─────────────────────────┐
                │      REPOSITORY / DATA LAYER               │
                │  SQLAlchemy Async Sessions                  │
                │                                            │
                │  ┌──────────────────────────────────────┐  │
                │  │         PostgreSQL                   │  │
                │  │  Schema: public (users, tenants)     │  │
                │  │  Schema: tenant_X (all other tables) │  │
                │  └──────────────────────────────────────┘  │
                │                                            │
                │  ┌──────────────────────────────────────┐  │
                │  │         ChromaDB                     │  │
                │  │  Collection: asip_knowledge_base     │  │
                │  │  Stores: incident memory embeddings  │  │
                │  └──────────────────────────────────────┘  │
                └────────────────────────────────────────────┘
```

### Tenant Architecture

```
PostgreSQL Database: asip_db
│
├── Schema: public
│   ├── users          ← All login users (across all tenants)
│   └── tenants        ← Tenant registry (slug → schema_name)
│
├── Schema: tenant_lodha_park
│   └── (towers, apartments, residents, incidents, ...)
│
└── Schema: tenant_godrej_city
    └── (same tables, completely isolated)
```

### Key Design Principle: Everything Is Layered

- **Routers** handle HTTP — nothing else
- **Services** handle business logic — no HTTP objects
- **Repositories** handle database — no business decisions
- **Agents** handle AI reasoning — no direct DB or HTTP access
- **Middleware** handles cross-cutting concerns — no business logic

---

## 5. Request Lifecycle

### General Flow

```
Client (Browser / IoT Sensor)
    ↓
Uvicorn (ASGI server)
    ↓
FastAPI Application
    ↓
CORSMiddleware
    ↓
TenantMiddleware
    (reads X-Tenant-Slug header → resolves PostgreSQL schema → sets contextvar)
    ↓
OAuth2 token extraction (from Authorization header)
    ↓
Route matched (URL + HTTP method)
    ↓
Dependencies resolved:
    - get_db() → AsyncSession yielded
    - get_current_user() → JWT decoded → User fetched from DB
    - require_roles() → role membership checked
    ↓
Pydantic validates request body → 422 if invalid
    ↓
Handler function executes
    ↓
Service called (business logic)
    ↓
Repository called (DB queries via SQLAlchemy)
    ↓
SQLAlchemy executes SQL
    (search_path = tenant schema, set by after_begin event listener)
    ↓
Result flows back through layers
    ↓
Pydantic serializes response model
    ↓
HTTP Response
```

### Example 1: POST /incidents/sensor-data

```
IoT Sensor Gateway
    POST /incidents/sensor-data
    Headers: Authorization: Bearer <token>, X-Tenant-Slug: lodha-park
    Body: { "tower_id": "...", "sensor_type": "water_pressure", "value": 1.2 }
    ↓
TenantMiddleware: resolves "lodha-park" → schema "tenant_lodha_park"
    ↓
get_current_user(): decodes JWT → role == sensor_gateway ✓
    ↓
WorkflowService.process_sensor_data(payload)
    ↓
    LangGraph pipeline:
    monitoring_agent → classifies "water_pressure_drop", severity "high"
    supervisor_decider → selects agents to run
    infrastructure_agent → ReAct loop diagnosis
    impact_analysis_agent → ML prediction (residents affected, cost, hours)
    contractor_agent → Thompson Sampling ranking → best contractor selected
    communication_agent → notification drafts created
    decision_agent → autonomous escalation decision
    supervisor_agent → final aggregated report
    ↓
WorkflowService persists:
    Incident, AgentLogs, WorkflowRun, ContractorAssignment, IncidentMemory
    ↓
Response: { "incident_id": "...", "status": "analyzing", "type": "water_pressure_drop" }
```

### Example 2: GET /dashboard/summary

```
Frontend Browser
    GET /dashboard/summary
    Headers: Authorization: Bearer <token>, X-Tenant-Slug: lodha-park
    ↓
TenantMiddleware → sets schema
    ↓
get_current_user() → manager role ✓
    ↓
dashboard.py → get_summary()
    ↓
4 SQL queries:
    1. COUNT active incidents
    2. COUNT by severity
    3. 7-day trend (1 GROUP BY query — was 7 queries before optimization)
    4. 30-day trend (1 GROUP BY query — was 30 queries before optimization)
    ↓
Response: { kpi: {...}, incident_trend: [...], agent_activity: [...] }
```

### Example 3: POST /auth/login

```
Frontend Login Form
    POST /auth/login
    Body: { "email": "admin@asip.ai", "password": "admin123" }
    ↓
No TenantMiddleware effect (users are in public schema)
    ↓
UserRepository.authenticate(email, password)
    SELECT * FROM public.users WHERE email = ?
    bcrypt.verify(password, user.hashed_password)
    ↓
create_token_pair(user_id, email, role)
    access_token: JWT (60 min expiry)
    refresh_token: JWT (7 day expiry)
    ↓
Response: { "access_token": "eyJ...", "refresh_token": "eyJ..." }
```

---

## 6. Folder / File Structure

```
ASIP/
├── backend/
│   ├── app/
│   │   ├── main.py              ← FastAPI app, middleware, router mounting, lifespan
│   │   ├── config.py            ← All settings (pydantic-settings, reads .env)
│   │   ├── dependencies.py      ← get_current_user, require_roles
│   │   ├── routing_config.py    ← Agent routing weights for supervisor
│   │   │
│   │   ├── api/                 ← HTTP route handlers (thin — no business logic)
│   │   │   ├── auth.py          ← Login, refresh, /me
│   │   │   ├── incidents.py     ← Incident CRUD + sensor-data trigger
│   │   │   ├── dashboard.py     ← KPI summary, 7/30-day trends
│   │   │   ├── analytics.py     ← 30-day detailed analytics
│   │   │   ├── contractors.py   ← Contractor list + ranking
│   │   │   ├── complaints.py    ← Resident complaint lifecycle
│   │   │   ├── notifications.py ← Notification list/read
│   │   │   ├── feedback.py      ← Post-resolution feedback
│   │   │   ├── predict.py       ← ML impact prediction
│   │   │   ├── decision.py      ← Autonomous decision history
│   │   │   ├── sensor_buffer.py ← IoT buffer upload + replay
│   │   │   └── agent_logs.py    ← Agent execution log viewer
│   │   │
│   │   ├── agents/              ← LangGraph multi-agent system
│   │   │   ├── state.py         ← ASIPState TypedDict (shared state between agents)
│   │   │   ├── graph.py         ← Graph definition, compilation, caching
│   │   │   ├── llm.py           ← get_llm() factory
│   │   │   ├── schemas.py       ← Pydantic models for LLM structured output
│   │   │   ├── monitoring.py    ← Agent 1: anomaly detection
│   │   │   ├── infrastructure.py ← Agent 2: root cause (ReAct loop)
│   │   │   ├── impact_analysis.py ← Agent 3: resident impact + ML
│   │   │   ├── contractor.py    ← Agent 4: contractor selection
│   │   │   ├── communication.py ← Agent 5: notification drafting
│   │   │   ├── decision.py      ← Agent 6: autonomous decisions
│   │   │   └── supervisor.py    ← Agent 7: orchestrator + final report
│   │   │
│   │   ├── core/
│   │   │   ├── auth.py          ← JWT create/decode (HS256)
│   │   │   ├── exceptions.py    ← ASIPException, HTTP helpers
│   │   │   ├── logging.py       ← Structured logging (structlog)
│   │   │   ├── tenant_context.py ← ContextVar: current tenant schema
│   │   │   ├── tenant_middleware.py ← TenantMiddleware + LRU cache
│   │   │   ├── request_context.py ← ContextVar: trace_id for correlation
│   │   │   └── llm/
│   │   │       ├── chain.py         ← invoke_chain() base call
│   │   │       ├── fallback.py      ← 3-level graceful degradation
│   │   │       └── circuit_breaker.py ← Async circuit breaker
│   │   │
│   │   ├── db/
│   │   │   ├── base.py          ← SQLAlchemy Base + common fields (id, timestamps)
│   │   │   ├── session.py       ← Engine, SessionFactory, get_db(), tenant listener
│   │   │   └── models/
│   │   │       ├── __init__.py      ← All model imports (for Alembic)
│   │   │       ├── tenant.py        ← Tenant registry
│   │   │       ├── user.py          ← User + UserRole enum
│   │   │       ├── tower.py         ← Tower (building) + InfrastructureType
│   │   │       ├── resident.py      ← Apartment + Resident
│   │   │       ├── incident.py      ← Incident + Type/Severity/Status enums
│   │   │       ├── incident_memory.py ← RAG memory + feedback storage
│   │   │       ├── contractor.py    ← Contractor + ContractorAssignment
│   │   │       ├── contractor_history.py ← Historical job records
│   │   │       ├── notification.py  ← Notification records
│   │   │       ├── agent_log.py     ← Per-agent execution logs
│   │   │       ├── workflow_run.py  ← Workflow run tracking
│   │   │       ├── maintenance_record.py ← Maintenance history
│   │   │       ├── sensor_event_buffer.py ← Offline IoT event queue
│   │   │       ├── complaint.py     ← Resident complaints
│   │   │       └── evaluation_result.py ← LLM evaluation results
│   │   │
│   │   ├── repositories/        ← ALL database access
│   │   │   ├── incident_repo.py
│   │   │   ├── contractor_repo.py
│   │   │   ├── user_repo.py
│   │   │   ├── complaint_repo.py
│   │   │   ├── sensor_buffer_repo.py
│   │   │   └── ... (one per model group)
│   │   │
│   │   ├── schemas/             ← Pydantic request/response schemas
│   │   │   ├── incident.py
│   │   │   ├── auth.py
│   │   │   ├── dashboard.py
│   │   │   ├── complaint.py
│   │   │   └── ...
│   │   │
│   │   ├── services/            ← Business logic
│   │   │   ├── workflow_service.py  ← Main pipeline orchestrator
│   │   │   ├── contractor_service.py ← Thompson Sampling ranking
│   │   │   ├── memory_service.py    ← ChromaDB RAG interface
│   │   │   ├── feedback_service.py  ← Feedback + Chroma reindex
│   │   │   ├── learning_service.py  ← Pure-math correction factors
│   │   │   ├── predictive_service.py ← ML-based impact prediction
│   │   │   ├── complaint_service.py ← Complaint lifecycle
│   │   │   └── sensor_buffer_service.py ← Store-and-forward
│   │   │
│   │   ├── ml/
│   │   │   └── training_pipeline.py ← scikit-learn training (subprocess)
│   │   │
│   │   ├── rag/                 ← RAG helper components
│   │   └── evaluation/          ← LLM evaluation framework
│   │
│   ├── alembic/                 ← Database migrations
│   ├── tests/                   ← Unit + integration tests
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── app/                 ← Next.js App Router pages
    │   │   ├── page.tsx         ← Main dashboard
    │   │   ├── layout.tsx       ← Root layout (wraps AuthProvider)
    │   │   ├── globals.css      ← Global styles + glass morphism
    │   │   ├── incidents/       ← Incident list + detail
    │   │   ├── analytics/       ← Analytics charts
    │   │   ├── complaints/      ← Complaint management
    │   │   ├── contractors/     ← Contractor ranking view
    │   │   ├── residence/       ← Resident portal
    │   │   ├── sensor-buffer/   ← IoT gateway dashboard
    │   │   ├── notifications/   ← Notification center
    │   │   ├── settings/        ← System settings
    │   │   └── agent-logs/      ← Agent execution log viewer
    │   │
    │   ├── components/
    │   │   ├── auth-provider.tsx ← Auth context + login form + demo mode
    │   │   └── sidebar.tsx      ← Navigation sidebar
    │   │
    │   └── lib/
    │       └── api.ts           ← All API calls + type definitions
    └── package.json
```

---

## 7. Database Design

### Multi-Tenant Schema Strategy

ASIP uses **PostgreSQL schema-based multi-tenancy**:
- `public` schema: global tables (`users`, `tenants`)
- Each society gets its own schema (e.g., `tenant_lodha_park`)
- Schema isolation via `SET search_path TO tenant_X, public` on every transaction
- This means a query like `SELECT * FROM incidents` automatically hits the correct tenant's incidents

### Complete Table List

**public schema:**
- `users` — all user accounts across all tenants
- `tenants` — registry mapping slug → schema_name

**Per-tenant schema (all other tables):**
- `towers` — residential buildings
- `apartments` — individual units in towers
- `residents` — people living in apartments
- `incidents` — detected problems (core table)
- `incident_memory` — RAG memory + ML feedback storage
- `contractors` — service providers
- `contractor_assignments` — incident-to-contractor linking
- `contractor_history` — historical job performance records
- `notifications` — resident notification records
- `agent_logs` — per-agent execution audit trail
- `workflow_runs` — LangGraph pipeline run tracking
- `maintenance_records` — maintenance history
- `sensor_event_buffer` — offline IoT event queue
- `complaints` — resident-filed complaints

### Key Tables in Detail

**incidents (central table)**
```
id               UUID PK
tower_id         UUID FK → towers.id (nullable)
type             ENUM (water_pressure_drop | water_shortage | tank_overflow |
                        power_outage | power_overload | abnormal_infrastructure)
severity         ENUM (low | medium | high | critical)
status           ENUM (detected | analyzing | action_planned |
                        in_progress | resolved | escalated)
confidence       FLOAT  -- AI confidence 0.0-1.0
description      TEXT
root_cause       TEXT   -- filled by infrastructure_agent
sensor_data      JSONB  -- raw sensor reading
ai_decision      JSONB  -- complete LangGraph state output
detected_at      TIMESTAMPTZ
resolved_at      TIMESTAMPTZ (nullable)
created_at       TIMESTAMPTZ
updated_at       TIMESTAMPTZ
```

**incident_memory (RAG + learning loop)**
```
id                   UUID PK
incident_uuid        UUID  -- links to incidents.id
incident_type        STRING
root_cause           TEXT
severity             STRING
affected_residents   INT
contractor_used      STRING
repair_duration_hours FLOAT  -- initially LLM estimate, updated with actual
predicted_outage_hrs FLOAT  -- stored at prediction time (V4)
actual_outage_hrs    FLOAT  -- stored when feedback arrives (V4)
predicted_cost       FLOAT  -- stored at prediction time (V4)
actual_cost          FLOAT  -- stored when feedback arrives (V4)
decision_accuracy    FLOAT  -- MAPE-based composite accuracy score (V4)
prediction_accuracy  FLOAT  -- outage-only accuracy score (V5)
```

**users (in public schema)**
```
id               UUID PK
email            STRING UNIQUE
hashed_password  STRING (bcrypt)
full_name        STRING
role             ENUM (admin | manager | maintenance | resident |
                        sensor_gateway | contractor)
is_active        BOOLEAN
resident_id      UUID nullable  -- soft link to tenant.residents.id
contractor_id    UUID nullable  -- soft link to tenant.contractors.id
```

**sensor_event_buffer (IoT offline support)**
```
id               UUID PK
sensor_id        STRING
idempotency_key  STRING UNIQUE  -- prevents duplicates on replay
payload          JSONB
event_timestamp  TIMESTAMPTZ
received_at      TIMESTAMPTZ
sync_status      ENUM (pending | synced | failed)
retry_count      INT
error_message    TEXT nullable
```

### ASCII ER Diagram

```
public.tenants                    public.users
┌─────────────────┐               ┌─────────────────┐
│ id PK           │               │ id PK           │
│ slug            │               │ email UNIQUE    │
│ schema_name     │               │ hashed_password │
└─────────────────┘               │ role ENUM       │
     [used by TenantMiddleware]    │ resident_id     │──→ residents.id (soft)
                                   │ contractor_id   │──→ contractors.id (soft)
                                   └─────────────────┘

[Inside each tenant schema:]

towers ──1:N──► apartments ──1:N──► residents
  │
  └──1:N──► incidents
               │
               ├──1:1──► contractor_assignments ──N:1──► contractors
               │                                              │
               ├──1:N──► notifications                        └──1:N──► contractor_history
               │
               ├──1:N──► agent_logs
               │
               └──1:N──► maintenance_records

incidents ──→ incident_memory (via incident_uuid, no FK — cross-schema safety)

sensor_event_buffer (standalone — replayed events create incidents)

complaints ──→ incidents (via linked_incident_id on conversion)
```

---

## 8. ORM / SQLAlchemy Design

### Engine and Session — Lazy Initialization

```python
# session.py
_engine: Optional[AsyncEngine] = None

def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            pool_size=2,       # 2 persistent connections (low-end hardware)
            max_overflow=3,    # burst to 5 total
            pool_recycle=300,  # recycle after 5 min (prevent stale connections)
            pool_pre_ping=True # verify connection health before use
        )
    return _engine
```

Engine is created LAZILY — this fixed "Future attached to a different loop" errors that occurred when engine was created at module import time.

### Session Lifecycle

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()    # auto-commit on success
        except Exception:
            await session.rollback()  # auto-rollback on exception
            raise
        finally:
            await session.close()
```

Every FastAPI route uses `db: AsyncSession = Depends(get_db)`.
- Success path: automatically committed
- Exception path: automatically rolled back
- Always closed

### Model Definition (SQLAlchemy 2.0 Style)

```python
class Incident(Base):
    __tablename__ = "incidents"

    type: Mapped[IncidentType] = mapped_column(
        SAEnum(IncidentType, name="incident_type_enum"),
        nullable=False, index=True
    )
    sensor_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
```

`Mapped[T]` provides type safety and IDE support. All models inherit from `Base` which provides `id`, `created_at`, `updated_at`.

### Tenant Isolation via Event Listener

```python
@event.listens_for(Session, "after_begin")
def set_search_path_listener(session, transaction, connection):
    schema = get_tenant_schema()  # reads Python contextvar
    if schema and schema != "public":
        safe_schema = str(quoted_name(schema, quote=True))
        connection.exec_driver_sql(f"SET search_path TO {safe_schema}, public")
```

Every transaction automatically gets scoped to the correct tenant schema. No repository code needs to know about tenancy. The `quoted_name()` safely escapes the identifier, preventing SQL injection.

### Important Session Settings

```python
async_sessionmaker(
    expire_on_commit=False,  # don't expire objects after commit
    autoflush=False,         # manual control of flush timing
)
```

`expire_on_commit=False` is important — without it, accessing attributes after `commit()` triggers another SELECT. Since we use `await db.refresh(obj)` explicitly where needed, this is the correct setting.

---

## 9. Pydantic / Schema Design

### Database Model vs Pydantic Schema

```
DATABASE MODEL (SQLAlchemy)      PYDANTIC SCHEMA
─────────────────────────        ──────────────────────────
Ye database ki "photo" hai       Ye API ki "language" hai
Columns = database fields        Fields = what client sends/receives
Used by: repositories            Used by: routers
Has: hashed_password             Never exposes: hashed_password
Has: sensor_data (JSONB)         May hide: internal-only fields
Has: ai_decision (large JSON)    May add: computed fields (tower_name)
```

### Example — Incident

```python
# SQLAlchemy Model
class Incident(Base):
    __tablename__ = "incidents"
    type: Mapped[IncidentType]
    severity: Mapped[IncidentSeverity]
    sensor_data: Mapped[Optional[dict]]  # raw sensor data, internal only
    ai_decision: Mapped[Optional[dict]]  # full LLM output, huge, internal

# Pydantic Request Schema
class IncidentCreate(BaseModel):
    tower_id: Optional[uuid.UUID] = None
    type: IncidentType
    severity: IncidentSeverity
    description: Optional[str] = None
    # NOT: id, created_at, updated_at (server-generated)

# Pydantic Response Schema
class IncidentOut(BaseModel):
    id: str
    type: str
    severity: str
    status: str
    tower_name: Optional[str] = None  # joined from Tower, not in Incident model
    detected_at: str
    # NOT: sensor_data (internal), ai_decision (huge/internal)
    model_config = ConfigDict(from_attributes=True)
```

### Validation Behavior

Pydantic automatically:
- Rejects missing required fields → `422 Unprocessable Entity`
- Coerces types: `"high"` → `IncidentSeverity.high`
- Validates enum values: `"invalid"` → 422
- Validates UUID format
- Runs `@field_validator` functions for custom logic

### Settings

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),  # reads from both locations
        case_sensitive=False,
    )
    database_url: str = Field(default="postgresql+asyncpg://...")
    openai_api_key: str = Field(default="")
```

`@lru_cache()` on `get_settings()` means `.env` is parsed exactly once at startup.

---

## 10. Router → Service → Repository Pattern

### Why This Pattern?

**Agar sab kuch router mein dalte:** Router functions 500 lines long ho jaate. Testing impossible. One change in DB breaks 5 routes. No reuse.

**Agar sab kuch service mein dalte (without repo):** Service mein raw SQL likhna padta. DB badlne pe service rewrite.

**Is pattern mein:** Har layer ka ek kaam hai. Change isolated hoti hai. Testing easy hai.

### Router Responsibilities

```python
# api/complaints.py
@router.post("/", response_model=ComplaintOut, status_code=201)
async def create_complaint(
    payload: ComplaintCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = require_roles(UserRole.resident, UserRole.manager),
) -> ComplaintOut:
    resident_id = current_user.resident_id if current_user.role == UserRole.resident else None
    complaint = await complaint_service.create_complaint(
        payload.model_dump(), db, resident_id=resident_id
    )
    return ComplaintOut.model_validate(complaint)
```

Router does: URL routing, auth check, Pydantic validation, ONE service call, return response. Nothing else.

### Service Responsibilities

```python
# services/complaint_service.py
async def create_complaint(data: dict, db: AsyncSession, resident_id=None) -> Complaint:
    # Business decisions here:
    repo = ComplaintRepository(db)
    if resident_id:
        data["resident_id"] = resident_id
    data.setdefault("status", ComplaintStatus.submitted)  # default status decision
    complaint = await repo.create(data)
    await db.commit()
    logger.info("Complaint created", complaint_id=str(complaint.id))
    return complaint
```

Service does: business rules, orchestration, decisions. No HTTP. Testable without HTTP.

### Repository Responsibilities

```python
# repositories/complaint_repo.py
class ComplaintRepository:
    async def get_by_id(self, id: uuid.UUID) -> Optional[Complaint]:
        stmt = select(Complaint).where(Complaint.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_complaints(self, status=None, page=1, page_size=20):
        stmt = select(Complaint)
        if status:
            stmt = stmt.where(Complaint.status == status)
        stmt = stmt.offset((page-1)*page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return result.scalars().all()
```

Repository does: SQL queries only. No business logic. No HTTP. If we switch to MongoDB, only this file changes.

---

## 11. Authentication / Authorization

### JWT Token Flow

```
Login:
    Client POST /auth/login { email, password }
        ↓
    bcrypt.verify(password, stored_hash)
        ↓
    create_token_pair():
        access_token = JWT { sub: user_id, role: "admin", exp: +60min }
        refresh_token = JWT { sub: user_id, exp: +7days }
        ↓
    Response: { access_token, refresh_token }

Subsequent Requests:
    Authorization: Bearer <access_token>
        ↓
    oauth2_scheme extracts token from header
        ↓
    get_current_user():
        decode_token() → jwt.decode(secret_key, HS256) → TokenData
        UserRepository.get_by_id(token_data.user_id)
        if not user or not user.is_active: raise 401
        ↓
    User object available in route handler

Token Refresh:
    POST /auth/refresh { refresh_token }
        ↓
    decode_token(refresh_token) → user_id
        ↓
    create_token_pair() → new pair
```

### Role-Based Authorization

```python
def require_roles(*roles: UserRole):
    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            allowed = ", ".join(r.value for r in roles)
            raise forbidden_http(f"Access denied. Required: {allowed}")
        return current_user
    return Depends(_check)
```

Usage: `current_user: User = require_roles(UserRole.admin, UserRole.manager)`

### Permissions Matrix

| Endpoint | resident | manager | admin | sensor_gateway |
|----------|----------|---------|-------|----------------|
| POST /auth/login | ✓ | ✓ | ✓ | ✓ |
| GET /dashboard/summary | ✗ | ✓ | ✓ | ✗ |
| POST /incidents/sensor-data | ✗ | ✗ | ✓ | ✓ |
| POST /complaints/ | ✓ | ✓ | ✓ | ✗ |
| GET /complaints/mine | ✓ | ✗ | ✗ | ✗ |
| GET /complaints/ | ✗ | ✓ | ✓ | ✗ |
| POST /sensor-buffer/upload | ✗ | ✗ | ✗ | ✓ |
| POST /feedback/{id} | ✗ | ✓ | ✓ | ✗ |

### Demo Mode (Frontend)

Frontend auth-provider has demo mode — three hardcoded credential sets that bypass the real API (for development/demo when backend is not running):
- `admin@asip.ai` + `admin123` → admin demo
- `resident1@asip.ai` + `password123` → resident demo
- `gateway@asip.ai` + `password123` → sensor_gateway demo

**Important bug that was fixed:** Originally `|| email.length > 0` was in the condition, meaning ANY failed login granted admin access. Fixed to only allow the three explicit pairs.

---

## 12. Concurrency & Async Design

### Why Fully Async?

ASIP handles many concurrent requests with potentially slow operations:
- LLM API calls: 2-10 seconds
- DB queries: 1-50ms

Without async: Server would block during LLM call → handles 1 request at a time → terrible throughput
With async: While waiting for LLM response, server handles other requests → 100x better throughput on same hardware

### Circuit Breaker Pattern

```
State: CLOSED (normal)
    ↓ LLM call fails
record_failure() [protected by asyncio.Lock]
    ↓ 5 consecutive failures
State: OPEN
    ↓ all LLM calls immediately return rule-based fallback (no API call)
    ↓ after 30 seconds
State: HALF-OPEN (probe)
    ↓ one test call
    success → State: CLOSED
    failure → State: OPEN again
```

The lock (`asyncio.Lock`) prevents race conditions when multiple concurrent requests trigger `record_failure()` simultaneously.

### Fallback Hierarchy

```
Level 1: GPT-4o (primary)
    ↓ fails
Level 2: GPT-3.5-turbo (faster, cheaper)
    ↓ fails
Level 3: Rule-based response (deterministic, no LLM)
    → "_degraded": true in response
    → Pipeline completes with reduced quality rather than crashing
```

### LangGraph State Checkpointing

LangGraph persists state to PostgreSQL via `AsyncPostgresSaver`. This means:
- If the server crashes mid-workflow, the state is preserved
- On restart, workflow can resume from last checkpoint
- In testing: `MemorySaver` (in-memory, no PostgreSQL needed)

### Sensor Buffer Store-and-Forward

For IoT sensors with intermittent connectivity:
```
Sensor offline → events accumulate locally on edge device
    ↓ connectivity restored
Sensor POSTs batch to /sensor-buffer/upload
    → stored in sensor_event_buffer table (idempotency_key prevents duplicates)
    ↓ Admin triggers /sensor-buffer/replay
WorkflowService processes each buffered event
    → success: mark_synced
    → failure: mark_failed, increment retry_count
```

---

## 13. API Documentation

### Core Endpoints

#### POST /incidents/sensor-data
```
Purpose: Trigger the full AI workflow from a sensor reading
Auth: sensor_gateway or admin
Request:
{
  "tower_id": "uuid",
  "sensor_type": "water_pressure",
  "value": 1.2,
  "unit": "bar",
  "threshold_min": 2.0,
  "timestamp": "2025-07-15T10:30:00Z"
}
Response:
{
  "incident_id": "uuid",
  "status": "analyzing",
  "type": "water_pressure_drop",
  "severity": "high"
}
Triggers: Full 7-agent LangGraph pipeline (async)
```

#### GET /dashboard/summary
```
Purpose: KPI summary for management dashboard
Auth: manager, admin
Response:
{
  "kpi": {
    "total_incidents": 47,
    "active_incidents": 8,
    "critical_incidents": 3,
    "resolved_today": 5
  },
  "incident_trend": [
    {"date": "Mon", "count": 4},
    ...7 days...
  ],
  "agent_activity": [
    {"agent_name": "MonitoringAgent", "executions_today": 288, ...},
    ...
  ],
  "severity_distribution": {"critical": 3, "high": 5, "medium": 12, "low": 27}
}
```

#### POST /feedback/{incident_id}
```
Purpose: Submit actual outcome data after incident resolution
Auth: manager, admin
Request:
{
  "actual_outage_hrs": 3.5,
  "actual_cost": 15000,
  "root_cause": "Pump seal failure — confirmed",
  "resolution_summary": "Seal replaced, pressure restored",
  "contractor_used": "Sharma Plumbing"
}
Response:
{
  "updated": true,
  "predicted_outage_hrs": 4.2,
  "actual_outage_hrs": 3.5,
  "decision_accuracy": 0.834
}
Side effects:
- Updates incident_memory with actuals
- Reindexes ChromaDB document (replaces predicted values with actuals)
- Triggers ML model retraining check (background subprocess)
```

#### POST /sensor-buffer/upload
```
Purpose: Batch upload buffered sensor events from offline IoT devices
Auth: sensor_gateway
Request:
{
  "events": [
    {
      "sensor_id": "pump-01",
      "idempotency_key": "pump-01-2025-07-15T10:30:00Z",
      "payload": {...sensor reading...},
      "event_timestamp": "2025-07-15T10:30:00Z"
    }
  ]
}
Response:
{
  "total_received": 5,
  "successful": 5,
  "failed": 0,
  "duplicate_skipped": 0
}
```

#### POST /complaints/{id}/convert
```
Purpose: Convert resident complaint to a formal incident
Auth: manager, admin
Request:
{
  "incident_type": "water_pressure_drop",
  "override_severity": "high"
}
Response:
{
  "complaint_id": "uuid",
  "incident_id": "uuid",
  "status": "converted"
}
Side effects:
- Creates Incident record
- Launches full LangGraph workflow (background task)
- Updates complaint.status to "converted_to_incident"
- Sets complaint.linked_incident_id
Atomicity: If incident creation fails, complaint status NOT changed
```

---

## 14. Error Handling

### Error Layers and Flow

```
Exception raised in Repository (e.g. IntegrityError)
    ↓
Service receives exception
    may wrap it in ASIPException, or let it bubble
    ↓
FastAPI exception handler catches it
    ↓
JSON error response sent to client
```

### Custom Exception Base

```python
class ASIPException(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message

@app.exception_handler(ASIPException)
async def asip_exception_handler(request, exc):
    return JSONResponse(status_code=400,
        content={"error": exc.code, "message": exc.message})
```

### HTTP Helper Functions

```python
# core/exceptions.py
def unauthorized_http(detail="Not authenticated"):
    raise HTTPException(status_code=401, detail=detail)

def forbidden_http(detail="Forbidden"):
    raise HTTPException(status_code=403, detail=detail)
```

### Error Type Reference

| Error | Status Code | When It Occurs | Where Raised |
|-------|-------------|----------------|--------------|
| Validation error | 422 | Request body fails Pydantic | FastAPI (automatic) |
| Invalid credentials | 401 | Wrong email/password | UserRepository |
| Invalid/expired JWT | 401 | Token decode fails | get_current_user() |
| User inactive | 401 | is_active = False | get_current_user() |
| Insufficient role | 403 | Role not in allowed list | require_roles() |
| Not found | 404 | get_by_id() returns None | Router handler |
| Complaint conversion fail | 400 | ValueError from service | complaints.py |
| Workflow failure | 500 | LangGraph unhandled exception | workflow_service.py |
| Global unhandled | 500 | Any uncaught exception | global_exception_handler |

### Global Fallback Handler

```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(status_code=500, content={
        "error": "INTERNAL_SERVER_ERROR",
        "message": "An unexpected error occurred."
    })
```

This ensures that no raw Python tracebacks ever reach the client.

### LLM Error Handling (Fallback Chain)

```python
# core/llm/fallback.py
async def invoke_with_fallback(prompt, input_data, parser, agent_type, primary_llm, response_model=None):
    # Level 1: primary LLM
    if not circuit_breaker.is_open("primary"):
        try:
            result = await invoke_chain(prompt, primary_llm, parser, input_data)
            circuit_breaker.record_success("primary")
            return result
        except Exception:
            circuit_breaker.record_failure("primary")

    # Level 2: fallback LLM
    if not circuit_breaker.is_open("fallback"):
        try:
            result = await invoke_chain(prompt, fallback_llm, parser, input_data)
            return result
        except Exception:
            circuit_breaker.record_failure("fallback")

    # Level 3: rule-based minimal response
    return _get_rule_based_response(agent_type)
```

---

## 15. Development Timeline

The development period was **April 2025 to July 26, 2025** — approximately 4 months.

### Phase 1 — Foundation (April 2025)

**What we wanted:**
- Working FastAPI application
- PostgreSQL database connection
- Basic incident CRUD

**What was built:**
- FastAPI app with Uvicorn
- SQLAlchemy async setup (asyncpg driver)
- Initial database models: Incident, Tower, Resident, User
- Basic REST endpoints: incidents CRUD
- JWT authentication (login, refresh, /me)
- Alembic migrations setup

**Key decisions made:**
- Async-first from day one (no sync SQLAlchemy)
- UUID primary keys everywhere
- Repository pattern established early
- pydantic-settings for configuration

**Problems encountered:**
- Engine created at module import time → "Future attached to a different loop" error
- Fix: lazy engine initialization (create engine on first use, not at import)

---

### Phase 2 — Multi-Tenancy + Agent Pipeline (May 2025)

**What we wanted:**
- Multiple societies on one database
- First version of the AI agent pipeline

**What was built:**
- PostgreSQL schema-based multi-tenancy
- TenantMiddleware (X-Tenant-Slug header → schema resolution)
- ContextVar for current_tenant_schema
- SQLAlchemy after_begin event listener (SET search_path automatically)
- First LangGraph agent graph: monitoring_agent → infrastructure_agent → supervisor
- ChromaDB integration for RAG memory
- memory_service.py with vector similarity search

**Key decisions made:**
- Schema-per-tenant (vs. row-level tenancy with tenant_id column)
  - Reason: Complete data isolation, simpler queries (no WHERE tenant_id = X everywhere)
  - Tradeoff: Schema management complexity
- Users in public schema (login crosses tenant boundaries)
- LangGraph chosen over custom orchestration code

**Problems encountered:**
- Cross-schema foreign keys (users.resident_id → tenant.residents.id) would fail
- Fix: soft links (plain UUID columns, no FK constraint)
- TenantMiddleware cache was unbounded — memory leak risk in large deployments
- Fix: OrderedDict LRU cache bounded at 512 entries

---

### Phase 3 — Full Agent Pipeline + Notifications (May-June 2025)

**What we wanted:**
- All 7 agents working end-to-end
- Actual notifications sent to residents
- Dashboard with real data

**What was built:**
- impact_analysis_agent: queries DB for affected residents, ML prediction
- contractor_agent: DB-driven contractor ranking
- communication_agent: notification drafts via LLM
- decision_agent: autonomous escalation engine
- supervisor_agent: final report aggregation
- CircuitBreaker for LLM API resilience
- 3-level fallback (GPT-4 → GPT-3.5 → rule-based)
- SendGrid email + Twilio SMS integration
- Dashboard API (summary, analytics)
- LangGraph PostgreSQL checkpointing (AsyncPostgresSaver)

**Key decisions made:**
- Supervisor-driven dynamic agent selection (supervisor_decider decides which agents run)
  - Alternative: fixed pipeline (always run all agents)
  - Reason chosen: unnecessary agents skipped for low-severity incidents
- Graph compiled once at startup (get_compiled_graph() with global cache)
  - Reason: compilation is expensive (100ms+), should not happen per-request
- AsyncOpenAI client as singleton in fallback.py
  - Reason: each client creation opens connection pool; N requests × new client = connection explosion

**Problems encountered:**
- N+1 queries: dashboard was running 37 separate queries (1 per day) for trend data
  - Fix: GROUP BY queries — 2 queries total for 7-day and 30-day trends
- memory_service.py used deprecated get_relevant_documents() → AttributeError
  - Fix: changed to .invoke() method (current LangChain API)
- impact_analysis_agent opened 2 separate DB sessions — double the connections
  - Fix: merged into single session, query results passed directly

---

### Phase 4 — ML + Learning Loop (June 2025)

**What we wanted:**
- ML-based predictions (not just LLM guessing)
- Self-improving system (learns from feedback)
- Thompson Sampling for contractor selection

**What was built:**
- predictive_service.py: ML model for outage duration + cost prediction
- learning_service.py: pure-math correction factor computation
- feedback_service.py: stores actual outcomes, updates ChromaDB
- training_pipeline.py: scikit-learn model training (runs as subprocess)
- Thompson Sampling in contractor_service.rank_contractors()
- IncidentMemory model extended: predicted_outage_hrs, actual_outage_hrs, predicted_cost, actual_cost
- POST /feedback/{incident_id} endpoint

**Math used (learning_service.py):**
```
For each incident:
  error_ratio = (predicted - actual) / max(1, actual)

Bias = mean(error_ratio)
  > 0: system overestimates
  < 0: system underestimates

Correction Factor = 1 / (1 + bias)
  new_prediction = base_prediction * correction_factor

Min samples required: 3 (below this, no correction applied)
Correction clamped to [0.5, 2.0] range
```

**Thompson Sampling for contractors:**
```
For each contractor:
  alpha = successes + 1
  beta  = failures + 1
  thompson_score = np.random.beta(alpha, beta)

Final score = 60% deterministic + 40% Thompson sample
Purpose: Explores newer contractors instead of always picking proven ones
```

**Problems encountered:**
- feedback_service.py was storing prediction values (not actuals) in ChromaDB
  - This contaminated RAG with incorrect data — future agents would retrieve wrong context
  - Fix: feedback endpoint now re-indexes the ChromaDB document with actual values
- contractor_service N+1: 2 queries per contractor in ranking loop (2N queries total)
  - Fix: 1 GROUP BY query for all aggregates + 1 window function query for evidence (2 queries total)
- Learning loop was computing corrections but not applying them to predictions
  - Fix: feedback_service passes correction_factors to predictive_service

---

### Phase 5 — Real Society Operations (July 2025)

**What we wanted:**
- Residents can interact with the system
- IoT offline support
- Complete complaint lifecycle

**What was built:**
- Resident-facing frontend pages (residence/, complaints/)
- Complaint model + lifecycle (submit → under_review → resolved → converted_to_incident)
- Sensor buffer store-and-forward (offline IoT support)
- New UserRole enum values: resident, sensor_gateway, contractor
- User.resident_id linking (connects login to resident profile)
- Complaint → Incident conversion endpoint
- Frontend: auth-provider.tsx with role-aware demo mode
- Frontend: all dashboard pages

**Problems encountered:**
- auth-provider.tsx: `|| email.length > 0` logic error gave admin access to any non-empty email
  - Fix: explicit credential pair matching only
- supervisor.py: `import importlib` used on every agent invocation to import memory_service
  - Fix: module-level import alias
- feedback_service.py: `import asyncio` inside function body (stdlib redundancy)
  - Fix: moved to module top
- main.py: `import sys` inside async lifespan function
  - Fix: moved to module top

---

### Phase 6 — Security & Performance Audit (September 2025)

**Round 1 audit — 22 fixes:**
- SQL injection in tenant search_path (used string formatting instead of quoted_name)
- Auth bypass in auth-provider.tsx (email.length > 0 bug)
- N+1 queries in dashboard (37 queries → 2)
- LangGraph graph recompiled every request (should be once)
- memory_service.py deprecated API usage
- Duplicate uuid import in incidents.py
- importlib.import_module() called on every supervisor invocation
- AsyncOpenAI client created per request (connection pool explosion)
- CircuitBreaker state mutations not protected by asyncio.Lock
- GPU/CSS optimizations for low-end hardware
- Date() computed multiple times per second in page.tsx

**Round 2 audit — 9 additional fixes:**
- importlib pattern in contractor.py (same as supervisor)
- asyncio import inside function body
- Contractor ranking N+1 (2N queries → 2 batched queries)
- for-loop list building → list comprehensions
- Dead code: require_tenant_scope() (never called)
- import sys inside async function → module top
- Triple blank lines cleanup across files

---

## 16. Decision Log

| Decision | What We Chose | Why | Alternatives | Phase |
|----------|--------------|-----|--------------|-------|
| Backend language | Python 3.11 | ML/AI ecosystem, async support | Node.js, Go | Phase 1 |
| Web framework | FastAPI | Async, auto docs, DI system | Django, Flask | Phase 1 |
| Database | PostgreSQL | JSONB, schema multi-tenancy, ENUMs | MySQL, MongoDB | Phase 1 |
| ORM | SQLAlchemy 2.0 async | Async sessions, event system, Alembic | Tortoise ORM, raw asyncpg | Phase 1 |
| Primary key type | UUID | Globally unique, no sequence collisions | Auto-increment INT | Phase 1 |
| Auth method | JWT (HS256) | Stateless, no session storage | OAuth2 with sessions | Phase 1 |
| Multi-tenancy model | Schema-per-tenant | Complete isolation, simpler queries | Row-level (tenant_id column) | Phase 2 |
| Tenant isolation mechanism | SET search_path via event listener | Transparent to all repo code | Passing tenant_id to every query | Phase 2 |
| Agent orchestration | LangGraph | Graph topology, state passing, checkpointing | Custom orchestration code | Phase 2 |
| Primary LLM | OpenAI GPT-4o | Best reasoning quality | Gemini, Claude | Phase 2 |
| Vector DB for RAG | ChromaDB | Open source, runs locally, no API cost | Pinecone, Weaviate | Phase 2 |
| Graph compilation | Cached (once per process) | Compilation is ~100ms — too expensive per request | Compile per request | Phase 3 |
| LLM client | Singleton AsyncOpenAI | Connection pool reuse | New client per request | Phase 3 |
| Contractor ranking | Thompson Sampling + deterministic hybrid | Balances exploitation and exploration | Pure deterministic scoring | Phase 4 |
| ML predictions | scikit-learn (separate subprocess) | Simple, no GPU needed, fast to train | PyTorch, TensorFlow | Phase 4 |
| Learning loop | Pure-function math module | Testable, no DB or async dependencies | Embedded in feedback_service | Phase 4 |
| Sensor offline support | PostgreSQL buffer table + idempotency_key | Prevents duplicates, uses existing infra | Redis queue, Kafka | Phase 5 |
| Frontend framework | Next.js 14 App Router | SSR, file routing, TypeScript first-class | Create React App, Vite | Phase 5 |
| CSS approach | Tailwind CSS | Rapid development, consistent design | Plain CSS, styled-components | Phase 5 |
| SQL injection prevention | quoted_name() from SQLAlchemy | Defence-in-depth for identifier quoting | Parameterized queries (not applicable for identifiers) | Phase 6 |

---

## 17. Problems, Bugs & Fixes

| # | Problem | Symptoms | Root Cause | Fix | Status |
|---|---------|----------|------------|-----|--------|
| 1 | Engine created at import time | "Future attached to a different loop" on startup | SQLAlchemy engine binds to event loop at creation; testing/startup creates multiple loops | Lazy engine init: create on first call, not at import | Fixed |
| 2 | Dashboard N+1 queries | Dashboard took 2-3 seconds to load; DB had 37 queries per page load | Loop ran one query per day for trend data | GROUP BY queries: 2 queries for 7-day + 30-day trends | Fixed |
| 3 | memory_service deprecated API | AttributeError: 'VectorStoreRetriever' has no 'get_relevant_documents' | LangChain API changed; old method removed | Changed to `.invoke()` method | Fixed |
| 4 | SQL injection in search_path | Potential schema injection via X-Tenant-Slug header | `f"SET search_path TO {schema}"` — unescaped string interpolation | `quoted_name(schema, quote=True)` wraps identifier safely | Fixed |
| 5 | Auth bypass in frontend | Any non-empty email + wrong password → admin access in demo mode | `email.length > 0` in OR condition | Explicit credential pair matching only | Fixed |
| 6 | LangGraph recompiled per request | High latency on every sensor-data call | `build_graph()` called inside request handler | Global `_compiled_graph` cache; set once at startup | Fixed |
| 7 | importlib on every invocation | Minor performance overhead | `importlib.import_module("app.services.memory_service")` called in each agent run | Module-level `import ... as _memory_service` | Fixed |
| 8 | AsyncOpenAI client per request | Connection pool exhaustion under load | New `AsyncOpenAI()` created in each fallback call | Singleton client pattern with module-level instance | Fixed |
| 9 | CircuitBreaker race condition | State corruption under concurrent requests | `allow_request()`, `record_failure()` were sync, no locking | `asyncio.Lock` protecting all state mutations; methods made async | Fixed |
| 10 | ChromaDB contamination by predictions | RAG retrieved wrong historical data | feedback_service stored prediction values (not actuals) in Chroma | Re-index with actual values when feedback arrives | Fixed |
| 11 | Contractor ranking N+1 | Slow contractor selection under load | 2 DB queries per contractor inside for-loop | 1 GROUP BY query + 1 window function query (2 total) | Fixed |
| 12 | Cross-schema FK constraint | Migration fails; FK from public.users to tenant.residents impossible | Different schemas, FK constraints cross schemas | Soft link: plain UUID column, no FK constraint | Fixed |
| 13 | TenantMiddleware memory leak | Server memory grows unbounded in large deployments | _TENANT_CACHE was unbounded dict | OrderedDict + LRU eviction at 512 entries | Fixed |
| 14 | impact_analysis double session | Extra DB connection per workflow run | Agent opened separate AsyncSessionFactory() context manager | Merged into single session, passed results directly | Fixed |
| 15 | asyncio import inside function | Minor: redundant import on every call | `import asyncio` inside `store_feedback()` function body | Moved to module-level import | Fixed |
| 16 | WorkflowRun hardcoded version | Schema version "v5.1" duplicated as magic string | `_STATE_SCHEMA_VERSION = "v5.1"` constant not used | Used constant consistently everywhere | Fixed |
| 17 | Dead code: require_tenant_scope | Wasted code; misleading to future devs | Function defined, never called anywhere | Removed entirely | Fixed |
| 18 | GPU CSS excessive blur | Slow rendering on integrated graphics | `backdrop-filter: blur(12px)` on multiple elements | Reduced to `blur(8px)`, added `@supports` guard, `prefers-reduced-motion` | Fixed |
| 19 | Date() called repeatedly in page.tsx | Minor: date computed every render cycle | `new Date()` called 3+ times in same render | Computed once, reused | Fixed |

---

## 18. Failed Approaches

### Attempt 1: Engine Created at Module Level

```python
# FAILED APPROACH
engine = create_async_engine(settings.database_url, ...)
AsyncSessionFactory = async_sessionmaker(bind=engine, ...)
```

**Why tried:** Simple — import and use immediately.

**What happened:** `Future attached to a different loop` errors in tests. The engine was created when the test runner first imported the module, binding it to a temporary event loop. The actual test loop was different.

**Fix:** Lazy initialization — create engine on first DB call, not at module import.

---

### Attempt 2: Row-Level Multi-Tenancy

**Why considered:** Simpler to implement — add `tenant_id` column to every table, filter by it in every query.

**What happened:** Rejected before implementation.

**Problems identified:**
- Every query needs `WHERE tenant_id = ?`
- Easy to forget — data leak risk
- Bulk queries get complex
- No natural isolation between tenants

**What we chose instead:** Schema-per-tenant. Each tenant's data is in a completely separate PostgreSQL schema. `SET search_path` handles isolation transparently — no query changes needed.

---

### Attempt 3: Fixed Agent Pipeline (All Agents Always Run)

**Why considered:** Simpler — no supervisor_decider needed.

**What happened:** Rejected in design phase.

**Problems:**
- Low-severity incident (a minor notification) would still run contractor_agent, impact_analysis_agent — wasteful
- LLM costs scale with number of agents run
- Response time increases for simple cases

**What we chose instead:** Supervisor-driven dynamic selection. supervisor_decider evaluates incident type and severity, selects only relevant agents. A simple notification incident skips contractor and impact agents.

---

### Attempt 4: Per-Request AsyncOpenAI Client

```python
# FAILED APPROACH
async def invoke_with_fallback(...):
    client = AsyncOpenAI(api_key=settings.openai_api_key)  # new client every call
    ...
```

**What happened:** Under load testing, connection pool exhaustion. Each `AsyncOpenAI()` creates its own connection pool. 100 concurrent requests = 100 pools.

**Fix:** Singleton client — one `AsyncOpenAI` instance for the entire process, shared across all calls.

---

### Attempt 5: ChromaDB Stores Prediction Values as "Ground Truth"

```python
# FAILED APPROACH in feedback_service.py
# When feedback arrives, add a new document with the "actual" data
# But the OLD document with predictions still exists in ChromaDB
```

**What happened:** When agents queried RAG for similar incidents, they retrieved both the old (prediction) document and the new (actual) document. The LLM averaged them. Future predictions were biased toward the incorrect prediction values.

**Fix:** On feedback arrival, DELETE the old ChromaDB document and INSERT a new one with actual values. Replace, don't append.

---

### Attempt 6: Synchronous Circuit Breaker

```python
# FAILED APPROACH
def allow_request(self) -> bool:      # sync method
    ...mutate shared state...

def record_failure(self):             # sync method
    ...
```

**What happened:** Race condition. Two concurrent requests both check `failure_count`, both see it at 4, both call `record_failure()`. Count might only reach 5 instead of 6 due to read-modify-write racing. Circuit might not open when it should.

**Fix:** `asyncio.Lock` protects all state mutations. Methods made async.

---

## 19. Important Concepts We Learned

### ASGI (Asynchronous Server Gateway Interface)

**Technical definition:** Protocol that allows async Python web applications to communicate with web servers. Successor to WSGI.

**In ASIP:** FastAPI is an ASGI application. Uvicorn is an ASGI server. They communicate via this interface.

**Simple explanation:** WSGI ek purana standard tha jo synchronous tha. ASGI naya hai jo async requests handle kar sakta hai — matlab ek request ke wait karte hue doosri request process ho sakti hai.

---

### LangGraph State Machine

**Technical definition:** A directed graph where each node is a Python async function. State is a TypedDict passed between nodes. Edges can be conditional (route to different nodes based on state values).

**In ASIP:** ASIPState flows through all 7 agents. Each agent reads from state, adds its output, returns updated state. supervisor_decider uses conditional edges to decide which agents run.

**Simple explanation:** Sochiye ek assembly line mein — ek product conveyor belt pe chalti hai. Har station kuch kaam karta hai aur aage bhejta hai. LangGraph ek aisi assembly line hai jahan AI agents stations hain, aur state woh product hai jo sab agents ke paas se guzarta hai.

---

### Thompson Sampling

**Technical definition:** Bayesian exploration-exploitation algorithm. Draws random samples from a Beta distribution parameterized by successes and failures. Naturally selects better performers while still exploring newer options.

**In ASIP:** Used for contractor selection. Instead of always picking the contractor with highest historical success rate, the system sometimes picks a lesser-known contractor who might actually be better.

**Simple explanation:** Agar hum sirf best-rated contractor ko always choose karein, nayi contractors ko kabhi chance nahi milega. Thompson Sampling sometimes nayi contractor ko try karta hai — agar woh accha karta hai, rating badhti hai; agar kharab karta hai, woh kam select hota hai. Exploration vs exploitation ka balance.

---

### RAG (Retrieval Augmented Generation)

**Technical definition:** Pattern where an LLM's prompt is augmented with relevant documents retrieved from a vector database based on semantic similarity.

**In ASIP:** When infrastructure_agent analyzes a new water pressure incident, it queries ChromaDB for the 5 most similar past incidents. Those incidents (with root causes and fixes) are included in the LLM prompt. The LLM then has real historical context, not just its training data.

**Simple explanation:** LLM ki ek limitation hai — wo sirf training data jaanta hai, specific society ki history nahi. RAG ek librarian ki tarah hai — pehle similar past incidents ki history dhundh laata hai, phir LLM ko deta hai ki "pichli baar aise hua tha, aaj bhi dekho." Isse LLM ka answer zyada relevant hota hai.

---

### Circuit Breaker Pattern

**Technical definition:** Stateful wrapper around a potentially failing external service. Tracks failure count. When threshold exceeded, "opens" circuit — all calls immediately return fallback without attempting the service.

**In ASIP:** Wraps LLM API calls. If OpenAI API is down or rate-limited, circuit opens and all agents use rule-based fallback instead of hammering a broken API.

**Simple explanation:** Ghar mein circuit breaker hota hai — zyada current aaye toh trip kar deta hai taki aur damage na ho. Yahaan bhi same — agar LLM API repeatedly fail ho, circuit breaker "trip" kar deta hai aur fallback responses deta hai. API ke wapas aane pe reset ho jaata hai.

---

### Async/Await in Python

**Technical definition:** Python's cooperative multitasking. `await` suspends the current coroutine and yields control back to the event loop, which can run other coroutines.

**In ASIP:** Every DB query, LLM call, and HTTP call uses `await`. While waiting for a 4-second LLM response, the event loop processes other incoming requests. This gives near-concurrent behavior without threads.

**Simple explanation:** Synchronous mein: ek kaam karo, phir doosra. Async mein: pehla kaam start karo, jab wo wait pe hai toh doosra kaam karo. Jaise ek chef multiple dishes cook karta hai — ek stove pe hai, doosri marinate ho rahi hai, teesri oven mein hai. Thread nahi, sirf smart scheduling.

---

### Multi-Tenancy via PostgreSQL Schemas

**Technical definition:** Multiple isolated datasets in one database instance. Each tenant gets a separate schema. Queries auto-route to the right schema via `SET search_path`.

**In ASIP:** Society A and Society B can both have an `incidents` table with the same structure. They never see each other's data because each connection runs with a different `search_path`.

**Simple explanation:** Ek apartment building mein kai flats hain — har flat ka apna lock hai. PostgreSQL schema-tenancy bhi aisi hi hai — har society ka apna "flat" hai database mein. Ek society ki incidents doosri society ko kabhi nahi dikhti.

---

### Connection Pooling

**Technical definition:** Maintaining a pool of pre-established database connections that are reused across requests instead of creating a new connection for each request.

**In ASIP:** Pool of 2-5 PostgreSQL connections shared across all concurrent requests. Creating a new PostgreSQL connection takes ~10-20ms. With pooling, checkout from pool takes <1ms.

**Simple explanation:** Ek office mein agar har employee ko apna phone line chahiye, bahut wiring hogi. Pool mein: kuch shared lines hain, koi use kare toh le lo, kaam hone pe wapas rakho. Same connection DB ke saath.

---

### Store-and-Forward Pattern (Sensor Buffer)

**Technical definition:** Offline-first architecture where data is stored locally when connectivity is unavailable and forwarded to the server when connection is restored.

**In ASIP:** IoT sensors in towers may have intermittent WiFi. Buffered events accumulate in `sensor_event_buffer` table with idempotency keys. On reconnect, sensors replay all missed events. Idempotency key prevents processing the same event twice.

**Simple explanation:** Jaise WhatsApp mein message send nahi hota toh pending rehta hai aur internet aate hi chala jaata hai — same logic yahan. Sensor offline tha, readings store rahi hain, connection aaya toh sab ek saath bhej diya. Duplicate na ho isliye har reading ka unique ID hai.

---

## 20. Important Code Flows

### Flow 1: Sensor Reading → Incident → Notification

```
IoT Sensor (water pump)
    │ detects pressure drop
    ↓
POST /incidents/sensor-data
    { tower_id, sensor_type: "water_pressure", value: 1.2, threshold_min: 2.0 }
    ↓
TenantMiddleware: X-Tenant-Slug → schema → contextvar
    ↓
Pydantic: SensorDataIn validates body
    ↓
WorkflowService.process_sensor_data(payload)
    ↓
    initial_state = {
        sensor_data: payload,
        incident_id: new UUID,
        trace_id: from contextvar,
        _schema_version: "v5.1"
    }
    ↓
    graph.ainvoke(initial_state)
    ↓
    [Node 1] monitoring_agent:
        LLM classifies sensor readings
        → IncidentEvent { type: "water_pressure_drop", severity: "high", confidence: 0.94 }
    ↓
    [Router] _monitoring_router:
        incident_event exists? YES → "supervisor_decider"
    ↓
    [Node 2] supervisor_decider:
        evaluates incident type + severity
        selects agents: ["infrastructure_agent", "impact_agent",
                         "contractor_agent", "communication_agent", "decision_agent"]
        sets state["selected_agents"]
    ↓
    [Node 3] infrastructure_agent:
        ReAct loop: LLM reasons about probable cause
        Fetches similar incidents from ChromaDB (RAG)
        → diagnosis: { probable_cause: "Pump seal failure",
                       recommended_action: "Replace seal, flush pipes",
                       confidence: 0.87 }
    ↓
    [Node 4] impact_analysis_agent:
        SELECT residents in affected tower → 312 residents
        ML prediction: outage_hrs=4.2, cost=18000
        learning_service applies correction_factor: 4.2 * 0.96 = 4.03 hrs
        → impact: { affected_residents: 312, severity_score: 8.2, priority: "high" }
    ↓
    [Node 5] contractor_agent:
        contractor_service.rank_contractors(incident_type, k=5)
        Thompson Sampling + deterministic hybrid scoring
        LLM selects top contractor
        → recommendation: { contractor: "Sharma Plumbing", cost: 16500, time_hrs: 3.5 }
    ↓
    [Node 6] communication_agent:
        LLM drafts notification content
        Creates Notification records in DB
        → notifications: [{ channel: "email", recipient: "all_residents", ... }]
    ↓
    [Node 7] decision_agent:
        LLM evaluates: should we escalate? activate backup? dispatch immediately?
        → autonomous_decision: { requires_escalation: false, auto_dispatch: true, risk: 0.72 }
    ↓
    [Node 8] supervisor_agent:
        Aggregates all agent outputs
        LLM generates final human-readable report
        Creates IncidentMemory record (for future RAG retrieval)
        → final_report: { summary: "...", root_cause: "...", action_plan: "..." }
    ↓
    graph returns final_state
    ↓
WorkflowService:
    → Creates Incident record in PostgreSQL
    → Bulk-inserts AgentLog records (one per agent)
    → Updates WorkflowRun status to "completed"
    → Creates ContractorAssignment record
    ↓
Response: { incident_id, status: "analyzing", type: "water_pressure_drop" }
```

---

### Flow 2: Resident Files Complaint → Converted to Incident

```
Resident (logged in app)
    ↓
POST /complaints/
    { title: "No water since morning",
      description: "Tower B has no water since 7am",
      category: "water",
      priority: "high" }
    ↓
Router: current_user.role == resident ✓
    ↓
complaint_service.create_complaint(data, db, resident_id=current_user.resident_id)
    → ComplaintRepository.create(data)
    → complaint.status = "submitted"
    → db.commit()
    ↓
Response: { complaint_id, status: "submitted" }

[Later — Manager reviews complaint in dashboard]

POST /complaints/{complaint_id}/convert
    { incident_type: "water_shortage", override_severity: "high" }
    ↓
complaint_service.convert_to_incident(complaint_id, db, background_tasks)
    ↓
    Atomic transaction:
        1. GET complaint (verify it exists and not already converted)
        2. CREATE Incident record
        3. UPDATE complaint.status = "converted_to_incident"
        4. UPDATE complaint.linked_incident_id = incident.id
        5. COMMIT
    ↓
    background_tasks.add_task(WorkflowService.process_sensor_data, incident_data)
    (Full LangGraph pipeline runs in background — resident gets immediate response)
    ↓
Response: { complaint_id, incident_id, status: "converted" }
```

---

### Flow 3: Feedback → Learning Loop → Better Predictions

```
Incident resolved (pump repaired after 3.5 hours, actual cost ₹15,000)

Manager submits feedback:
POST /feedback/{incident_id}
    { actual_outage_hrs: 3.5, actual_cost: 15000, ... }
    ↓
feedback_service.store_feedback(incident_id, feedback)
    ↓
    1. UPDATE incident_memory SET
           actual_outage_hrs = 3.5,
           actual_cost = 15000
       WHERE incident_uuid = incident_id
    ↓
    2. ChromaDB: DELETE old document (which had predicted values)
       ChromaDB: INSERT new document (with actual values as ground truth)
    ↓
    3. Fetch last N=10 IncidentMemory records with feedback
    ↓
    4. learning_service.compute_correction_factors(feedback_records)
       For each record:
           error_ratio = (predicted - actual) / max(1, actual)
       bias = mean(error_ratios) = +0.20  (system was overestimating by 20%)
       correction_factor = 1 / (1 + 0.20) = 0.833
    ↓
    5. Store correction_factors (in-memory or cache)
    ↓
    6. asyncio.create_task(_trigger_model_retrain_if_needed())
       → computes rolling MAE
       → if MAE > threshold: spawns scikit-learn training subprocess
    ↓

[Next incident — water shortage in Tower A]
POST /incidents/sensor-data → impact_analysis_agent runs
    ↓
predictive_service.predict_impact(incident_type)
    → base ML prediction: 5.0 hrs
    → apply correction_factor: 5.0 * 0.833 = 4.17 hrs
    → return corrected prediction
    ↓
System now predicts more accurately than before
```

---

### Flow 4: Token Validation on Every Request

```
GET /incidents/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    ↓
oauth2_scheme: extracts token from Authorization header
    ↓
get_current_user(token, db):
    if token == "demo-token":
        → fetch admin@asip.ai from DB
        → return if active

    token_data = decode_token(token)
        → jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        → if expired: raises ValueError → 401 Unauthorized
        → returns TokenData { user_id, email, role }
    ↓
    user = UserRepository.get_by_id(token_data.user_id)
        SELECT * FROM public.users WHERE id = ?
        (always public schema — users table not tenant-scoped)
    ↓
    if not user or not user.is_active: raise 401
    ↓
    return user
    ↓
require_roles(manager, admin)(user):
    user.role in (manager, admin)? YES → proceed
    NO → raise 403 Forbidden
    ↓
Incident list returned
```

---

## 21. Current State (as of September 2025)

### What Is Working

**Backend — Fully Functional:**
- All 12 API routers operational
- 7-agent LangGraph pipeline end-to-end
- Multi-tenant schema isolation
- JWT authentication + role-based access
- ML prediction + learning loop
- Thompson Sampling contractor ranking
- ChromaDB RAG memory
- Sensor buffer store-and-forward
- Resident complaint lifecycle
- Post-resolution feedback with ChromaDB reindexing
- LangGraph PostgreSQL checkpointing
- 3-level LLM fallback with circuit breaker
- Structured logging with trace_id correlation

**Frontend — Functional:**
- Dashboard with KPI cards, incident trend charts
- Authentication with role-aware demo mode
- Incidents list and detail view
- Analytics page
- Complaints management
- Contractor ranking view
- Sensor buffer monitoring
- Notification center
- Agent logs viewer
- Settings page

### Known Limitations / Technical Debt

1. **Frontend uses mock data for some pages** — Several frontend pages (residence/, some analytics sections) display hardcoded mock data. Backend API calls are not fully wired to all pages.

2. **No real-time updates** — Dashboard requires manual refresh. No WebSockets or Server-Sent Events for live incident updates.

3. **Notification delivery is best-effort** — If SendGrid/Twilio fails, notification is marked failed but not automatically retried. No dead-letter queue.

4. **Training pipeline is a subprocess** — scikit-learn model training runs as a subprocess from Python. This is simple but not production-grade (no job queue, no distributed training).

5. **No rate limiting** — Sensor gateway endpoints have no rate limiting. A misbehaving sensor could flood the system.

6. **Demo mode in production code** — The demo token (`"demo-token"`) check in `get_current_user()` should be removed or gated behind an environment check for production.

7. **No automated tests for agents** — Unit tests for the LangGraph agents are incomplete. Testing agents requires mocking the LLM, which is not fully set up.

8. **Frontend has no error boundaries** — API errors in some pages cause uncaught exceptions.

### What Remains To Be Done

- Connect remaining frontend pages to live backend APIs
- WebSocket / SSE for real-time dashboard updates
- Rate limiting on sensor gateway endpoints
- Automated integration tests for the agent pipeline
- Notification retry queue (dead-letter pattern)
- Remove/gate demo-token in production mode
- Proper error boundaries in frontend
- Production deployment configuration (Docker Compose / Kubernetes)
- Monitoring/alerting (Prometheus + Grafana)

---

## 22. DO NOT BREAK THESE THINGS

### Architecture Rules

```
1. BUSINESS LOGIC BELONGS IN SERVICES — NOT ROUTERS, NOT REPOSITORIES.
   Routers call one service method. That's it.
   If you need to add business logic, it goes in a service.

2. DATABASE QUERIES BELONG IN REPOSITORIES — NOT SERVICES, NOT ROUTERS.
   Services call repository methods. They never call db.execute() directly.
   Exception: WorkflowService (complex orchestration — justified).

3. THE TENANT CONTEXTVAR MUST BE SET BEFORE ANY DB QUERY.
   All DB queries go to the tenant schema via the after_begin listener.
   If you create a new DB session path that bypasses TenantMiddleware,
   you WILL query the wrong schema.

4. THE CIRCUIT BREAKER MUST USE asyncio.Lock FOR STATE MUTATIONS.
   All methods that read-then-write CircuitBreaker state MUST hold the lock.
   Without the lock, race conditions corrupt the breaker state.

5. DO NOT STORE PREDICTIONS IN CHROMADB AS "GROUND TRUTH".
   ChromaDB documents must contain actual (confirmed) values, not predictions.
   When feedback arrives, DELETE old document and INSERT new one with actuals.
   Appending instead of replacing causes RAG contamination.

6. LANGGRAPH GRAPH MUST BE COMPILED EXACTLY ONCE PER PROCESS.
   get_compiled_graph() returns the cached compiled graph.
   Never call build_graph() directly from a request handler.
   Each compilation takes ~100ms and is not cheap.

7. USERS TABLE IS IN THE PUBLIC SCHEMA — NOT THE TENANT SCHEMA.
   Users authenticate across tenant boundaries.
   The resident_id and contractor_id links are soft links (no FK constraint).
   Do not add FK constraints from public.users to tenant.* tables.

8. THE ASYNC ENGINE MUST BE CREATED LAZILY.
   Do not create AsyncEngine at module import time.
   It must be created after the event loop is running.
   Use the get_engine() pattern in session.py.

9. THE IDEMPOTENCY KEY IN SENSOR BUFFER MUST REMAIN UNIQUE-CONSTRAINED.
   Removing the UNIQUE constraint will cause duplicate event processing
   when IoT devices retry uploads.

10. FEEDBACK MUST RE-INDEX CHROMADB, NOT JUST UPDATE POSTGRESQL.
    Post-resolution feedback updates BOTH incident_memory (PostgreSQL)
    AND the ChromaDB document. Updating only one causes data divergence.
    Future RAG queries will retrieve stale prediction values.
```

---

## 23. New Developer Guide

### First Understand

1. **The overall mission:** ASIP automates residential society incident management using a multi-agent AI pipeline. Every incident flows through 7 AI agents before a human ever sees it.

2. **The two databases:** PostgreSQL (structured data, multi-tenant via schemas) and ChromaDB (vector embeddings for RAG memory). They serve different purposes.

3. **The multi-tenant model:** One PostgreSQL database, many schemas. `X-Tenant-Slug` header → TenantMiddleware → schema contextvar → `SET search_path`. Every query silently goes to the right tenant.

### Then Read (In This Order)

1. [`app/db/models/__init__.py`](backend/app/db/models/__init__.py) — see all 16 database models and understand the data structure
2. [`app/agents/state.py`](backend/app/agents/state.py) — understand ASIPState (the shared state that flows through all agents)
3. [`app/agents/graph.py`](backend/app/agents/graph.py) — understand how the 7-agent pipeline is wired together
4. [`app/services/workflow_service.py`](backend/app/services/workflow_service.py) — understand how a sensor reading becomes an incident
5. [`app/main.py`](backend/app/main.py) — understand app startup, middleware order, router mounting

### Then Run

```bash
# 1. Start PostgreSQL and ChromaDB
docker-compose up -d postgres chromadb

# 2. Create virtual environment
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Set up .env file
cp .env.example .env
# Edit .env: add OPENAI_API_KEY, DATABASE_URL

# 4. Run Alembic migrations
alembic upgrade head

# 5. Start the backend
uvicorn app.main:app --reload --port 8000

# 6. Start the frontend
cd ../frontend
npm install
npm run dev  # runs on http://localhost:3000

# 7. Verify
curl http://localhost:8000/health
# {"status": "healthy", "version": "1.0.0"}
```

### Before Changing

1. **Adding a new API endpoint:** Create router handler (thin), add business logic to a service, add DB access to a repository. Never skip layers.

2. **Changing the agent pipeline:** Understand ASIPState first. Adding a new field to ASIPState requires bumping `_STATE_SCHEMA_VERSION` in workflow_service.py.

3. **Adding a new database model:** Add the model to `db/models/`, import it in `db/models/__init__.py` (Alembic needs this), then run `alembic revision --autogenerate`.

4. **Modifying ChromaDB behavior:** Review feedback_service.py carefully. The re-indexing logic (DELETE + INSERT) is intentional and must not be changed to append-only.

5. **Changing tenant isolation:** Any change to TenantMiddleware or the after_begin event listener affects ALL tenants. Test with multiple tenant schemas.

---

## 24. Glossary

**ASIP**
- Simple: AI Society Intelligence Platform
- In project: The complete platform name

**ASIPState**
- Simple: A Python dictionary that all AI agents share
- In project: TypedDict passed through every LangGraph node containing sensor data, incident event, diagnosis, impact, contractor recommendation, notifications, and final report

**LangGraph**
- Simple: A workflow manager for AI agents
- In project: Framework that defines the 7-agent pipeline as a directed graph with conditional routing

**Supervisor Agent**
- Simple: The boss agent that coordinates all other agents
- In project: Has two roles — supervisor_decider (selects which agents to run) and supervisor_agent (aggregates final report)

**RAG (Retrieval Augmented Generation)**
- Simple: Giving the LLM relevant history before asking a question
- In project: ChromaDB stores past incident memories. When new incident occurs, similar past incidents retrieved and injected into LLM prompt

**Tenant**
- Simple: One society/customer using ASIP
- In project: A row in `public.tenants` table mapping a slug to a PostgreSQL schema name

**Schema (PostgreSQL)**
- Simple: A namespace inside the database, like a folder
- In project: Each tenant has their own schema (e.g., tenant_lodha_park) containing all their data tables

**search_path (PostgreSQL)**
- Simple: Tells PostgreSQL which schema to look in first
- In project: Set to tenant schema on every transaction via after_begin event listener

**Circuit Breaker**
- Simple: Automatic shutdown when external service fails repeatedly
- In project: Wraps LLM API calls. Opens when 5+ consecutive failures. Returns rule-based fallback instead of calling broken API.

**Thompson Sampling**
- Simple: Smart randomness for choosing contractors
- In project: Balances proven contractors (exploitation) vs trying newer ones (exploration). Uses Beta distribution sampled from historical success/failure counts.

**Correction Factor (Learning Loop)**
- Simple: A multiplier that adjusts predictions based on past errors
- In project: learning_service computes bias from predicted vs actual values, derives correction factor. Applied by predictive_service to future predictions.

**Idempotency Key**
- Simple: A unique ID that prevents the same action from being done twice
- In project: sensor_event_buffer.idempotency_key has UNIQUE constraint. IoT sensors can safely retry uploads — duplicate events are silently skipped.

**Soft Link**
- Simple: A reference without a strict database constraint
- In project: public.users.resident_id references tenant.residents.id as a plain UUID column (no FK constraint). Cross-schema FK constraints are not possible.

**Worker / Event Loop**
- Simple: The async engine that runs all coroutines
- In project: Uvicorn starts one event loop per worker process. All async functions share this loop via cooperative scheduling.

**Fallback Chain**
- Simple: Plan A → Plan B → Plan C when things fail
- In project: GPT-4o → GPT-3.5-turbo → rule-based response. Ensures pipeline always completes even during total LLM outage.

**Store-and-Forward**
- Simple: Save now, send later
- In project: Sensor buffer pattern — IoT devices store readings locally when offline, forward them in batch when connectivity restored.

---

## 25. Final Project Story

*(The complete Janamkundli — project ki poori kahani)*

### Shuruaat (April 2025)

Project ASIP ki shuruat ek simple observation se hui: large residential societies mein infrastructure problems ka management bahut manual aur reactive tha. Ek society mein 10 towers, 500+ apartments, aur daily water/power issues — sab kuch watchman aur maintenance staff ke notes pe depend karta tha.

Humara goal tha: ek aisa system banao jo automatically detect kare, analyze kare, aur resolve kare — without human bottleneck for routine cases.

**April mein** humne foundation rakha:
- FastAPI aur PostgreSQL choose kiye — speed aur reliability ke liye
- Async-first architecture — isliye ki LLM calls slow hoti hain aur server block nahi karna tha
- JWT authentication — stateless, scalable
- Repository pattern — isliye ki future mein database change karna easy ho

Pehli problem pehle hi din aayi: SQLAlchemy engine module import pe create kiya — "Future attached to a different loop" error. Fix: lazy initialization.

### Pehla Milestone — Multi-Tenancy aur Agents (May 2025)

**May mein** hum real complexity mein aaye:

**Multi-tenancy:** Ek database mein kai societies. Schema-per-tenant choose kiya — har society ka apna isolated data. TenantMiddleware likha jo har request se `X-Tenant-Slug` header padta hai, PostgreSQL schema resolve karta hai, aur contextvar set karta hai. SQLAlchemy event listener ne har transaction pe automatically `SET search_path` kar diya — repositories ko kuch bhi change nahi karna pada.

Ek tricky problem: `public.users.resident_id` → `tenant.residents.id` ke beech FK constraint possible nahi tha cross-schema mein. Soft link banaya — plain UUID column, no FK.

**LangGraph agents:** Pehla version simple tha — monitoring → infrastructure → supervisor. Phir samjha ki har incident ke liye alag set of agents chahiye. Supervisor-driven dynamic selection design kiya: supervisor_decider decides which agents to run based on incident type and severity.

### Asli Intelligence (June 2025)

**June mein** system real AI bana:

Saare 7 agents build hue. Infrastructure agent ne ReAct loop use karna shuru kiya — LLM reasoning steps ke saath tools use karta hai. Impact analysis agent ne actual DB residents count karna shuru kiya.

**Contractor ranking** ek interesting problem tha. Pehle simple rating-based was. Phir Thompson Sampling introduce kiya — isliye ki agar hum sirf best contractor ko always choose karein, nayi contractors ko kabhi prove karne ka chance nahi milega. Thompson Sampling probabilistically explores — sometimes less-proven but potentially better contractors get selected.

**ChromaDB RAG:** Har incident ke baad IncidentMemory store hota hai. Agli baar similar incident pe, similar past incidents retrieve hokar LLM ko context milta hai. System apni history se seekhne laga.

**Ek bada bug:** ChromaDB mein prediction values store ho rahi theen as "ground truth." Jab feedback aaya actual values ke saath, humne sirf PostgreSQL update kiya — ChromaDB mein purani predictions rahi gayi. Future RAG queries galat context retrieve karti theen. Fix: feedback pe ChromaDB mein DELETE + INSERT (replace, not append).

### Learning Loop aur Real Society Features (July 2025)

**July mein** system intelligent bana:

**Learning loop:** Predictions vs actuals compare karna shuru kiya. learning_service.py ek pure-math module banaya (no DB, no async) jo correction factors compute karta hai. Agar system consistently overestimate karta hai, correction factor predictions reduce karta hai. 3+ feedback records ke baad hi correction apply hoti — single outlier se overfit nahi hota.

**Sensor buffer:** IoT devices kabhi offline hote hain. Store-and-forward pattern implement kiya — buffer table mein events store hote hain, idempotency_key se duplicates prevent hote hain, replay pe sab process hota hai.

**Resident features:** Residents complaint file kar sakte hain. Manager complaint ko formal incident mein convert kar sakta hai — atomic transaction mein: incident create + complaint status update. Ek bhi fail hue toh rollback.

**Frontend:** Next.js 14 mein complete dashboard banaya — dark mode, glass morphism, real-time charts.

### Security Aur Performance Audit (September 2025)

**September mein** do rounds of comprehensive audit kiye:

**Round 1 mein** major issues mile:
- SQL injection: `f"SET search_path TO {schema}"` — unescaped schema name. Fix: `quoted_name()` wrapping.
- Auth bypass: frontend mein `email.length > 0` condition ne kisi bhi email ko admin access diya demo mode mein. Fix: explicit credential pair matching.
- N+1 queries: dashboard 37 queries run karta tha (ek per day for trend). Fix: GROUP BY queries — 2 total.
- LangGraph graph har request pe recompile hota tha. Fix: startup pe cache.
- AsyncOpenAI client har call pe create hota tha. Fix: singleton.
- Circuit breaker mein asyncio.Lock nahi tha — race condition. Fix: Lock add kiya.

**Round 2 mein** aur refinements:
- Contractor ranking mein N+1 (2N queries) → 2 batched queries.
- importlib.import_module() per agent call pe → module-level import.
- Dead code remove: require_tenant_scope() never called anywhere.
- import sys inside async function → module top.

### Aaj Ka State (September 2025)

Aaj ASIP ek production-ready backbone hai ek real residential society ke liye. Backend fully functional hai — authentication, multi-tenancy, 7-agent AI pipeline, ML learning loop, RAG memory, sensor offline support, complaint lifecycle — sab kuch kaam karta hai.

Frontend ka most of dashboard live API se connected hai. Kuch pages abhi bhi mock data use karte hain — woh aage connect honge.

Kuch cheezein baaki hain: WebSocket real-time updates, rate limiting on sensor endpoints, notification retry queue, aur proper production deployment configuration.

**Is project ki sabse interesting cheez kya hai?**

Ye ek self-improving system hai. Jitna zyada incidents process honge, jitna zyada feedback aayega — utna zyada ML model accurate hoga, utna zyada correction factors refined honge, utna zyada contractors ka history build hoga. System time ke saath aur smart banta jaata hai — bina manually retraining ya reconfiguring ke.

Yahi ASIP ki asli "intelligence" hai.

---

*PROJECT_JANAMKUNDLI.md — Complete as of September 2025 (+ Deployment Phase: September 2026)*
*Backend: /Users/kratish/study/projects/ASIP/backend/*
*Frontend: /Users/kratish/study/projects/ASIP/frontend/*
*Development period: April 2025 – July 2025 (+ September 2025 audit + September 2026 deployment)*
*Repository: https://github.com/KRATISH07/ASIP*

---

## 26. Production Deployment Phase — September 2026

> **"Code likhna alag baat hai, deploy karna alag baat hai."**
> Is section mein woh poora journey hai jab hum ASIP ko pehli baar live internet pe laaye.

---

### 26.1 Deployment Platform Decision

**Challenge:** ASIP ka stack complex hai — FastAPI backend, Next.js frontend, PostgreSQL database (multi-tenant), ChromaDB vector DB. Sab free mein deploy karna tha.

**Options considered:**

| Platform | Pros | Cons | Decision |
|----------|------|------|----------|
| Railway | All-in-one | Requires payment for persistent deployment | ❌ Rejected |
| Render + Neon + Vercel | 100% free forever | 3 separate platforms | ✅ Chosen |
| Heroku | Familiar | Removed free tier | ❌ Rejected |
| Fly.io | Container-native | Complex setup | ❌ Rejected |

**Final stack:**
```
Frontend  →  Vercel       (Next.js, free forever, no sleep)
Backend   →  Render.com   (FastAPI, free tier, sleeps after 15 min)
Database  →  Neon.tech    (PostgreSQL serverless, free, no expiry)
AI Memory →  Skipped      (ChromaDB not deployed — rule-based fallback)
```

---

### 26.2 Files Created for Deployment

```
ASIP/
├── Dockerfile.backend          ← Root-context Dockerfile for Render
│                                  (copies from backend/ since Render
│                                   builds from repo root)
├── render.yaml                 ← Render blueprint (service config,
│                                   env vars, free plan declaration)
├── backend/
│   ├── Dockerfile              ← Updated: runs alembic before uvicorn
│   ├── railway.json            ← Railway config (kept for future use)
│   └── .railwayignore          ← Slim Docker context
└── frontend/
    ├── Dockerfile              ← Multi-stage Next.js production build
    ├── vercel.json             ← Vercel config (minimal — Next.js auto-detected)
    ├── railway.json            ← Railway config (kept for future use)
    └── next.config.ts          ← Added: output: "standalone" for Docker
```

**Key decisions in Dockerfile.backend:**
```dockerfile
# Run Alembic migrations THEN start server
# Target specific revision — avoids "multiple heads" error
CMD alembic upgrade 0000_create_all && alembic stamp heads && \
    uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

Why `${PORT:-8000}`? Render dynamically assigns a port via `$PORT` env var.
If not set (local dev), falls back to 8000.

---

### 26.3 CORS Update for Production

**Problem:** Frontend on `*.vercel.app` was blocked by backend CORS (only allowed `localhost:3000`).

**Fix in `main.py`:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", *_extra_origins],
    allow_origin_regex=r"https://(.*\.railway\.app|.*\.vercel\.app|.*\.onrender\.com)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Used `allow_origin_regex` instead of listing every possible Vercel subdomain — one regex covers all deployment URLs forever.

---

### 26.4 Deployment Bugs — All Found & Fixed

#### Bug 1: Alembic Multiple Heads Error
**Error:**
```
alembic.util.exc.CommandError: Multiple head revisions are present
```
**Root Cause:** We created a new `0000_create_all` migration with `down_revision=None` (a new branch root). The old migration chain also had its own root. Alembic found 2 heads and refused to run `upgrade head`.

**Fix:**
```bash
# Instead of: alembic upgrade head
# Do this:
alembic upgrade 0000_create_all && alembic stamp heads
```
`stamp heads` marks all existing revision chains as "already applied" so future `upgrade head` calls work normally.

**Lesson:** Never run `alembic upgrade head` on a fresh DB with multiple branches. Always target specific revision + stamp.

---

#### Bug 2: email-validator Missing
**Error:**
```
ImportError: email-validator is not installed, run `pip install email-validator`
```
**Root Cause:** Pydantic v2 requires `email-validator` as an **explicit** dependency when using `EmailStr` fields. It was not in `requirements.txt`.

**Fix:**
```
# requirements.txt
email-validator==2.2.0
```

**Lesson:** Pydantic v2 split many optional deps. Always check `pydantic[email]` extras and explicitly list them.

---

#### Bug 3: "Could Not Validate Credentials" on Login
**Error:** Every login returned 401 — "could not validate credentials"

**Root Cause:** The Neon database was empty. We ran migrations (table structure ✅) but **never seeded any users**. So `admin@asip.ai`, `resident1@asip.ai` etc. literally did not exist in the DB.

**Fix:** Wrote and ran a seed script locally against Neon:
```python
# Seeded 7 users + 1 tenant directly into production Neon DB
DEMO_USERS = [
    ("admin@asip.ai",       "admin123",    UserRole.admin),
    ("manager@asip.ai",     "manager123",  UserRole.manager),
    ("maintenance@asip.ai", "maint123",    UserRole.maintenance),
    ("resident1@asip.ai",   "password123", UserRole.resident),
    ("resident2@asip.ai",   "password123", UserRole.resident),
    ("gateway@asip.ai",     "password123", UserRole.sensor_gateway),
    ("contractor@asip.ai",  "password123", UserRole.contractor),
]
```

Also seeded default tenant: `slug="default"`, `schema_name="public"`.

**Lesson:** Migrations ≠ Seed data. Always have a separate seed script. Migrations create schema, seed data creates initial records.

---

#### Bug 4: passlib + modern bcrypt incompatibility (local Python 3.9)
**Error when running seed script locally:**
```
(trapped) error reading bcrypt version
AttributeError: module 'bcrypt' has no attribute '__about__'
ValueError: password cannot be longer than 72 bytes
```

**Root Cause:** System Python 3.9 had old `passlib` (1.7.4) which is incompatible with modern `bcrypt` (4.x). The bcrypt module's internal API changed.

**Fix:** Bypassed passlib entirely in the seed script, used `bcrypt` directly:
```python
import bcrypt
def hash_pw(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()
```

**Note:** This was only for the one-time seed script. The backend itself uses passlib normally (inside Docker with correct versions).

---

#### Bug 5: "No contractor candidates found" — Empty State
**Problem:** When clicking any incident in the frontend, the AI Contractor Candidate Evaluation section showed: *"No contractor candidates found matching specialization."* — a completely empty, unhelpful message.

**Root Cause 1 (UI):** No empty state was designed. Just a single `<p>` tag.
**Root Cause 2 (Data):** The contractors table was also empty — no contractors were in the database.

**Fix 1 (UI):** Replaced the bare text with a rich empty state UI:
- 🟡 Amber warning icon + clear explanation
- 3 actionable suggestion cards:
  - 👷 Add a Contractor → links to `/contractors`
  - 🔧 Set Specializations (info)
  - 📊 Seed Demo Contractors (info)
- 🟣 Violet info pill: explains Thompson Sampling will activate once contractors exist

**Fix 2 (Data):** Seeded 5 demo contractors into Neon:

| Contractor | Specializations | Rating | Jobs Done |
|-----------|----------------|--------|-----------|
| Sharma Plumbing & Water Works | water, pump, pipeline, plumbing | ⭐ 4.7 | 142 |
| PowerTech Electrical Solutions | electrical, power, generator | ⭐ 4.5 | 98 |
| RapidFix Civil & Structural | civil, structural, waterproofing | ⭐ 4.3 | 67 |
| CoolAir HVAC Services | hvac, ac, ventilation, cooling | ⭐ 4.6 | 55 |
| SecurePro Security & CCTV | security, cctv, access_control | ⭐ 4.4 | 43 |

Now water/pump incidents show Sharma Plumbing ranked #1 by Thompson Sampling.
Power incidents show PowerTech ranked #1. AI ranking actually works end-to-end.

---

#### Bug 6: Vercel "Not Authorized" on redeploy
**Error:**
```
Error: Not authorized
Contact Support: https://vercel.link/help
```
**Root Cause:** Using `vercel --yes` with conflicting flags caused the CLI to lose scope.
**Fix:** Use `vercel deploy --prod` (explicit deploy subcommand) instead of `vercel --yes --prod`.

---

### 26.5 Database Seeding Architecture

**Decision:** Seed data is NOT in migrations. Why?

```
migrations/   → Schema only (tables, columns, indexes, constraints)
seed data     → Separate script, run manually or as startup hook
```

**Reason:** Migrations are idempotent, versioned, and reversible.
Seed data is environment-specific (prod vs dev vs test gets different data).
Mixing them causes "INSERT fails because row already exists" errors on subsequent migration runs.

**How we seed on Render:** The `CMD` in Dockerfile runs migrations but NOT seed data.
Seed data was run once from local machine using the connection string.
For new environments, developer runs `python3 seed.py` once.

---

### 26.6 Live Deployment URLs

| Service | URL | Notes |
|---------|-----|-------|
| **Frontend (Vercel)** | https://frontend-pi-seven-20.vercel.app | Always live, no sleep |
| **Backend (Render)** | https://asip-fgin.onrender.com | Sleeps after 15 min idle |
| **Swagger Docs** | https://asip-fgin.onrender.com/docs | Full API documentation |
| **Health Check** | https://asip-fgin.onrender.com/health | Returns `{"status":"ok"}` |
| **GitHub Repo** | https://github.com/KRATISH07/ASIP | Source of truth |
| **Neon Dashboard** | https://console.neon.tech | Database management |

**Free tier limitations:**
- Render backend sleeps after 15 min of no traffic → first request after sleep takes ~30s to wake up
- Neon pauses compute after 5 min idle → first DB query after pause has ~1s cold start
- Vercel hobby: 100GB bandwidth/month, unlimited deploys

---

### 26.7 Auto-Deploy Setup

Both Render and Vercel auto-deploy on every push to `main`:

```
git push origin main
    ↓
GitHub webhook fires
    ↓
Render pulls new code → Docker build → alembic migrate → uvicorn start
Vercel pulls new code → npm build → Next.js standalone → node server.js
```

No manual deploy step needed after initial setup.
Every `git push` = new production deployment.

---

### 26.8 Private Credentials File

Created `ASIP_CREDENTIALS.md` at project root — gitignored, never pushed to GitHub.
Contains all deployment URLs, passwords, API keys, connection strings in one place.

Added to `.gitignore`:
```
# Credentials file — NEVER commit this
ASIP_CREDENTIALS.md
```

---

### 26.9 Commit History — Deployment Phase

| Commit | Message | What it did |
|--------|---------|-------------|
| `f7ee3e1` | docs: add PROJECT_JANAMKUNDLI.md | 2275-line complete engineering history |
| `062d659` | deploy: add Railway deployment config | railway.json, Dockerfiles, CORS update |
| `dd2b301` | deploy: free-tier setup (Vercel+Render+Neon) | render.yaml, vercel.json, Dockerfile.backend |
| `34349f9` | deploy: add clean initial migration | 0000_create_all_tables.py, fix vercel.json |
| `5dd66df` | fix(deploy): fix Alembic multiple-heads error | CMD: upgrade 0000_create_all && stamp heads |
| `515d71a` | fix(deploy): add email-validator | requirements.txt += email-validator==2.2.0 |
| `a115ab7` | chore: gitignore ASIP_CREDENTIALS.md | .gitignore += private credentials file |
| `be5c82c` | fix(ui): replace empty contractor state | Rich suggestions UI + 5 contractors seeded |

---

### 26.10 Key Lessons Learned in Deployment

1. **Migrations ≠ Seed data.** Always separate them. Don't put INSERT statements in migration files.

2. **Multiple Alembic heads are silent in dev, catastrophic in prod.** Always check `alembic heads` before deploying.

3. **CORS regex > static origins list.** `allow_origin_regex=r"https://.*\.vercel\.app"` covers all future preview deployments automatically.

4. **passlib + modern bcrypt = incompatible on old Python.** Use bcrypt directly for scripts, or use Docker (which has the right versions).

5. **Empty states are UX debt.** Every list/section needs a designed empty state — not just a `<p>` tag. Users don't know what to do when they see nothing.

6. **Free tier is enough for demos and small societies.** Render free + Neon free + Vercel free = production-grade system at ₹0/month.

7. **The Render `PORT` env var is mandatory.** Don't hardcode `--port 8000`. Use `${PORT:-8000}` so Render can assign its own port.

8. **`vercel deploy --prod` != `vercel --prod --yes`.** The `--yes` flag in some CLI versions causes auth scope issues. Use explicit subcommand.

---

*Section 26 added: September 26, 2026 — Deployment Phase complete*

