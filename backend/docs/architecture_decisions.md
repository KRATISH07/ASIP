# Architecture Decision Records — ASIP

> **Status**: Active  
> **Last Updated**: 2026-06-27  
> **Authors**: Engineering Team

This document records the significant architectural decisions made during the
design and evolution of the **AI Society Intelligence Platform (ASIP)**.

Each ADR follows the standard format:
- **Context** — the forces and constraints at the time of the decision
- **Decision** — what was chosen
- **Alternatives Considered** — what was evaluated and rejected
- **Consequences** — trade-offs accepted

---

## ADR-001: Workflow Orchestration — LangGraph

**Date**: 2024-Q4  
**Status**: ✅ Accepted

### Context

ASIP requires a multi-agent pipeline in which several specialist agents
(infrastructure diagnosis, impact analysis, contractor selection, notifications,
autonomous decision) must run in a defined sequence, share state, and recover
from partial failures.

Requirements:
1. Typed, shared state across all agents
2. Conditional routing (different incident types run different agent subsets)
3. Checkpointing — if the pipeline fails at step 4 of 7, work from steps 1–3
   must not be lost
4. Future-proof for adding new agents without changing existing ones

### Decision

Use **LangGraph** (`langgraph.graph.StateGraph`) as the workflow orchestrator.

```
monitoring_agent
     │
supervisor_decider  ← config-driven routing (routing_config.py)
     │
[infrastructure_agent, impact_agent, contractor_agent,
 communication_agent, decision_agent]  ← selected dynamically
     │
supervisor_agent   ← aggregation + LLM synthesis
     │
  __end__
```

The compiled graph is cached via `lru_cache(maxsize=1)` to amortise the
O(topology) compilation cost across all HTTP requests.

Checkpointing uses `MemorySaver` (in-process, no extra infra). The upgrade
path to `AsyncPostgresSaver` is one import swap using the existing PostgreSQL
instance.

### Alternatives Considered

| Alternative | Reason Rejected |
|-------------|----------------|
| **Celery + Redis** | Heavyweight infra (Redis broker, worker pool). Adds ops surface. No native LLM primitives. |
| **Prefect / Airflow** | Designed for data engineering DAGs, not low-latency LLM pipelines. Cold start overhead. |
| **Raw async Python** (manual orchestration) | Requires hand-rolling state management, retry logic, and routing. High maintenance burden. |
| **LangChain LCEL** (chains only) | No native conditional routing or inter-agent state. Cannot model "supervisor selects agents" pattern. |

### Consequences

**Accepted trade-offs**:
- LangGraph is relatively new (v0.2 API); we accept the risk of minor API
  changes between minor versions.
- `MemorySaver` checkpoints are lost on process restart. Production upgrade to
  `AsyncPostgresSaver` is planned for V7.

**Benefits realised**:
- Adding a new agent requires one line in `routing_config.py` and one node
  registration in `graph.py`. Zero changes to existing agents (Open/Closed).
- State typing via `ASIPState` (TypedDict) catches key-name errors at
  development time, not in production.

---

## ADR-002: Structured LLM Outputs — Instructor

**Date**: 2025-Q1  
**Status**: ✅ Accepted

### Context

All LLM calls in ASIP must return structured data (`InfrastructureDiagnosis`,
`SupervisorReportSchema`, etc.). Early implementation used prompt engineering
alone with `JsonOutputParser`, which produced three failure modes:

1. **Hallucinated JSON keys** — LLM omits required fields silently.
2. **Out-of-range values** — `confidence: 1.5` passes JSON parsing but violates
   domain constraints.
3. **Inconsistent retry logic** — each agent had its own try/except block.

### Decision

Adopt **Instructor** (`pip install instructor`) for all structured LLM outputs.

Architecture:

```python
# app/core/llm/fallback.py — central structured output path
client = instructor.from_openai(openai_client, mode=instructor.Mode.JSON)
result: MySchema = await client.chat.completions.create(
    model=model_name,
    messages=[...],
    response_model=MySchema,   # Pydantic model — Instructor handles retry
)
```

