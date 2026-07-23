# Multi-Tenancy Schema Design

> **Status**: Design document (not yet implemented)  
> **Date**: 2026-06-27  
> **Scope**: How ASIP would extend its schema to serve multiple housing societies
> (tenants) from a single deployment.

---

## 1. What is "Multi-Tenancy" in ASIP's Context?

ASIP currently serves a single housing society ("Greenfield Heights") from
one database schema. Multi-tenancy means a single ASIP deployment serves
**N distinct housing societies** — each with their own:

- Towers, apartments, residents
- Contractors and pricing agreements
- Incident history and ML models
- Notification channels and SLA thresholds

Data from Society A must never be visible to Society B.

---

## 2. Isolation Strategies Evaluated

Three canonical approaches exist. The right choice depends on the number of
tenants, their size, and their compliance requirements.

### Strategy 1 — Separate Database per Tenant

```
asip_society_a  (PostgreSQL DB)
asip_society_b  (PostgreSQL DB)
asip_society_c  (PostgreSQL DB)
```

**Pros**:
- Strongest isolation. A misconfigured query in Society A cannot touch Society B.
- Independent backup, restore, and migration per tenant.
- Simpler to offer data residency guarantees (each DB on a different server).

**Cons**:
- N × connection pool overhead. At 100 tenants = 100 connection pools.
- Schema migration runs N times (Alembic must target each DB).
- Operational complexity grows linearly with tenant count.

**When to use**: Compliance-heavy environments (healthcare, government).
Enterprise clients paying for dedicated infra.

---

### Strategy 2 — Separate Schema per Tenant (Recommended)

```
PostgreSQL: asip_db
├── schema: society_a   (tables: incidents, towers, residents, ...)
├── schema: society_b
└── schema: public      (shared: users, tenant_registry)
```

**Pros**:
- Strong logical isolation within a single database.
- One connection pool, shared across all tenants.
- Alembic can run `SET search_path = society_a` before migrations — same
  migration script applies to all schemas.
- Cross-tenant analytics queries possible when authorised (e.g., platform
  operations dashboards).

**Cons**:
- Requires PostgreSQL (MySQL does not support schema-level isolation cleanly).
- Schema-per-tenant in Alembic requires a custom `env.py` that iterates over
  all tenant schemas.
- Connection string must inject `search_path` on each session.

**When to use**: SaaS platforms with 10–500 tenants, all on the same compliance
tier.

**This is the recommended approach for ASIP.**

---

### Strategy 3 — Row-Level Tenancy (Discriminator Column)

```sql
-- Every table gains a tenant_id column
ALTER TABLE incidents ADD COLUMN tenant_id UUID NOT NULL REFERENCES tenants(id);
CREATE INDEX ON incidents (tenant_id);
```

**Pros**:
- Simplest to implement. No schema changes beyond adding `tenant_id`.
- One migration, one schema, one connection pool.
- Cross-tenant aggregation is trivial (admin can query without switching context).

**Cons**:
- Highest risk of data leakage. A missing `WHERE tenant_id = ?` in any query
  exposes all tenants' data.
