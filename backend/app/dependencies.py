from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.auth import decode_token
from app.core.exceptions import unauthorized_http, forbidden_http
from app.repositories.user_repo import UserRepository
from app.db.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        token_data = decode_token(token)
    except ValueError:
        raise unauthorized_http()

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(token_data.user_id)
    if not user or not user.is_active:
        raise unauthorized_http("User not found or inactive.")
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise forbidden_http("Admin access required.")
    return current_user


async def require_manager_or_above(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.admin, UserRole.manager):
        raise forbidden_http("Manager or Admin access required.")
    return current_user