Instructor wraps the underlying LLM client and automatically:
1. Appends the JSON schema to the system prompt
2. Validates the response against the Pydantic model
3. Retries up to `max_retries=3` with the validation error as feedback

### Fallback Hierarchy

```
Instructor (primary)
    │ ValidationError after 3 retries
    ▼
invoke_chain (raw LangChain JSON parser)
    │ Exception
    ▼
Rule-based fallback dict (hardcoded, always succeeds)
```

The rule-based fallback is keyed by `agent_type` in `_RULE_BASED_FALLBACKS`.
This guarantees the pipeline always produces a usable (if degraded) output.

### Alternatives Considered

| Alternative | Reason Rejected |
|-------------|----------------|
| **Raw `JsonOutputParser`** | No automatic validation or retry. Silent field omissions are undetectable. |
| **Pydantic validators post-hoc** | Validation happens after parsing; requires manual retry logic. Code duplication per agent. |
| **Outlines / LMQL** | Grammar-constrained decoding requires model-level changes. Not compatible with OpenAI/Gemini APIs. |
| **Function Calling (OpenAI)** | OpenAI-specific. ASIP must support both OpenAI and Gemini. Instructor abstracts this. |

### Consequences

**Accepted trade-offs**:
- Instructor adds ~1 extra API call per failure (retry with validation error).
  In practice, well-engineered prompts fail < 2% of the time.
- Test suite requires an `is_mock` bypass check in `invoke_with_fallback` to
  avoid Instructor patching `AsyncMock` objects during unit tests.

**Benefits realised**:
- All 6 structured output schemas (`InfrastructureDiagnosis`, `ContractorSelection`,
  `NotificationDraft`, `NotificationListSchema`, `SupervisorReportSchema`,
  `EvaluationScores`) are validated at the boundary.
- Zero raw JSON parsing in the codebase.

---

## ADR-003: Saga Pattern for Workflow Failure Recovery

**Date**: 2025-Q2  
**Status**: ✅ Accepted

### Context

When a multi-step incident workflow fails partway through (e.g., contractor
assignment times out at step 5 of 7), two options exist:

1. **Abandon** — fail the whole workflow and require manual re-trigger.
2. **Compensate** — undo completed steps to return to a consistent state, then
   retry or escalate.

ASIP incidents have time-sensitive SLA constraints. Silent abandonment violates
the SLA and leaves infrastructure in an uncertain state.

### Decision

Implement the **Saga pattern** with forward retry and backward compensation.

```
WorkflowRun (DB record)
  ├── status: pending | running | completed | failed | compensating
  ├── current_step
  ├── completed_steps: []
  ├── retry_count (max 3)
  └── last_error
```

**Forward path** (retry):
- If a step fails, increment `retry_count`.
- If `retry_count < 3`, re-execute from the failed step using the LangGraph
  checkpoint (no re-running completed steps).
- On the 3rd failure, trigger backward compensation.

**Backward compensation**:
- Execute compensating transactions in reverse order of completed steps.
- Final compensation: escalate to manual review queue with full context.

```python
# app/services/workflow_service.py
class WorkflowService:
    async def execute_with_saga(self, incident_id, workflow_fn):
        ...
    async def _compensate(self, workflow_run):
        # reverse-order compensating transactions
        ...
```

### Alternatives Considered

| Alternative | Reason Rejected |
|-------------|----------------|
| **2PC (Two-Phase Commit)** | Requires all participants to implement a coordinator protocol. Incompatible with LLM agents (non-deterministic). |
| **Event sourcing (full)** | Over-engineered for current scale. Saga covers 95% of failure modes. |
| **Simple retry without compensation** | Idempotency not guaranteed for all steps (e.g., contractor dispatch would fire twice). |
| **Dead letter queue (Celery/SQS)** | Adds external broker dependency. Increases ops surface without proportional benefit at current scale. |

### Consequences

**Accepted trade-offs**:
- Saga requires all compensating operations to be idempotent. This was
  enforced by design (all DB writes use `upsert` patterns).
- `WorkflowRun` table adds one DB write per incident step transition.

**Benefits realised**:
- `reconcile_failed_runs` (scheduled task) can recover stalled workflows on
  restart — no data loss.
