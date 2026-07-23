import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.db.models.user import User, UserRole
from app.dependencies import require_roles, require_admin, require_manager_or_above


@pytest.mark.asyncio
async def test_require_roles_factory_success():
    """Verify that require_roles factory allows correct role to pass."""
    current_user = User(email="test@asip.ai", role=UserRole.resident)

    # Dependency check for resident
    dependency = require_roles(UserRole.resident, UserRole.admin)
    resolved_user = await dependency.dependency(current_user)
    assert resolved_user == current_user


@pytest.mark.asyncio
async def test_require_roles_factory_forbidden():
    """Verify that require_roles factory raises 403 for forbidden roles."""
    current_user = User(email="test@asip.ai", role=UserRole.resident)

    # Dependency check for manager / admin
    dependency = require_roles(UserRole.manager, UserRole.admin)
    with pytest.raises(HTTPException) as exc:
        await dependency.dependency(current_user)
    assert exc.value.status_code == 403
    assert "Access denied" in exc.value.detail


@pytest.mark.asyncio
async def test_require_admin_success():
    """Verify that require_admin allows admin role."""
    current_user = User(email="admin@asip.ai", role=UserRole.admin)
    resolved = await require_admin(current_user)
    assert resolved == current_user


@pytest.mark.asyncio
async def test_require_admin_forbidden():
    """Verify that require_admin raises 403 for non-admins."""
    current_user = User(email="manager@asip.ai", role=UserRole.manager)
    with pytest.raises(HTTPException) as exc:
        await require_admin(current_user)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_require_manager_or_above_success():
    """Verify require_manager_or_above allows admin and manager roles."""
    admin_user = User(email="admin@asip.ai", role=UserRole.admin)
    manager_user = User(email="manager@asip.ai", role=UserRole.manager)

    assert await require_manager_or_above(admin_user) == admin_user
    assert await require_manager_or_above(manager_user) == manager_user


@pytest.mark.asyncio
async def test_require_manager_or_above_forbidden():
    """Verify require_manager_or_above raises 403 for maintenance / resident roles."""
    maint_user = User(email="maint@asip.ai", role=UserRole.maintenance)
    with pytest.raises(HTTPException) as exc:
        await require_manager_or_above(maint_user)
    assert exc.value.status_code == 403
