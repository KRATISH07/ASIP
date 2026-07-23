import pytest
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.tenant_context import get_tenant_schema, set_tenant_schema, reset_tenant_schema
from app.core.tenant_middleware import TenantMiddleware
from app.services.tenant_service import provision_tenant


@pytest.mark.asyncio
async def test_tenant_context_management():
    """Verify that tenant ContextVar bindings are scoped and reversible."""
    assert get_tenant_schema() == "public"
    token = set_tenant_schema("society_riverside")
    assert get_tenant_schema() == "society_riverside"
    reset_tenant_schema(token)
    assert get_tenant_schema() == "public"


@pytest.mark.asyncio
async def test_tenant_middleware_default():
    """Verify that TenantMiddleware falls back to default tenant when headers are absent."""
    mock_request = MagicMock()
    mock_request.headers = {}

    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_res)

    class AsyncSessionCM:
        async def __aenter__(self):
            return mock_db
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    async def call_next(req):
        # Within request scope, active schema should fall back to default
        assert get_tenant_schema() == "society_default"
        return "response"

    with patch("app.core.tenant_middleware.AsyncSessionFactory", return_value=AsyncSessionCM()):
        middleware = TenantMiddleware(None)
        res = await middleware.dispatch(mock_request, call_next)
        assert res == "response"

    # Beyond request scope, context must be public
    assert get_tenant_schema() == "public"


@pytest.mark.asyncio
async def test_tenant_middleware_custom_header():
    """Verify that TenantMiddleware extracts custom header and queries database."""
    mock_request = MagicMock()
    mock_request.headers = {"X-Tenant-Slug": "riverside"}

    # Mock Tenant record return
    mock_tenant = MagicMock()
    mock_tenant.schema_name = "society_riverside"

    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = mock_tenant
    mock_db.execute = AsyncMock(return_value=mock_res)

    class AsyncSessionCM:
        async def __aenter__(self):
            return mock_db
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    async def call_next(req):
        assert get_tenant_schema() == "society_riverside"
        return "response"

    with patch("app.core.tenant_middleware.AsyncSessionFactory", return_value=AsyncSessionCM()):
        # Clear cache first to force DB query
        from app.core.tenant_middleware import _TENANT_CACHE
        _TENANT_CACHE.clear()

        middleware = TenantMiddleware(None)
        res = await middleware.dispatch(mock_request, call_next)
        assert res == "response"


@pytest.mark.asyncio
async def test_tenant_db_session_search_path():
    """Verify that database session event listener sets search_path dynamically."""
    from app.db.session import set_search_path_listener

    mock_connection = MagicMock()

    token = set_tenant_schema("society_lakeside")
    try:
        set_search_path_listener(None, None, mock_connection)
        mock_connection.exec_driver_sql.assert_called_once_with('SET search_path TO "society_lakeside", public')
    finally:
        reset_tenant_schema(token)
