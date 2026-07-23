import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.notification import Notification, NotificationStatus
from app.db.models.agent_log import AgentLog


class NotificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, notification_id: uuid.UUID) -> Optional[Notification]:
        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()

    async def create_bulk(self, payloads: List[dict]) -> List[Notification]:
        notifications = [Notification(**p) for p in payloads]
        self.db.add_all(notifications)
        await self.db.flush()
        return notifications

    async def list_by_incident(self, incident_id: uuid.UUID) -> List[Notification]:
        result = await self.db.execute(
            select(Notification).where(Notification.incident_id == incident_id)
        )
        return list(result.scalars().all())

    async def list_all(self, status: Optional[NotificationStatus] = None) -> List[Notification]:
        q = select(Notification).order_by(Notification.created_at.desc())
        if status:
            q = q.where(Notification.status == status)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def mark_sent(self, notification_id: uuid.UUID) -> None:
        from datetime import datetime, timezone
        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notif = result.scalar_one_or_none()
        if notif:
            notif.status = NotificationStatus.sent
            notif.sent_at = datetime.now(timezone.utc)
            await self.db.flush()


class AgentLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> AgentLog:
        log = AgentLog(**data)
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(log)
        return log

    async def list_by_incident(self, incident_id: uuid.UUID) -> List[AgentLog]:
        result = await self.db.execute(
            select(AgentLog)
            .where(AgentLog.incident_id == incident_id)
            .order_by(AgentLog.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_recent(self, limit: int = 50) -> List[AgentLog]:
        result = await self.db.execute(
            select(AgentLog).order_by(AgentLog.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
