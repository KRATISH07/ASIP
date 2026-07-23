import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, func, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.models.sensor_event_buffer import SensorEventBuffer, SyncStatus


class SensorBufferRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_batch(
        self, events: List[dict]
    ) -> tuple[int, int]:
        """
        Insert many events, skipping duplicates via idempotency_key.
        Returns (inserted_count, duplicate_count).
        """
        if not events:
            return 0, 0

        inserted = 0
        duplicates = 0
        for event_data in events:
            stmt = (
                pg_insert(SensorEventBuffer)
                .values(**event_data)
                .on_conflict_do_nothing(index_elements=["idempotency_key"])
            )
            result = await self.db.execute(stmt)
            if result.rowcount > 0:
                inserted += 1
            else:
                duplicates += 1
        await self.db.flush()
        return inserted, duplicates

    async def get_failed(self, limit: int = 50) -> List[SensorEventBuffer]:
        """Fetch failed events ordered by last_attempt_at (oldest first)."""
        result = await self.db.execute(
            select(SensorEventBuffer)
            .where(SensorEventBuffer.sync_status == SyncStatus.failed)
            .order_by(SensorEventBuffer.last_attempt_at.asc().nullsfirst())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_pending(self, limit: int = 50) -> List[SensorEventBuffer]:
        """Fetch pending events ordered by event_timestamp (oldest first)."""
        result = await self.db.execute(
            select(SensorEventBuffer)
            .where(SensorEventBuffer.sync_status == SyncStatus.pending)
            .order_by(SensorEventBuffer.event_timestamp.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_synced(self, event_id: uuid.UUID) -> None:
        """Mark an event as successfully synced."""
        result = await self.db.execute(
            select(SensorEventBuffer).where(SensorEventBuffer.id == event_id)
        )
        event = result.scalar_one_or_none()
        if event:
            event.sync_status = SyncStatus.synced
            await self.db.flush()

    async def mark_failed(self, event_id: uuid.UUID, error: str) -> None:
        """Mark an event as failed with error message and update retry metadata."""
        from datetime import timezone
        result = await self.db.execute(
            select(SensorEventBuffer).where(SensorEventBuffer.id == event_id)
        )
        event = result.scalar_one_or_none()
        if event:
            event.sync_status = SyncStatus.failed
            event.error_message = error
            event.retry_count += 1
            event.last_attempt_at = datetime.now(timezone.utc)
            await self.db.flush()

    async def get_stats(self) -> dict:
        """Return aggregate counts and oldest unsynced event age."""
        from datetime import timezone

        pending_count = (
            await self.db.execute(
                select(func.count(SensorEventBuffer.id)).where(
                    SensorEventBuffer.sync_status == SyncStatus.pending
                )
            )
        ).scalar_one()

        failed_count = (
            await self.db.execute(
                select(func.count(SensorEventBuffer.id)).where(
                    SensorEventBuffer.sync_status == SyncStatus.failed
                )
            )
        ).scalar_one()

        synced_count = (
            await self.db.execute(
                select(func.count(SensorEventBuffer.id)).where(
                    SensorEventBuffer.sync_status == SyncStatus.synced
                )
            )
        ).scalar_one()

        # Oldest unsynced event (pending or failed)
        oldest_result = await self.db.execute(
            select(func.min(SensorEventBuffer.event_timestamp)).where(
                SensorEventBuffer.sync_status.in_([SyncStatus.pending, SyncStatus.failed])
            )
        )
        oldest_ts = oldest_result.scalar_one_or_none()

        oldest_age_seconds: Optional[float] = None
        if oldest_ts:
            now = datetime.now(timezone.utc)
            # Make timezone-aware if needed
            if oldest_ts.tzinfo is None:
                from datetime import timezone as tz
                oldest_ts = oldest_ts.replace(tzinfo=tz.utc)
            oldest_age_seconds = (now - oldest_ts).total_seconds()

        # Replay success rate: synced / (synced + failed), 0 if no data
        total_attempted = synced_count + failed_count
        replay_success_rate = (synced_count / total_attempted) if total_attempted > 0 else 0.0

        return {
            "pending_count": pending_count,
            "failed_count": failed_count,
            "synced_count": synced_count,
            "replay_success_rate": round(replay_success_rate, 4),
            "oldest_unsynced_age_seconds": oldest_age_seconds,
        }