- Manual review escalation creates an auditable trail for every failure.

---

## ADR-004: Model Routing by Task Complexity

**Date**: 2025-Q3  
**Status**: ✅ Accepted

### Context

Early ASIP used a single model (`gpt-4o` / `gemini-1.5-pro`) for all LLM tasks.
This created two problems:

1. **Cost**: Simple tasks (drafting an SMS notification, extracting a JSON field)
   cost the same as complex tasks (root cause analysis, multi-source report
   synthesis).
2. **Latency**: Notification drafting does not need GPT-4's reasoning depth.
   Routing it to a faster model reduces p95 by ~800ms.

### Decision

Route to the appropriate model based on `task_type` in `get_llm()`.

```python
# app/agents/llm.py
@lru_cache(maxsize=32)
def get_llm(task_type: str = "general", temperature: float = 0.1):
    model_map = {
        "extraction":   "gpt-4o-mini",    # ~10x cheaper, ~2x faster
        "notification": "gpt-4o-mini",
        "diagnosis":    "gpt-4o",          # requires deep reasoning
        "supervisor":   "gpt-4o",          # multi-source synthesis
    }
```

The same routing table exists for Google Gemini (`gemini-1.5-flash` vs
`gemini-1.5-pro`).

**LLM-as-judge** (ADR-005) also uses the cheap model (`extraction` tier) since
rubric scoring is a consistency task, not a reasoning task.

### Cost Model

| Task | Model | Cost/1K tokens | Notes |
|------|-------|----------------|-------|
| extraction | gpt-4o-mini | $0.00015 | JSON field parsing |
| notification | gpt-4o-mini | $0.00015 | SMS/email drafts |
| diagnosis | gpt-4o | $0.0025 | Root cause analysis |
| supervisor | gpt-4o | $0.0025 | Report synthesis |

Estimated per-incident cost: **$0.03** (down from $0.08 with uniform gpt-4o).

### Alternatives Considered

| Alternative | Reason Rejected |
|-------------|----------------|
| **Single model for all tasks** | 2.5x higher cost, unnecessary latency on simple tasks. |
| **Dynamic routing via embedding similarity** | Over-engineering. Task types are known at call-site. Static map is simpler and auditable. |
| **Fine-tuned local model for extraction** | Ops burden (GPU infra, model serving). Premature optimisation at current scale. |

### Consequences

**Accepted trade-offs**:
- `lru_cache(maxsize=32)` caches LLM client instances by `(task_type, temperature)`.
  Cache invalidation requires process restart (acceptable).
- Routing table must be updated when a new task type is introduced.

**Benefits realised**:
- ~62% cost reduction on notification and extraction tasks.
- p95 latency for notification drafts reduced from ~2.1s to ~0.9s.

---

## ADR-005: LLM-as-Judge for Prompt Quality Evaluation

**Date**: 2025-Q4  
**Status**: ✅ Accepted

### Context

Without automated evaluation, the only quality signal for LLM-generated
incident reports is human review — which does not scale and introduces
significant lag between prompt regressions and detection.

