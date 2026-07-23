import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.idempotency import get_idempotency_cache
from app.api.incidents import ingest_sensor_data
from app.schemas.incident import SensorDataPayload


@pytest.mark.asyncio
async def test_idempotency_cache_logic():
    """Test standard core cache logic (set, get, expiration)."""
    import time
    cache = get_idempotency_cache()
    cache.clear()

    key = "test-key-1"
    response = {"data": "some_response"}

    assert cache.get(key) is None

    cache.set(key, response)
    assert cache.get(key) == response

    # Mock time to test expiration
    with patch("time.time", return_value=time.time() + 400):
        assert cache.get(key) is None  # should be expired (> 300s)


@pytest.mark.asyncio
async def test_api_endpoint_idempotency():
    """Test that FastAPI /incidents/sensor-data endpoint correctly deduplicates."""
    cache = get_idempotency_cache()
    cache.clear()

    # Mock user
    mock_user = MagicMock()

    # Mock WorkflowService to see how many times it gets called
    mock_service = MagicMock()
    mock_incident = MagicMock()
    mock_incident.id = "11111111-2222-3333-4444-555555555555"
    mock_incident.severity.value = "high"
    mock_service.process_sensor_data = AsyncMock(return_value=mock_incident)

    payload_dict = {
        "tower_id": "00000000-0000-0000-0000-000000000001",
        "sensor_type": "water_pressure",
        "value": 0.2,
        "unit": "bar",
        "timestamp": "2026-06-15T12:00:00Z",
        "idempotency_key": "unique-uuid-12345"
    }

    with patch("app.services.workflow_service.WorkflowService", return_value=mock_service):
        # First request
        payload = SensorDataPayload(**payload_dict)
        data1 = await ingest_sensor_data(
            payload=payload,
            background_tasks=MagicMock(),
            db=MagicMock(),
            current_user=mock_user
        )
        assert data1["incident_id"] == str(mock_incident.id)
        assert mock_service.process_sensor_data.call_count == 1

        # Second request with same idempotency key
        payload = SensorDataPayload(**payload_dict)
        data2 = await ingest_sensor_data(
            payload=payload,
            background_tasks=MagicMock(),
            db=MagicMock(),
            current_user=mock_user
        )
        assert data2 == data1
        # Service should STILL have only been called once!
        assert mock_service.process_sensor_data.call_count == 1

        # Third request with DIFFERENT key should run service again
        payload_dict["idempotency_key"] = "another-key"
        payload = SensorDataPayload(**payload_dict)
        data3 = await ingest_sensor_data(
            payload=payload,
            background_tasks=MagicMock(),
            db=MagicMock(),
            current_user=mock_user
        )
        assert mock_service.process_sensor_data.call_count == 2


@pytest.mark.asyncio
async def test_api_endpoint_production_async_execution():
    """Test that the production async path queues the background task and returns immediately."""
    from app.config import settings
    
    mock_user = MagicMock()
    mock_bg_tasks = MagicMock()
    
    payload_dict = {
        "tower_id": "00000000-0000-0000-0000-000000000001",
        "sensor_type": "water_pressure",
        "value": 0.2,
        "unit": "bar",
        "timestamp": "2026-06-15T12:00:00Z",
        "idempotency_key": "async-key-123"
    }
    
    # Force environment to production/development (non-testing) for this test
    import os
    with (
        patch.dict(os.environ, {"ASIP_FORCE_ASYNC": "true"}),
        patch("app.core.idempotency.get_idempotency_cache") as mock_cache
    ):
        mock_cache.return_value.get.return_value = None
        
        payload = SensorDataPayload(**payload_dict)
        response = await ingest_sensor_data(
            payload=payload,
            background_tasks=mock_bg_tasks,
            db=MagicMock(),
            current_user=mock_user
        )
        
        # Verify it returns immediately with queued status and pre-generated incident_id
        assert response["status"] == "queued"
        assert "incident_id" in response
        assert "accepted for background processing" in response["message"]
        
        # Verify background tasks added the job
        mock_bg_tasks.add_task.assert_called_once()
        called_args = mock_bg_tasks.add_task.call_args[0]
        # First arg should be the function
        assert called_args[0].__name__ == "_run_workflow_background"
        # Second arg should be the payload
        assert str(called_args[1]["tower_id"]) == "00000000-0000-0000-0000-000000000001"

