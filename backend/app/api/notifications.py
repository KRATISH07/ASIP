import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies import get_current_user
from app.repositories.notification_repo import NotificationRepository
from app.schemas.contractor import NotificationOut
from app.db.models.notification import NotificationStatus
from app.db.models.user import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=List[NotificationOut], summary="List all notifications")
async def list_notifications(
    status_filter: Optional[NotificationStatus] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = NotificationRepository(db)
    items = await repo.list_all(status=status_filter)
    return items


@router.get(
    "/incident/{incident_id}",
    response_model=List[NotificationOut],
    summary="Get all notifications for an incident",
)
async def list_by_incident(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = NotificationRepository(db)
    return await repo.list_by_incident(incident_id)


@router.post(
    "/{notification_id}/send",
    summary="Mark a notification as sent (or trigger actual delivery)",
)
async def send_notification(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = NotificationRepository(db)
    await repo.mark_sent(notification_id)
    return {"message": "Notification marked as sent.", "id": str(notification_id)}


@router.delete("/{notification_id}", status_code=200, summary="Delete a notification")
async def delete_notification(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = NotificationRepository(db)
    notification = await repo.get_by_id(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    await db.delete(notification)
    await db.commit()
    return {"message": "Notification deleted successfully"}