- Row-Level Security (RLS) in PostgreSQL mitigates this but adds complexity.
- Full-table scans become costly as tenant count grows (indexes on `tenant_id`
  help but don't eliminate).
- Regulatory compliance harder to demonstrate (data co-mingled at row level).

**When to use**: Internal tools with a small, trusted user base. Not recommended
for production SaaS where tenants are distinct organisations.

---

## 3. Recommended Implementation: Schema-per-Tenant

### 3.1 Tenant Registry (Public Schema)

```sql
-- public.tenants
CREATE TABLE tenants (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug        TEXT UNIQUE NOT NULL,  -- e.g. 'greenfield-heights'
    name        TEXT NOT NULL,
    schema_name TEXT UNIQUE NOT NULL,  -- e.g. 'society_greenfield'
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_active   BOOLEAN NOT NULL DEFAULT true
);
```

The `slug` is used in API URL prefixes (`/api/v1/{slug}/incidents`).

### 3.2 Schema Creation on Tenant Onboarding

```python
# app/services/tenant_service.py

async def provision_tenant(session: AsyncSession, name: str, slug: str) -> Tenant:
    """
    Creates a new PostgreSQL schema and runs all Alembic migrations against it.
    Called once during tenant onboarding.
    """
    schema_name = f"society_{slug.replace('-', '_')}"

    # 1. Create schema
    await session.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))

    # 2. Run Alembic migrations against the new schema
    _run_alembic_for_schema(schema_name)

    # 3. Register in public.tenants
    tenant = Tenant(slug=slug, name=name, schema_name=schema_name)
    session.add(tenant)
    await session.commit()
    return tenant


def _run_alembic_for_schema(schema_name: str):
    """Invoke alembic upgrade head with search_path set to the tenant schema."""
    import subprocess
    env = {**os.environ, "ALEMBIC_SCHEMA": schema_name}
    subprocess.run(
        ["alembic", "upgrade", "head"],
        env=env,
        check=True,
    )
```

### 3.3 Alembic `env.py` Changes

```python
# alembic/env.py (additions)

schema_name = os.environ.get("ALEMBIC_SCHEMA", "public")

def run_migrations_online():
    connectable = engine_from_config(...)
    with connectable.connect() as connection:
        # Set search_path so all DDL targets the correct schema
        connection.execute(text(f'SET search_path TO "{schema_name}"'))
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
```

### 3.4 Session Middleware — Injecting `search_path`

Every database session for a tenant request must set `search_path` before
any query executes.

```python
# app/core/tenant_middleware.py

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract tenant slug from URL path or JWT claim
        slug = _extract_slug(request)
        tenant = await _resolve_tenant(slug)  # cache in Redis

        # Store on request state for downstream use
        request.state.tenant = tenant
        return await call_next(request)


# app/dependencies.py — tenant-aware session
async def get_tenant_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    schema = request.state.tenant.schema_name
    async with AsyncSessionLocal() as session:
        # Inject search_path for this session
        await session.execute(text(f'SET LOCAL search_path TO "{schema}"'))
        yield session
```

### 3.5 API URL Structure

```
/api/v1/greenfield-heights/incidents       → society_greenfield schema
/api/v1/riverside-towers/incidents         → society_riverside schema
/api/v1/admin/tenants                      → public schema (platform admin only)
```

JWT tokens include a `tenant_id` claim. The middleware validates that the
token's `tenant_id` matches the URL slug (prevents cross-tenant impersonation).

---

## 4. ML Model Isolation

Each tenant's ML pipeline must train on its own incident history only.

```python
# app/ml/pipeline.py — tenant-aware training

class MLPipeline:
    def __init__(self, tenant_id: UUID):
        self.tenant_id = tenant_id

    async def train(self, session: AsyncSession):
        # All queries automatically scoped to tenant schema via search_path
        incidents = await self._load_incidents(session)
        ...
```

Per-tenant model artifacts stored at:
```
models/
├── society_greenfield/
│   └── impact_predictor_v3.pkl
└── society_riverside/
    └── impact_predictor_v1.pkl
```

---

## 5. LLM Context Isolation

Incident memory (ChromaDB vector store) must be scoped per tenant:

```python
# app/rag/memory.py — tenant-aware collection naming

def get_collection_name(tenant_slug: str) -> str:
    return f"asip_incidents_{tenant_slug}"
    # e.g. "asip_incidents_greenfield_heights"
```

Each tenant gets a dedicated ChromaDB collection. No cross-tenant embedding
similarity is possible by construction.

---

## 6. Migration Playbook for Adding Multi-Tenancy to ASIP

| Step | Action | Risk |
|------|--------|------|
| 1 | Add `public.tenants` table (new migration) | Zero — additive |
| 2 | Update `alembic/env.py` to support `ALEMBIC_SCHEMA` env var | Low — affects migration runner only |
| 3 | Migrate existing data into a `society_default` schema | Medium — data migration, must be reversible |
| 4 | Add `TenantMiddleware` + `get_tenant_session` dependency | Medium — all route handlers must adopt new session dependency |
| 5 | Update ChromaDB to per-tenant collections | Low — additive |
| 6 | Update ML pipeline to per-tenant model storage | Low — additive |
| 7 | Add tenant admin API (`POST /admin/tenants`) | Low — new endpoints |

**Total estimated effort**: 3–5 engineering days for an experienced team already
familiar with the ASIP codebase.

---

## 7. Decision Summary

| Criterion | Separate DB | Schema-per-Tenant ✅ | Row-Level |
|-----------|-------------|----------------------|-----------|
| Isolation strength | ★★★ | ★★★ | ★★ |
| Ops complexity | ★★★ | ★★ | ★ |
| Migration difficulty | ★★★ | ★★ | ★ |
| Cross-tenant analytics | ✗ | Possible | ✓ |
| Recommended for ASIP | Only for compliance | **Yes** | No |

Schema-per-tenant provides the right balance of isolation, operational
simplicity, and scalability for a SaaS housing management platform at
ASIP's target scale (10–500 societies).
