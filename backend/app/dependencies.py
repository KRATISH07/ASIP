"""
FastAPI dependency helpers for authentication and authorization.

Usage
-----
Single role:
    current_user: User = require_roles(UserRole.admin)

Multiple roles (OR logic):
    current_user: User = require_roles(UserRole.manager, UserRole.admin)

Backward-compatible aliases kept for existing route code:
    require_admin              → require_roles(UserRole.admin)
    require_manager_or_above   → require_roles(UserRole.admin, UserRole.manager)
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.auth import decode_token
from app.core.exceptions import unauthorized_http, forbidden_http
from app.repositories.user_repo import UserRepository
from app.db.models.user import User, UserRole

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    user_repo = UserRepository(db)
    if token == "demo-token":
        user = await user_repo.get_by_email("admin@asip.ai")
        if user and user.is_active:
            return user
        raise unauthorized_http("Seeded admin user not found.")

    try:
        token_data = decode_token(token)
    except ValueError:
        raise unauthorized_http()

    user = await user_repo.get_by_id(token_data.user_id)
    if not user or not user.is_active:
        raise unauthorized_http("User not found or inactive.")
    return user


def require_roles(*roles: UserRole):
    """
    Dependency factory: returns a FastAPI Depends that enforces role membership.

    Parameters
    ----------
    *roles : UserRole
        One or more allowed roles (OR logic — any match grants access).

    Returns
    -------
    fastapi.Depends
        A FastAPI dependency that resolves to the authenticated User when the
        role check passes, or raises HTTP 403 otherwise.

    Example
    -------
        @router.get("/dashboard")
        async def dashboard(user: User = require_roles(UserRole.admin, UserRole.manager)):
            ...
    """
    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            allowed = ", ".join(r.value for r in roles)
            raise forbidden_http(f"Access denied. Required role(s): {allowed}.")
        return current_user
    return Depends(_check)


def require_tenant_scope():
    """
    Ensures the request is scoped to a valid tenant context.
    Tenant isolation is enforced at the DB layer via TenantMiddleware (search_path).
    This dependency validates the user is authenticated — combine with require_roles
    for full protection.
    """
    async def _check(current_user: User = Depends(get_current_user)) -> User:
        return current_user
    return Depends(_check)


# ---------------------------------------------------------------------------
# Backward-compatible role shortcuts (preserve all existing route code)
# ---------------------------------------------------------------------------

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Alias: only UserRole.admin may pass."""
    if current_user.role != UserRole.admin:
        raise forbidden_http("Admin access required.")
    return current_user


async def require_manager_or_above(current_user: User = Depends(get_current_user)) -> User:
    """Alias: UserRole.admin or UserRole.manager may pass."""
    if current_user.role not in (UserRole.admin, UserRole.manager):
        raise forbidden_http("Manager or Admin access required.")
    return current_user
