from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.tenant_context import set_tenant_schema, reset_tenant_schema
from app.core.logging import get_logger
from app.db.session import AsyncSessionFactory
from app.db.models.tenant import Tenant
from sqlalchemy import select

logger = get_logger("tenant_middleware")

# Thread-safe in-memory cache to avoid DB round-trips on every HTTP request
_TENANT_CACHE = {}


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware that intercepts incoming HTTP requests, extracts the target tenant
    slug, resolves the corresponding PostgreSQL schema name, and binds it to the
    current asynchronous execution context using ContextVars.
    """
    async def dispatch(self, request: Request, call_next):
        tenant_slug = request.headers.get("X-Tenant-Slug") or "default"
        
        schema_name = "public"
        if tenant_slug != "public":
            if tenant_slug in _TENANT_CACHE:
                schema_name = _TENANT_CACHE[tenant_slug]
            else:
                try:
                    async with AsyncSessionFactory() as db:
                        stmt = select(Tenant).where(Tenant.slug == tenant_slug).limit(1)
                        res = await db.execute(stmt)
                        tenant = res.scalar_one_or_none()
                        
                        if tenant:
                            schema_name = tenant.schema_name
                            _TENANT_CACHE[tenant_slug] = schema_name
                        elif tenant_slug == "default":
                            # Default fallback if tenant registry is not yet populated
                            schema_name = "society_default"
                        else:
                            return Response(
                                content=f"Tenant '{tenant_slug}' not found",
                                status_code=404
                            )
                except Exception as e:
                    # Graceful fallback during Alembic migration runs
                    if tenant_slug == "default":
                        schema_name = "society_default"
                    else:
                        logger.error("Failed to resolve tenant schema from database", error=str(e))
                        return Response(
                            content="Database schema initialization in progress",
                            status_code=503
                        )
                        
        token = set_tenant_schema(schema_name)
        try:
            response = await call_next(request)
            return response
        finally:
            reset_tenant_schema(token)
