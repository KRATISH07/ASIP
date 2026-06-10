import uuid
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.contractor import Contractor, ContractorAssignment


class ContractorRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> Contractor:
        contractor = Contractor(**data)
        self.db.add(contractor)
        await self.db.flush()
        await self.db.refresh(contractor)
        return contractor

    async def get_by_id(self, contractor_id: uuid.UUID) -> Optional[Contractor]:
        result = await self.db.execute(
            select(Contractor).where(Contractor.id == contractor_id)
        )
        return result.scalar_one_or_none()

    async def list_active(self, specialization: Optional[str] = None) -> List[Contractor]:
        q = select(Contractor).where(Contractor.is_active == True).order_by(Contractor.rating.desc())
        result = await self.db.execute(q)
        contractors = result.scalars().all()
        if specialization:
            contractors = [c for c in contractors if specialization in c.specializations]
        return list(contractors)

    async def create_assignment(self, data: dict) -> ContractorAssignment:
        assignment = ContractorAssignment(**data)
        self.db.add(assignment)
        await self.db.flush()
        await self.db.refresh(assignment)
        return assignment

    async def update_stats(self, contractor_id: uuid.UUID, success: bool) -> None:
        contractor = await self.get_by_id(contractor_id)
        if contractor:
            contractor.total_jobs += 1
            if success:
                contractor.success_rate = (
                    (contractor.success_rate * (contractor.total_jobs - 1) + 1.0)
                    / contractor.total_jobs
                )
            await self.db.flush()
