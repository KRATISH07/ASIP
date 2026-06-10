import uuid
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies import get_current_user
from app.repositories.notification_repo import AgentLogRepository
from app.schemas.contractor import AgentLogOut
from app.db.models.user import User

router = APIRouter(prefix="/agent-logs", tags=["Agent Observability"])


@router.get("/", response_model=List[AgentLogOut], summary="List recent agent execution logs")
async def list_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = AgentLogRepository(db)
    logs = await repo.list_recent(limit=100)
    return logs


@router.get(
    "/{incident_id}",
    response_model=List[AgentLogOut],
    summary="Get all agent logs for a specific incident",
)
async def logs_by_incident(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = AgentLogRepository(db)
    return await repo.list_by_incident(incident_id)
