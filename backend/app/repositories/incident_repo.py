import uuid
from typing import Optional, List
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models.incident import Incident, IncidentStatus, IncidentSeverity


class IncidentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> Incident:
        incident = Incident(**data)
        self.db.add(incident)
        await self.db.flush()
        await self.db.refresh(incident)
        return incident

    async def get_by_id(self, incident_id: uuid.UUID) -> Optional[Incident]:
        result = await self.db.execute(
            select(Incident)
            .options(
                selectinload(Incident.tower),
                selectinload(Incident.contractor_assignment),
                selectinload(Incident.agent_logs),
                selectinload(Incident.notifications),
            )
            .where(Incident.id == incident_id)
        )
        return result.scalar_one_or_none()

    async def list_incidents(
        self,
        status: Optional[IncidentStatus] = None,
        severity: Optional[IncidentSeverity] = None,
        tower_id: Optional[uuid.UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Incident], int]:
        filters = []
        if status:
            filters.append(Incident.status == status)
        if severity:
            filters.append(Incident.severity == severity)
        if tower_id:
            filters.append(Incident.tower_id == tower_id)

        count_q = select(func.count(Incident.id))
        if filters:
            count_q = count_q.where(and_(*filters))
        total = (await self.db.execute(count_q)).scalar_one()

        q = (
            select(Incident)
            .options(selectinload(Incident.contractor_assignment))
            .order_by(Incident.detected_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        if filters:
            q = q.where(and_(*filters))
        items = (await self.db.execute(q)).scalars().all()
        return list(items), total

    async def update(self, incident_id: uuid.UUID, data: dict) -> Optional[Incident]:
        incident = await self.get_by_id(incident_id)
        if not incident:
            return None
        for key, value in data.items():
            setattr(incident, key, value)
        await self.db.flush()
        await self.db.refresh(incident)
        return incident

    async def count_by_status(self) -> dict:
        result = await self.db.execute(
            select(Incident.status, func.count(Incident.id))
            .group_by(Incident.status)
        )
        return {row[0].value: row[1] for row in result.all()}

    async def count_by_severity(self) -> dict:
        result = await self.db.execute(
            select(Incident.severity, func.count(Incident.id))
            .group_by(Incident.severity)
        )
        return {row[0].value: row[1] for row in result.all()}
