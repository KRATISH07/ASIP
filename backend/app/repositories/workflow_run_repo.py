import uuid
from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.workflow_run import WorkflowRun, WorkflowRunStatus


class WorkflowRunRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> WorkflowRun:
        run = WorkflowRun(**data)
        self.db.add(run)
        await self.db.flush()
        await self.db.refresh(run)
        return run

    async def get_by_id(self, run_id: uuid.UUID) -> Optional[WorkflowRun]:
        result = await self.db.execute(
            select(WorkflowRun).where(WorkflowRun.id == run_id)
        )
        return result.scalar_one_or_none()

    async def get_by_incident_id(self, incident_id: uuid.UUID) -> Optional[WorkflowRun]:
        result = await self.db.execute(
            select(WorkflowRun).where(WorkflowRun.incident_id == incident_id)
        )
        return result.scalar_one_or_none()

    async def update(self, run_id: uuid.UUID, data: dict) -> Optional[WorkflowRun]:
        run = await self.get_by_id(run_id)
        if not run:
            return None
        for key, value in data.items():
            setattr(run, key, value)
        await self.db.flush()
        await self.db.refresh(run)
        return run

    async def get_runnable_retries(self, max_retries: int = 3) -> List[WorkflowRun]:
        result = await self.db.execute(
            select(WorkflowRun).where(
                and_(
                    WorkflowRun.status == WorkflowRunStatus.failed,
                    WorkflowRun.retry_count < max_retries,
                )
            )
        )
        return list(result.scalars().all())
