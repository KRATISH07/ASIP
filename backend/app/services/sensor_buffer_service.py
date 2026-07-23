"""
Sensor Buffer Service — Store-and-Forward orchestration layer.

Responsibilities:
- Replay orchestration: re-process failed buffered events through the incident workflow
- Duplicate detection: delegated to SensorBufferRepository (ON CONFLICT DO NOTHING)
- Synchronisation management: mark events synced/failed, track retry counts
- Retry tracking: increment retry_count and last_attempt_at on each failure

Architecture:
    Edge gateway → POST /sensor-buffer/upload → SensorBufferRepository (insert)
    POST /sensor-buffer/replay → sensor_buffer_service.replay_failed() → workflow
    Workflow success → mark_synced; Workflow failure → mark_failed (with error)
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.sensor_buffer_repo import SensorBufferRepository
from app.core.logging import get_logger

logger = get_logger("sensor_buffer_service")


async def upload_events(events: list[dict], db: AsyncSession) -> dict:
    """
    Batch-insert buffered sensor events.
    Idempotency is enforced via idempotency_key (conflicts are silently skipped).

    Parameters
    ----------
    events : list[dict]
        Each dict must contain: sensor_id, idempotency_key, payload, event_timestamp.
        received_at and sync_status are set server-side.

    Returns
    -------
    dict with keys: total_received, successful, failed, duplicate_skipped
    """
    now = datetime.now(timezone.utc)
    repo = SensorBufferRepository(db)

    enriched = []
    for e in events:
        enriched.append({
            **e,
            "received_at": now,
            "sync_status": "pending",
            "retry_count": 0,
        })

    inserted, duplicates = await repo.create_batch(enriched)
    failed_insert = len(events) - inserted - duplicates

    await db.commit()

    logger.info(
        "Sensor buffer upload complete",
        total=len(events),
        inserted=inserted,
        duplicates=duplicates,
        failed=failed_insert,
    )
    return {
        "total_received": len(events),
        "successful": inserted,
        "failed": failed_insert,
        "duplicate_skipped": duplicates,
    }


async def replay_failed_events(db: AsyncSession, limit: int = 50) -> dict:
    """
    Retry failed buffered events by re-injecting their payloads into the incident workflow.

    Each event's payload is expected to be a valid sensor reading compatible with
    POST /incidents/sensor-data. Events that succeed are marked `synced`; events
    that fail are marked `failed` with an updated error_message and retry_count.

    Parameters
    ----------
    db : AsyncSession
        The async database session.
    limit : int
        Maximum events to attempt per replay call.

    Returns
    -------
    dict with keys: replayed, succeeded, failed
    """
    from app.services.workflow_service import WorkflowService

    repo = SensorBufferRepository(db)
    failed_events = await repo.get_failed(limit=limit)

    succeeded = 0
    failed_count = 0

    for event in failed_events:
        try:
            async with db.begin_nested():
                # Re-inject payload through the normal workflow pipeline
                service = WorkflowService(db)
                incident = await service.process_sensor_data(event.payload)
                await repo.mark_synced(event.id)
                succeeded += 1
                logger.info(
                    "Buffer event replayed successfully",
                    event_id=str(event.id),
                    sensor_id=event.sensor_id,
                    incident_id=str(incident.id) if incident else None,
                )
        except Exception as exc:
            await repo.mark_failed(event.id, str(exc))
            failed_count += 1
            logger.warning(
                "Buffer event replay failed",
                event_id=str(event.id),
                sensor_id=event.sensor_id,
                error=str(exc),
            )

    await db.commit()

    return {
        "replayed": len(failed_events),
        "succeeded": succeeded,
        "failed": failed_count,
    }


async def get_buffer_stats(db: AsyncSession) -> dict:
    """
    Return aggregate buffer health metrics.

    Returns
    -------
    dict with keys: pending_count, failed_count, synced_count,
                    replay_success_rate, oldest_unsynced_age_seconds
    """
    repo = SensorBufferRepository(db)
    return await repo.get_stats()
