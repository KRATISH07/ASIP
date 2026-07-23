import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.complaint import Complaint, ComplaintStatus


class ComplaintRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> Complaint:
        complaint = Complaint(**data)
        self.db.add(complaint)
        await self.db.flush()
        await self.db.refresh(complaint)
        return complaint

    async def get_by_id(self, complaint_id: uuid.UUID) -> Optional[Complaint]:
        result = await self.db.execute(
            select(Complaint).where(Complaint.id == complaint_id)
        )
        return result.scalar_one_or_none()

    async def list_complaints(
        self,
        status: Optional[ComplaintStatus] = None,
        category: Optional[str] = None,
        resident_id: Optional[uuid.UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Complaint], int]:
        filters = []
        if status:
            filters.append(Complaint.status == status)
        if category:
            filters.append(Complaint.category == category)
        if resident_id:
            filters.append(Complaint.resident_id == resident_id)

        count_q = select(func.count(Complaint.id))
        if filters:
            count_q = count_q.where(and_(*filters))
        total = (await self.db.execute(count_q)).scalar_one()

        q = (
            select(Complaint)
            .order_by(Complaint.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        if filters:
            q = q.where(and_(*filters))
        items = (await self.db.execute(q)).scalars().all()
        return list(items), total

    async def update(self, complaint_id: uuid.UUID, data: dict) -> Optional[Complaint]:
        complaint = await self.get_by_id(complaint_id)
        if not complaint:
            return None
        for key, value in data.items():
            setattr(complaint, key, value)
        await self.db.flush()
        await self.db.refresh(complaint)
        return complaint

    async def get_stats(self) -> dict:
        """Aggregate complaint counts and average resolution time."""
        total = (await self.db.execute(select(func.count(Complaint.id)))).scalar_one()

        open_count = (
            await self.db.execute(
                select(func.count(Complaint.id)).where(
                    Complaint.status == ComplaintStatus.submitted
                )
            )
        ).scalar_one()

        under_review = (
            await self.db.execute(
                select(func.count(Complaint.id)).where(
                    Complaint.status == ComplaintStatus.under_review
                )
            )
        ).scalar_one()

        resolved = (
            await self.db.execute(
                select(func.count(Complaint.id)).where(
                    Complaint.status == ComplaintStatus.resolved
                )
            )
        ).scalar_one()

        converted = (
            await self.db.execute(
                select(func.count(Complaint.id)).where(
                    Complaint.status == ComplaintStatus.converted_to_incident
                )
            )
        ).scalar_one()

        # Average resolution time: resolved complaints with known timestamps
        avg_hrs_result = await self.db.execute(
            select(
                func.avg(
                    func.extract("epoch", Complaint.updated_at - Complaint.created_at) / 3600
                )
            ).where(Complaint.status == ComplaintStatus.resolved)
        )
        avg_resolution_time_hours = avg_hrs_result.scalar_one_or_none()

        return {
            "total_complaints": total,
            "open": open_count,
            "under_review": under_review,
            "resolved": resolved,
            "converted_to_incidents": converted,
            "avg_resolution_time_hours": (
                round(avg_resolution_time_hours, 2)
                if avg_resolution_time_hours is not None
                else None
            ),
        }
