"""Integration-style unit tests to verify agents use memory retrieval."""
import pytest
import uuid
from unittest.mock import AsyncMock, patch

from app.agents.infrastructure import infrastructure_agent
from app.agents.contractor import contractor_agent


@pytest.mark.asyncio
async def test_infrastructure_uses_memory(monkeypatch):
    state = {
        "incident_id": str(uuid.uuid4()),
        "sensor_data": {"tower_id": "t1", "sensor_type": "water_pressure", "value": 0.3},
        "incident_event": {"type": "water_pressure_drop", "severity": "critical"},
        "diagnosis": None,
        "impact": None,
        "contractor_recommendation": None,
        "notifications": None,
        "final_report": None,
        "error": None,
        "next": "infrastructure_agent",
    }

    # Patch memory retrieval to return a sample memory
    sample_memories = [{"resolution_summary": "Replaced pump", "contractor_used": "AquaFix"}]
    monkeypatch.setattr("app.services.memory_service.retrieve_similar_incidents", AsyncMock(return_value=sample_memories))

    with patch("app.agents.infrastructure.get_llm") as mock_llm:
        mock_instance = mock_llm.return_value
        mock_chain = AsyncMock(return_value={"probable_cause": "pump fail", "recommended_action": "replace", "confidence": 0.9})
        mock_instance.__or__ = lambda self, other: mock_chain

        res = await infrastructure_agent(state)

        # Ensure LLM chain was invoked and that the provided context included memory summary
        assert mock_chain.await_count == 1
        called_args = mock_chain.await_args[0][0]
        assert "context" in called_args
        assert "Replaced pump" in called_args["context"]


@pytest.mark.asyncio
async def test_contractor_uses_memory(monkeypatch):
    state = {
        "incident_id": str(uuid.uuid4()),
        "sensor_data": {"tower_id": "t1"},
        "incident_event": {"type": "water_pressure_drop", "severity": "critical"},
        "impact": {"estimated_residents": 100, "priority": "high"},
        "contractor_recommendation": None,
        "notifications": None,
        "final_report": None,
        "error": None,
        "next": "contractor_agent",
    }

    sample_memories = [{"resolution_summary": "Replaced pump", "contractor_used": "AquaFix"}]
    monkeypatch.setattr("app.services.memory_service.retrieve_similar_incidents", AsyncMock(return_value=sample_memories))

    with patch("app.agents.contractor.get_llm") as mock_llm:
        mock_instance = mock_llm.return_value
        mock_chain = AsyncMock(return_value={"contractor_name": "AquaFix Pro", "estimated_cost": 8000.0, "estimated_time_hrs": 2.0})
        mock_instance.__or__ = lambda self, other: mock_chain

        res = await contractor_agent(state)

        # Contractor chain should be awaited and receive historical incidents in input
        assert mock_chain.await_count == 1
        called_args = mock_chain.await_args[0][0]
        assert "historical_incidents" in called_args
        assert "Replaced pump" in called_args["historical_incidents"]
