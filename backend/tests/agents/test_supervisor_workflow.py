"""
Tests for Supervisor-driven dynamic orchestration workflow.
"""
import pytest
import uuid
from unittest.mock import AsyncMock, patch

from app.agents.graph import build_graph


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
async def test_water_incident_supervisor_routing():
    graph = build_graph()

    initial_state = {
        "incident_id": str(uuid.uuid4()),
        "sensor_data": {
            "tower_id": "00000000-0000-0000-0000-000000000001",
            "sensor_type": "water_pressure",
            "value": 0.3,
            "unit": "bar",
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

    # Supervisor should have selected the full water workflow (including V4 decision_agent)
    assert final_state.get("selected_agents") == [
        "infrastructure_agent",
        "impact_agent",
        "contractor_agent",
        "communication_agent",
        "decision_agent",
    ]
    assert set(final_state.get("completed_agents", [])) >= set(final_state.get("selected_agents", []))
    assert final_state.get("final_report") is not None


@pytest.mark.asyncio
async def test_contractor_only_request():
    graph = build_graph()

    initial_state = {
        "incident_id": str(uuid.uuid4()),
        "sensor_data": {
            "tower_id": "00000000-0000-0000-0000-000000000001",
            "sensor_type": "water_pressure",
            "value": 0.3,
            "unit": "bar",
            "request_type": "contractor_review",
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
        # Provide responses, contractor will be used
        mock_instance = mock_contractor_llm.return_value
        mock_chain = AsyncMock(return_value=MOCK_CONTRACTOR)
        mock_instance.__or__ = lambda self, other: mock_chain

        # Supervisor LLM
        mock_sup = mock_sup_llm.return_value
        mock_chain_sup = AsyncMock(return_value=MOCK_FINAL_REPORT)
        mock_sup.__or__ = lambda self, other: mock_chain_sup

        final_state = await graph.ainvoke(initial_state)

    # contractor_review also gets decision_agent in V4
    assert final_state.get("selected_agents") == ["contractor_agent", "decision_agent"]
    assert "contractor_agent" in final_state.get("completed_agents", [])
    assert final_state.get("final_report") is not None


@pytest.mark.asyncio
async def test_communication_only_request():
    graph = build_graph()

    initial_state = {
        "incident_id": str(uuid.uuid4()),
        "sensor_data": {
            "tower_id": "00000000-0000-0000-0000-000000000001",
            "sensor_type": "water_pressure",
            "value": 0.3,
            "unit": "bar",
            "request_type": "communication_only",
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
        patch("app.agents.communication.get_llm") as mock_comm_llm,
        patch("app.agents.supervisor.get_llm") as mock_sup_llm,
    ):
        mock_comm = mock_comm_llm.return_value
        mock_chain_comm = AsyncMock(return_value=MOCK_NOTIFICATIONS)
        mock_comm.__or__ = lambda self, other: mock_chain_comm

        mock_sup = mock_sup_llm.return_value
        mock_chain_sup = AsyncMock(return_value=MOCK_FINAL_REPORT)
        mock_sup.__or__ = lambda self, other: mock_chain_sup

        final_state = await graph.ainvoke(initial_state)

    assert final_state.get("selected_agents") == ["communication_agent"]
    assert "communication_agent" in final_state.get("completed_agents", [])
    assert final_state.get("final_report") is not None
