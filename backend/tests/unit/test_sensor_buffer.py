import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import select

from app.db.models.sensor_event_buffer import SensorEventBuffer, SyncStatus
from app.repositories.sensor_buffer_repo import SensorBufferRepository
from app.services import sensor_buffer_service


@pytest.fixture
async def session():
    """Yield a real database session scoped to a transaction that rolls back."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from app.config import settings
    from sqlalchemy import text
    
    # Create engine bound to the current test's event loop
    engine = create_async_engine(settings.database_url, pool_size=1, max_overflow=0)
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with session_factory() as s:
        # Clean slate before starting the test
        await s.execute(text("TRUNCATE TABLE sensor_event_buffer CASCADE;"))
        await s.commit()
        
        try:
            yield s
        finally:
            await s.close()
    await engine.dispose()


@pytest.mark.asyncio
async def test_duplicate_upload_skipped(session):
    """
    Same idempotency_key uploaded twice in a batch or successive batches
    should only result in one row inserted, with the other skipped.
    """
    sensor_id = "sensor-1"
    key = f"key-{uuid.uuid4()}"
    timestamp = datetime.now(timezone.utc)
    payload = {
        "tower_id": str(uuid.uuid4()),
        "sensor_type": "water_pressure",
        "value": 1.2,
        "unit": "bar",
        "timestamp": timestamp.isoformat(),
    }

    events = [
        {
            "sensor_id": sensor_id,
            "idempotency_key": key,
            "payload": payload,
            "event_timestamp": timestamp,
        },
        {
            "sensor_id": sensor_id,
            "idempotency_key": key,
            "payload": payload,
            "event_timestamp": timestamp,
        },
    ]

    # Batch upload containing duplicate
    result = await sensor_buffer_service.upload_events(events, session)
    assert result["total_received"] == 2
    assert result["successful"] == 1
    assert result["duplicate_skipped"] == 1

    # Verify single record in DB
    repo = SensorBufferRepository(session)
    pending = await repo.get_pending(limit=10)
    assert len(pending) == 1
    assert pending[0].sensor_id == sensor_id


@pytest.mark.asyncio
async def test_retry_count_increments_on_failure(session, monkeypatch):
    """
    If a buffered event replay fails, the sync_status should be 'failed',
    retry_count should increment, and error_message should be captured.
    """
    sensor_id = "sensor-fail"
    key = f"key-{uuid.uuid4()}"
    timestamp = datetime.now(timezone.utc)
    # Bad payload (missing required keys like tower_id) to trigger workflow failure
    payload = {
        "sensor_type": "water_pressure",
        "value": -99.0,
    }

    events = [
        {
            "sensor_id": sensor_id,
            "idempotency_key": key,
            "payload": payload,
            "event_timestamp": timestamp,
        }
    ]

    # 1. Upload event (inserted as pending)
    upload_res = await sensor_buffer_service.upload_events(events, session)
    assert upload_res["successful"] == 1

    # Mock process_sensor_data to raise exception to guarantee failure
    from app.services.workflow_service import WorkflowService
    async def mock_process(*args, **kwargs):
        raise ValueError("Simulated ingestion crash")
    monkeypatch.setattr(WorkflowService, "process_sensor_data", mock_process)

    # 2. Replay (will fail)
    # A fresh upload is status=pending. We need to manually mark it failed first, then replay.
    repo = SensorBufferRepository(session)
    pending = await repo.get_pending(limit=10)
    assert len(pending) == 1
    event = pending[0]
    await repo.mark_failed(event.id, "initial failure")

    # Verify state is failed, retry_count is 1
    assert event.sync_status == SyncStatus.failed
    assert event.retry_count == 1

    # 3. Replay failed event
    replay_res = await sensor_buffer_service.replay_failed_events(session, limit=10)
    assert replay_res["replayed"] == 1
    assert replay_res["succeeded"] == 0
    assert replay_res["failed"] == 1

    # Refresh from DB
    stmt = select(SensorEventBuffer).where(SensorEventBuffer.id == event.id)
    res = await session.execute(stmt)
    refreshed = res.scalar_one()
    assert refreshed.sync_status == SyncStatus.failed
    assert refreshed.retry_count == 2
    assert "Simulated ingestion crash" in refreshed.error_message


@pytest.mark.asyncio
async def test_partial_replay_success(session, monkeypatch):
    """
    Replay a batch where one event succeeds and another fails.
    """
    sensor_id = "sensor-partial"
    key1 = f"key-{uuid.uuid4()}"
    key2 = f"key-{uuid.uuid4()}"
    timestamp = datetime.now(timezone.utc)

    # 1. Insert two failed events
    repo = SensorBufferRepository(session)
    now = datetime.now(timezone.utc)
    ev1 = SensorEventBuffer(
        id=uuid.uuid4(),
        sensor_id=sensor_id,
        idempotency_key=key1,
        payload={"val": 1},
        event_timestamp=timestamp,
        received_at=now,
        sync_status=SyncStatus.failed,
        retry_count=1,
    )
    ev2 = SensorEventBuffer(
        id=uuid.uuid4(),
        sensor_id=sensor_id,
        idempotency_key=key2,
        payload={"val": 2},
        event_timestamp=timestamp,
        received_at=now,
        sync_status=SyncStatus.failed,
        retry_count=1,
    )
    session.add_all([ev1, ev2])
    await session.flush()

    # Mock process_sensor_data to succeed for ev1 and fail for ev2
    from app.services.workflow_service import WorkflowService
    async def mock_process(self, payload, *args, **kwargs):
        if payload.get("val") == 1:
            # Succeed (return dummy incident or None)
            from app.db.models.incident import Incident
            return Incident()
        else:
            raise ValueError("Failure on payload 2")
            
    monkeypatch.setattr(WorkflowService, "process_sensor_data", mock_process)

    # Replay
    replay_res = await sensor_buffer_service.replay_failed_events(session, limit=10)
    assert replay_res["replayed"] == 2
    assert replay_res["succeeded"] == 1
    assert replay_res["failed"] == 1

    # Verify DB states
    stmt1 = select(SensorEventBuffer).where(SensorEventBuffer.id == ev1.id)
    ev1_db = (await session.execute(stmt1)).scalar_one()
    assert ev1_db.sync_status == SyncStatus.synced

    stmt2 = select(SensorEventBuffer).where(SensorEventBuffer.id == ev2.id)
    ev2_db = (await session.execute(stmt2)).scalar_one()
    assert ev2_db.sync_status == SyncStatus.failed
    assert ev2_db.retry_count == 2
    assert "Failure on payload 2" in ev2_db.error_message
