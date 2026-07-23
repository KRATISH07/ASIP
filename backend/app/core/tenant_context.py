import contextvars
from typing import Optional

# ContextVar storing the active tenant's PostgreSQL schema name
_TENANT_SCHEMA: contextvars.ContextVar[str] = contextvars.ContextVar(
    "tenant_schema", default="public"
)


def get_tenant_schema() -> str:
    """Retrieve the currently active tenant's database schema name."""
    return _TENANT_SCHEMA.get()


def set_tenant_schema(schema_name: str) -> contextvars.Token[str]:
    """Bind the active tenant's database schema name to the current context."""
    return _TENANT_SCHEMA.set(schema_name)


def reset_tenant_schema(token: contextvars.Token[str]) -> None:
    """Reset the tenant schema context back to the state before set_tenant_schema."""
    _TENANT_SCHEMA.reset(token)
