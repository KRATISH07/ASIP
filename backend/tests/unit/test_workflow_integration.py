import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.workflow_service import WorkflowService
from app.core.request_context import set_request_context
from app.db.models.incident import Incident

@pytest.mark.asyncio
async def test_process_sensor_data_success(monkeypatch):
    """Test process_sensor_data creates incident and stores incident memory on success."""
    # Set correlation ID context
    set_request_context(trace_id="test_wf_trace")

    # Mock DB session
    mock_db = AsyncMock()
    
    from app.db.models.incident import IncidentSeverity
    # Mock incident repository
    dummy_incident = Incident(
        id=uuid.uuid4(),
        severity=IncidentSeverity.critical,
    )
    mock_incident_repo = MagicMock()
    mock_incident_repo.create = AsyncMock(return_value=dummy_incident)
    monkeypatch.setattr("app.services.workflow_service.IncidentRepository", lambda db: mock_incident_repo)

    # Mock WorkflowRunRepository
    mock_run_repo = MagicMock()
    mock_run_repo.create = AsyncMock(return_value=MagicMock())
    mock_run_repo.update = AsyncMock()
    monkeypatch.setattr("app.services.workflow_service.WorkflowRunRepository", lambda db: mock_run_repo)

    # Mock CompiledGraph execution
    final_state = {
        "incident_event": {"type": "water_pressure_drop", "severity": "critical", "confidence": 0.9},
        "final_report": {"incident_summary": "Summary", "root_cause": "Pump fail"},
        "incident_id": str(dummy_incident.id),
        "impact": {"estimated_residents": 150},
    }
    mock_graph = MagicMock()
    async def mock_invoke(init_state, *args, **kwargs):
        return {**init_state, **final_state}
    mock_graph.ainvoke = AsyncMock(side_effect=mock_invoke)
    
    with (
        patch("app.agents.graph.get_compiled_graph", return_value=mock_graph),
        patch("app.services.memory_service.store_incident_memory") as mock_store_memory
    ):
        service = WorkflowService(mock_db)
        sensor_payload = {
            "tower_id": str(uuid.uuid4()),
            "sensor_type": "water_pressure",
            "value": 0.2,
        }
        res = await service.process_sensor_data(sensor_payload)
        
        assert res == dummy_incident
        mock_graph.ainvoke.assert_called_once()
        mock_store_memory.assert_awaited_once()

        # Check payload matches
        called_state = mock_store_memory.call_args[0][0]
        assert called_state["trace_id"] == "test_wf_trace"
        assert called_state["_schema_version"] == "v5.1"


@pytest.mark.asyncio
async def test_process_sensor_data_failure_records_error(monkeypatch):
    """Test process_sensor_data calls failure recording if workflow raises exception."""
    set_request_context(trace_id="test_fail_trace")

    mock_db = AsyncMock()
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(side_effect=Exception("LLM Timeout Error"))

    # Mock WorkflowRunRepository
    mock_run_repo = MagicMock()
    mock_run_repo.create = AsyncMock(return_value=MagicMock())
    mock_run_repo.update = AsyncMock()
    monkeypatch.setattr("app.services.workflow_service.WorkflowRunRepository", lambda db: mock_run_repo)

    with (
        patch("app.agents.graph.get_compiled_graph", return_value=mock_graph),
        patch("app.services.workflow_service.WorkflowService._record_pipeline_failure") as mock_record_failure
    ):
        service = WorkflowService(mock_db)
        sensor_payload = {
            "tower_id": str(uuid.uuid4()),
            "sensor_type": "water_pressure",
            "value": 0.2,
        }
        res = await service.process_sensor_data(sensor_payload)
        
        assert res is None
        mock_record_failure.assert_awaited_once()
        called_args = mock_record_failure.call_args[1]
        assert "LLM Timeout Error" in called_args["error"]
        assert called_args["trace_id"] == "test_fail_trace"
