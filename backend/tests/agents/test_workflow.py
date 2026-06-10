"""
Integration test: full LangGraph workflow with mocked LLM.
Tests the graph executes all nodes and returns a FinalReport.
"""
import pytest
import uuid
from unittest.mock import AsyncMock, patch
from app.agents.graph import build_graph
from app.agents.state import ASIPState


MOCK_DIAGNOSIS = {
    "probable_cause": "Booster pump motor failure due to single-phase fault",
    "recommended_action": "Replace pump motor, check electrical connections",
    "confidence": 0.92,
    "retrieved_context": "Section 2.1: Pump failure causes pressure drop",
}

MOCK_CONTRACTOR = {
    "contractor_id": "c1",
    "contractor_name": "AquaFix Pro",
    "estimated_cost": 12500.0,
    "estimated_time_hrs": 5.0,
    "selection_reasoning": "Best rating and specialization match for water incidents",
}

MOCK_NOTIFICATIONS = [
    {
        "channel": "email",
        "subject": "Water Pressure Alert",
        "content": "Dear resident, water pressure is low. Our team is working on it.",
        "recipient_type": "residents",
    }
]

MOCK_FINAL_REPORT = {
    "incident_summary": "Critical water pressure drop detected in Tower A",
    "root_cause": "Booster pump motor failure",
    "impact_summary": "350 residents affected",
    "action_plan": "1. Replace pump motor 2. Test pressure 3. Notify residents",
    "estimated_resolution_hrs": 5.0,
    "priority": "critical",
}


@pytest.mark.asyncio
async def test_full_workflow_critical_incident():
    """Test that a critical sensor reading triggers the full workflow."""
    graph = build_graph()

    initial_state: ASIPState = {
        "incident_id": str(uuid.uuid4()),
        "sensor_data": {
            "tower_id": "00000000-0000-0000-0000-000000000001",
            "sensor_type": "water_pressure",
            "value": 0.3,
            "unit": "bar",
            "timestamp": "2026-06-09T00:00:00Z",
        },
        "incident_event": None,
        "diagnosis": None,
        "impact": None,
        "contractor_recommendation": None,
        "notifications": None,
        "final_report": None,
        "error": None,
        "next": "monitoring_agent",
    }

    with (
        patch("app.agents.infrastructure.get_llm") as mock_infra_llm,
        patch("app.agents.infrastructure._retrieve_context", return_value="Pump failure context"),
        patch("app.agents.contractor.get_llm") as mock_contractor_llm,
        patch("app.agents.communication.get_llm") as mock_comm_llm,
        patch("app.agents.supervisor.get_llm") as mock_sup_llm,
    ):
        # Mock LLM chains to return structured outputs
        for mock_llm, return_val in [
            (mock_infra_llm, MOCK_DIAGNOSIS),
            (mock_contractor_llm, MOCK_CONTRACTOR),
            (mock_comm_llm, MOCK_NOTIFICATIONS),
            (mock_sup_llm, MOCK_FINAL_REPORT),
        ]:
            mock_instance = mock_llm.return_value
            mock_chain = AsyncMock(return_value=return_val)
            mock_instance.__or__ = lambda self, other: mock_chain

        final_state = await graph.ainvoke(initial_state)

    # Monitoring should have detected the incident
    assert final_state["incident_event"] is not None
    assert final_state["incident_event"]["type"] == "water_pressure_drop"
    assert final_state["incident_event"]["severity"] == "critical"

    # Impact should be calculated
    assert final_state["impact"] is not None
    assert final_state["impact"]["estimated_residents"] > 0


@pytest.mark.asyncio
async def test_normal_reading_ends_graph():
    """Test that a normal sensor reading ends the graph early (no incident)."""
    graph = build_graph()

    initial_state: ASIPState = {
        "incident_id": str(uuid.uuid4()),
        "sensor_data": {
            "tower_id": "00000000-0000-0000-0000-000000000001",
            "sensor_type": "water_pressure",
            "value": 3.5,
            "unit": "bar",
            "timestamp": "2026-06-09T00:00:00Z",
        },
        "incident_event": None,
        "diagnosis": None,
        "impact": None,
        "contractor_recommendation": None,
        "notifications": None,
        "final_report": None,
        "error": None,
        "next": "monitoring_agent",
    }

    final_state = await graph.ainvoke(initial_state)

    # No incident should be detected
    assert final_state["incident_event"] is None
    assert final_state["diagnosis"] is None
    assert final_state["final_report"] is None
