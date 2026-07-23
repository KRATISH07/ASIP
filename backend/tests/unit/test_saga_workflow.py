import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.workflow_service import WorkflowService
from app.db.models.workflow_run import WorkflowRun, WorkflowRunStatus
from app.db.models.incident import Incident, IncidentStatus, IncidentSeverity


@pytest.mark.asyncio
async def test_saga_workflow_success(monkeypatch):
    """Test saga success path: run is completed and incident is created."""
    mock_db = AsyncMock()

    # Mock WorkflowRunRepository
    dummy_run = WorkflowRun(
        id=uuid.uuid4(),
        incident_id=uuid.uuid4(),
        status=WorkflowRunStatus.running,
    )
    mock_run_repo = MagicMock()
    mock_run_repo.create = AsyncMock(return_value=dummy_run)
    mock_run_repo.update = AsyncMock()
    monkeypatch.setattr(
        "app.services.workflow_service.WorkflowRunRepository",
        lambda db: mock_run_repo,
    )

    # Mock IncidentRepository
    dummy_incident = Incident(
        id=dummy_run.incident_id,
        severity=IncidentSeverity.critical,
    )
    mock_incident_repo = MagicMock()
    mock_incident_repo.create = AsyncMock(return_value=dummy_incident)
    monkeypatch.setattr(
        "app.services.workflow_service.IncidentRepository",
        lambda db: mock_incident_repo,
    )

    # Mock CompiledGraph execution
    final_state = {
        "incident_event": {
            "type": "water_pressure_drop",
            "severity": "critical",
            "confidence": 0.9,
        },
        "final_report": {"incident_summary": "Summary", "root_cause": "Pump fail"},
        "incident_id": str(dummy_run.incident_id),
        "completed_agents": ["monitoring_agent", "infrastructure_agent"],
    }
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(return_value=final_state)

    with (
        patch("app.agents.graph.get_compiled_graph", return_value=mock_graph),
        patch("app.services.memory_service.store_incident_memory") as mock_store_memory,
    ):
        service = WorkflowService(mock_db)
        sensor_payload = {
            "tower_id": str(uuid.uuid4()),
            "sensor_type": "water_pressure",
            "value": 0.2,
        }
        res = await service.process_sensor_data(sensor_payload)

        # Assertions
        assert res == dummy_incident
        mock_run_repo.create.assert_called_once()
        mock_run_repo.update.assert_called_once_with(
            dummy_run.id,
            {
                "status": WorkflowRunStatus.completed,
                "completed_steps": ["monitoring_agent", "infrastructure_agent"],
                "current_step": None,
            },
        )
        mock_incident_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_saga_workflow_failure(monkeypatch):
    """Test saga failure path: run is marked failed with error details, and no incident is created."""
    mock_db = AsyncMock()

    # Mock WorkflowRunRepository
    dummy_run = WorkflowRun(
        id=uuid.uuid4(),
        incident_id=uuid.uuid4(),
        status=WorkflowRunStatus.running,
    )
    mock_run_repo = MagicMock()
    mock_run_repo.create = AsyncMock(return_value=dummy_run)
    mock_run_repo.update = AsyncMock()
    monkeypatch.setattr(
        "app.services.workflow_service.WorkflowRunRepository",
        lambda db: mock_run_repo,
    )

    # Mock CompiledGraph execution to raise error
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(side_effect=Exception("LLM Timeout Error"))

    # Mock state history retrieval on failure
    mock_state_info = MagicMock()
    mock_state_info.values = {
        "completed_agents": ["monitoring_agent"],
        "sensor_data": {},
    }
    mock_state_info.next = ["infrastructure_agent"]
    mock_graph.aget_state = AsyncMock(return_value=mock_state_info)

    with patch("app.agents.graph.get_compiled_graph", return_value=mock_graph):
        service = WorkflowService(mock_db)
        sensor_payload = {
            "tower_id": str(uuid.uuid4()),
            "sensor_type": "water_pressure",
            "value": 0.2,
        }
        res = await service.process_sensor_data(sensor_payload)

        # Assertions
        assert res is None
        mock_run_repo.create.assert_called_once()
        mock_run_repo.update.assert_called_once_with(
            dummy_run.id,
            {
                "status": WorkflowRunStatus.failed,
                "completed_steps": ["monitoring_agent"],
                "current_step": "infrastructure_agent",
                "failed_at_step": "infrastructure_agent",
                "last_error": "LLM Timeout Error",
            },
        )


