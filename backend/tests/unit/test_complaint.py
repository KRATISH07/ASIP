import uuid
import pytest
from datetime import datetime, timezone
from sqlalchemy import select

from app.db.models.complaint import Complaint, ComplaintStatus, ComplaintCategory
from app.db.models.incident import Incident
from app.repositories.complaint_repo import ComplaintRepository
from app.services import complaint_service


@pytest.fixture
async def session():
    """Yield a real database session with a clean complaints table."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from app.config import settings
    from sqlalchemy import text
    
    engine = create_async_engine(settings.database_url, pool_size=1, max_overflow=0)
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with session_factory() as s:
        await s.execute(text("TRUNCATE TABLE complaints, incidents CASCADE;"))
        await s.commit()
        try:
            yield s
        finally:
            await s.close()
    await engine.dispose()


@pytest.mark.asyncio
async def test_complaint_creation(session):
    """Verify complaint is created successfully and defaults to submitted status."""
    resident_id = uuid.uuid4()
    data = {
        "title": "Broken Lift in Tower A",
        "description": "The lift is making strange noises and stopping randomly.",
        "category": ComplaintCategory.lift,
    }

    complaint = await complaint_service.create_complaint(data, session, resident_id=resident_id)
    assert complaint.id is not None
    assert complaint.status == ComplaintStatus.submitted
    assert complaint.resident_id == resident_id

    # Verify in DB
    repo = ComplaintRepository(session)
    loaded = await repo.get_by_id(complaint.id)
    assert loaded is not None
    assert loaded.title == "Broken Lift in Tower A"


@pytest.mark.asyncio
async def test_complaint_conversion(session, monkeypatch):
    """Verify complaint is atomically converted to incident, status changes, and task is queued."""
    # Mock WorkflowService process_sensor_data
    from app.services.workflow_service import WorkflowService
    workflow_called = []
    async def mock_process(self, payload, *args, **kwargs):
        workflow_called.append(payload)
        from app.db.models.incident import Incident
        return Incident()
    monkeypatch.setattr(WorkflowService, "process_sensor_data", mock_process)

    # 1. Create complaint
    data = {
        "title": "Water Leakage",
        "description": "Water leaking from ceiling of apartment 501",
        "category": ComplaintCategory.plumbing,
    }
    complaint = await complaint_service.create_complaint(data, session)
    assert complaint.status == ComplaintStatus.submitted

    # 2. Convert to incident
    class MockBackgroundTasks:
        def __init__(self):
            self.tasks = []
        def add_task(self, func, *args, **kwargs):
            self.tasks.append((func, args, kwargs))

    bg_tasks = MockBackgroundTasks()
    res = await complaint_service.convert_to_incident(
        complaint.id, session, bg_tasks, incident_type_override="water_pressure_drop"
    )
    assert res["complaint_id"] == complaint.id
    assert res["incident_id"] is not None
    assert res["workflow_queued"] is True

    # Verify status changed and linked incident set in DB
    repo = ComplaintRepository(session)
    loaded = await repo.get_by_id(complaint.id)
    assert loaded.status == ComplaintStatus.converted_to_incident
    assert loaded.linked_incident_id is not None

    # Run queued background task
    assert len(bg_tasks.tasks) == 1
    func, args, kwargs = bg_tasks.tasks[0]
    await func(*args, **kwargs)
    assert len(workflow_called) == 1
    assert workflow_called[0]["metadata"]["complaint_id"] == str(complaint.id)