Required:
1. Automated, consistent quality scoring for every supervisor report.
2. Score dimensions that align with operational requirements (not just "is it
   valid JSON?").
3. Zero latency impact on the main incident workflow.
4. Score persistence for trend analysis and regression detection.

### Decision

Implement **LLM-as-judge**: a cheaper model (`gpt-4o-mini`) evaluates the
output of a more expensive model (`gpt-4o`) on a 4-dimension rubric.

```python
# app/evaluation/judge.py
RUBRIC = {
    "root_cause_specificity": "1=vague, 5=specific technical cause",
    "action_plan_completeness": "1=missing, 5=numbered actionable steps",
    "priority_correctness": "1=clearly wrong, 5=matches incident severity",
    "factual_consistency": "1=hallucinations, 5=fully grounded",
}
```

The judge call is wrapped with Instructor (`EvaluationScores` schema) to
prevent the evaluator itself from returning malformed scores.

The judge runs as `asyncio.create_task` — **fire-and-forget** — inside
`supervisor_agent`. It never blocks the main workflow.

Flagging: any dimension score `< 3` → `flagged=True` → human review queue.

Persistence: scores stored in `evaluation_results` (PostgreSQL), indexed by
`incident_id` and `flagged`.

### Alternatives Considered

| Alternative | Reason Rejected |
|-------------|----------------|
| **Human review only** | Does not scale. Lag between regression and detection. |
| **Rule-based heuristics** (regex, keyword counts) | Cannot detect semantic failures (plausible-sounding hallucinations). |
| **Reference-free embedding similarity** | No ground truth for incident reports. Cosine similarity to "good reports" requires curated corpus. |
| **Same model self-evaluation** | Known to exhibit self-serving bias — models rate their own outputs higher than external evaluators do. |
| **Synchronous judge call** | Adds ~600ms to every incident response. Unacceptable for SLA compliance. |

### Consequences

**Accepted trade-offs**:
- Sentinel result (score=1, flagged=True) returned when judge fails. This
  appears as a false positive in the flagged queue — acceptable vs. silently
  dropping evaluation data.
- Judge uses OpenAI Async API directly (bypasses the LangChain wrapper) to
  keep the evaluation path independent of the main agent infrastructure.

**Benefits realised**:
- Every report is automatically scored within 2 seconds of generation.
- Prompt regressions detectable within one deployment cycle (vs. days with
  human review).
- `flagged` index enables ops dashboard: "show me all low-quality reports from
  the past 7 days."

---

## ADR-006: Database Schema — SQLAlchemy Async + Alembic

**Date**: 2024-Q3  
**Status**: ✅ Accepted

### Context

ASIP is a FastAPI application with async request handlers. All database I/O
must be non-blocking to avoid starving the event loop. Schema evolution must
be traceable and reversible.

### Decision

Use **SQLAlchemy 2.x async** with `asyncpg` driver and **Alembic** for
schema migrations.

```python
# app/db/session.py
engine = create_async_engine(settings.database_url, pool_size=10)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
```

All migrations live in `alembic/versions/`. The `Base.metadata` in
`app/db/base.py` is the single source of truth — Alembic's `autogenerate`
targets it via `app/db/models/__init__.py` (all models imported here).

**Non-negotiable rule**: never bypass Alembic. No `Base.metadata.create_all()`
in application startup. Schema changes must go through versioned migrations.

### Alternatives Considered

| Alternative | Reason Rejected |
|-------------|----------------|
| **Tortoise ORM** | Smaller ecosystem. Poor integration with existing SQLAlchemy tooling. |
| **Prisma (Python client)** | Immature Python client. Schema-first approach conflicts with code-first model definitions. |
| **Synchronous SQLAlchemy** | Blocks the event loop under concurrent requests. Unacceptable for async FastAPI. |
| **Raw `asyncpg`** | No ORM = hand-written SQL everywhere. Type safety and migration story are poor. |

### Consequences

**Accepted trade-offs**:
- `expire_on_commit=False` is required for async sessions (objects accessed
  after commit would trigger lazy-load, illegal in async context).
- Unit tests use in-memory SQLite with a singleton engine reset between tests
  to prevent DB leakage.

**Benefits realised**:
- Schema evolution is fully reversible (`alembic downgrade -1`).
- All models are discoverable by Alembic via a single `__init__.py` import.
- Type-safe ORM queries with IDE autocompletion.

---

## Revision History

| ADR | Version | Date | Change |
|-----|---------|------|--------|
| ADR-001 | 1.0 | 2024-Q4 | Initial — LangGraph adoption |
| ADR-001 | 1.1 | 2025-Q2 | Added routing_config.py (Open/Closed fix) |
| ADR-002 | 1.0 | 2025-Q1 | Initial — Instructor adoption |
| ADR-003 | 1.0 | 2025-Q2 | Initial — Saga pattern |
| ADR-004 | 1.0 | 2025-Q3 | Initial — Model routing |
| ADR-005 | 1.0 | 2025-Q4 | Initial — LLM-as-judge |
| ADR-006 | 1.0 | 2024-Q3 | Initial — SQLAlchemy async + Alembic |