@pytest.mark.asyncio
async def test_saga_workflow_retry_success(monkeypatch):
    """Test that retrying a failed run successfully resumes and completes the workflow."""
    mock_db = AsyncMock()

    # Mock WorkflowRunRepository
    dummy_run = WorkflowRun(
        id=uuid.uuid4(),
        incident_id=uuid.uuid4(),
        status=WorkflowRunStatus.failed,
        retry_count=0,
    )
    mock_run_repo = MagicMock()
    mock_run_repo.get_by_id = AsyncMock(return_value=dummy_run)
    mock_run_repo.update = AsyncMock(return_value=dummy_run)
    monkeypatch.setattr(
        "app.services.workflow_service.WorkflowRunRepository",
        lambda db: mock_run_repo,
    )

    # Mock IncidentRepository
    dummy_incident = Incident(
        id=dummy_run.incident_id,
        severity=IncidentSeverity.critical,
    )
    mock_incident_repo = MagicMock()
    mock_incident_repo.create = AsyncMock(return_value=dummy_incident)
    monkeypatch.setattr(
        "app.services.workflow_service.IncidentRepository",
        lambda db: mock_incident_repo,
    )

    # Mock CompiledGraph execution on resume (input = None)
    final_state = {
        "incident_event": {
            "type": "water_pressure_drop",
            "severity": "critical",
            "confidence": 0.9,
        },
        "final_report": {"incident_summary": "Summary", "root_cause": "Pump fail"},
        "incident_id": str(dummy_run.incident_id),
        "completed_agents": ["monitoring_agent", "infrastructure_agent"],
    }
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(return_value=final_state)

    with (
        patch("app.agents.graph.get_compiled_graph", return_value=mock_graph),
        patch("app.services.memory_service.store_incident_memory") as mock_store_memory,
    ):
        service = WorkflowService(mock_db)
        res = await service.retry_workflow_run(dummy_run.id)

        # Assertions
        assert res == dummy_incident
        mock_graph.ainvoke.assert_called_once_with(None, config={"configurable": {"thread_id": str(dummy_run.incident_id)}})
        
        # Verify update calls:
        # 1. Update retry_count and status to running
        mock_run_repo.update.assert_any_call(
            dummy_run.id,
            {"retry_count": 1, "status": WorkflowRunStatus.running},
        )
        # 2. Update status to completed
        mock_run_repo.update.assert_any_call(
            dummy_run.id,
            {
                "status": WorkflowRunStatus.completed,
                "completed_steps": ["monitoring_agent", "infrastructure_agent"],
                "current_step": None,
            },
        )


@pytest.mark.asyncio
async def test_saga_workflow_retry_fails_escalates(monkeypatch):
    """Test that exceeding max retries triggers the compensating transaction (escalated Incident)."""
    mock_db = AsyncMock()

    # Mock WorkflowRunRepository. Retry count is 2, so next retry makes it 3 (max).
    dummy_run = WorkflowRun(
        id=uuid.uuid4(),
        incident_id=uuid.uuid4(),
        status=WorkflowRunStatus.failed,
        retry_count=2,
        failed_at_step="infrastructure_agent",
    )
    mock_run_repo = MagicMock()
    mock_run_repo.get_by_id = AsyncMock(return_value=dummy_run)
    # Return updated run with retry_count=3
    updated_run = WorkflowRun(
        id=dummy_run.id,
        incident_id=dummy_run.incident_id,
        status=WorkflowRunStatus.running,
        retry_count=3,
    )
    mock_run_repo.update = AsyncMock(return_value=updated_run)
    monkeypatch.setattr(
        "app.services.workflow_service.WorkflowRunRepository",
        lambda db: mock_run_repo,
    )

    # Mock IncidentRepository to return the escalated incident
    dummy_incident = Incident(
        id=dummy_run.incident_id,
        severity=IncidentSeverity.high,
        status=IncidentStatus.escalated,
    )
    mock_incident_repo = MagicMock()
    mock_incident_repo.create = AsyncMock(return_value=dummy_incident)
    monkeypatch.setattr(
        "app.services.workflow_service.IncidentRepository",
        lambda db: mock_incident_repo,
    )

    # Mock graph execution failure on retry
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(side_effect=Exception("Database Connection Error"))

    # Mock state history retrieval on failure
    mock_state_info = MagicMock()
    mock_state_info.values = {
        "completed_agents": ["monitoring_agent"],
        "sensor_data": {
            "tower_id": str(uuid.uuid4()),
            "sensor_type": "water_pressure",
            "value": 0.2,
        },
    }
    mock_state_info.next = ["infrastructure_agent"]
    mock_graph.aget_state = AsyncMock(return_value=mock_state_info)

    with patch("app.agents.graph.get_compiled_graph", return_value=mock_graph):
        service = WorkflowService(mock_db)
        res = await service.retry_workflow_run(dummy_run.id)

        # Assertions
        assert res == dummy_incident
        mock_graph.ainvoke.assert_called_once()
        
        # Verify status set to compensating
        mock_run_repo.update.assert_any_call(
            dummy_run.id,
            {
                "status": WorkflowRunStatus.compensating,
                "completed_steps": ["monitoring_agent"],
                "current_step": None,
                "failed_at_step": "infrastructure_agent",
                "last_error": "Database Connection Error",
            },
        )
        
        # Verify escalated incident is created
        mock_incident_repo.create.assert_called_once()
        called_incident_data = mock_incident_repo.create.call_args[0][0]
        assert called_incident_data["id"] == dummy_run.incident_id
        assert called_incident_data["status"] == IncidentStatus.escalated
        assert "Automation pipeline failed to complete" in called_incident_data["description"]
        assert called_incident_data["ai_decision"]["requires_manual_review"] is True


@pytest.mark.asyncio
async def test_reconcile_failed_runs(monkeypatch):
    """Test reconciler finds failed runs and triggers retry."""
    mock_db = AsyncMock()

    # Mock WorkflowRunRepository
    dummy_runs = [
        WorkflowRun(id=uuid.uuid4(), status=WorkflowRunStatus.failed, retry_count=0),
        WorkflowRun(id=uuid.uuid4(), status=WorkflowRunStatus.failed, retry_count=1),
    ]
    mock_run_repo = MagicMock()
    mock_run_repo.get_runnable_retries = AsyncMock(return_value=dummy_runs)
    monkeypatch.setattr(
        "app.services.workflow_service.WorkflowRunRepository",
        lambda db: mock_run_repo,
    )

    service = WorkflowService(mock_db)
    
    # Mock retry_workflow_run
    dummy_incident = Incident(id=uuid.uuid4())
    service.retry_workflow_run = AsyncMock(return_value=dummy_incident)

    res = await service.reconcile_failed_runs(max_retries=3)

    assert len(res) == 2
    assert res[0] == dummy_incident
    assert service.retry_workflow_run.call_count == 2
