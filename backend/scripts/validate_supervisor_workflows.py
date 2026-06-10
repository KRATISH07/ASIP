"""
Run supervisor-driven workflows with mocked LLMs and print final states.

Usage: python scripts/validate_supervisor_workflows.py
"""
import asyncio
import json
import uuid
from unittest.mock import AsyncMock, patch

from app.agents.graph import build_graph


MOCK_DIAGNOSIS = {
    "probable_cause": "Booster pump motor failure",
    "recommended_action": "Replace pump motor",
    "confidence": 0.92,
    "retrieved_context": "Pump section",
}

MOCK_CONTRACTOR = {
    "contractor_id": "c1",
    "contractor_name": "AquaFix Pro",
    "estimated_cost": 12500.0,
    "estimated_time_hrs": 5.0,
    "selection_reasoning": "Best match",
}

MOCK_NOTIFICATIONS = [
    {"channel": "email", "subject": "Alert", "content": "Water low", "recipient_type": "residents"}
]

MOCK_SUPERVISOR = {
    "incident_summary": "Water pressure drop",
    "root_cause": "Booster pump motor failure",
    "impact_summary": "350 residents affected",
    "action_plan": "Replace pump motor",
    "estimated_resolution_hrs": 5.0,
    "priority": "critical",
}


async def run_scenario(name: str, initial_state: dict):
    graph = build_graph()

    with (
        patch("app.agents.infrastructure.get_llm") as mock_infra_llm,
        patch("app.agents.infrastructure._retrieve_context", return_value="Pump failure context"),
        patch("app.agents.contractor.get_llm") as mock_contractor_llm,
        patch("app.agents.communication.get_llm") as mock_comm_llm,
        patch("app.agents.supervisor.get_llm") as mock_sup_llm,
    ):
        # Infrastructure
        infra_inst = mock_infra_llm.return_value
        infra_chain = AsyncMock(return_value=MOCK_DIAGNOSIS)
        infra_inst.__or__ = lambda self, other: infra_chain

        # Contractor
        cont_inst = mock_contractor_llm.return_value
        cont_chain = AsyncMock(return_value=MOCK_CONTRACTOR)
        cont_inst.__or__ = lambda self, other: cont_chain

        # Communication
        comm_inst = mock_comm_llm.return_value
        comm_chain = AsyncMock(return_value=MOCK_NOTIFICATIONS)
        comm_inst.__or__ = lambda self, other: comm_chain

        # Supervisor
        sup_inst = mock_sup_llm.return_value
        sup_chain = AsyncMock(return_value=MOCK_SUPERVISOR)
        sup_inst.__or__ = lambda self, other: sup_chain

        final_state = await graph.ainvoke(initial_state)

    output = {
        "scenario": name,
        "input": initial_state,
        "selected_agents": final_state.get("selected_agents"),
        "execution_order": final_state.get("completed_agents"),
        "agent_outputs": final_state.get("agent_outputs"),
        "supervisor_decisions": final_state.get("supervisor_decisions"),
        "final_report": final_state.get("final_report"),
    }

    print(json.dumps(output, indent=2, default=str))


def main():
    scenarios = []

    # Water incident (critical)
    scenarios.append(("water_critical", {
        "incident_id": str(uuid.uuid4()),
        "sensor_data": {"tower_id": "t1", "sensor_type": "water_pressure", "value": 0.3, "unit": "bar"},
        "incident_event": None,
        "diagnosis": None,
        "impact": None,
        "contractor_recommendation": None,
        "notifications": None,
        "final_report": None,
        "error": None,
        "next": "monitoring_agent",
    }))

    # Electricity outage (power_consumption -> outage)
    scenarios.append(("power_outage", {
        "incident_id": str(uuid.uuid4()),
        "sensor_data": {"tower_id": "t1", "sensor_type": "power_consumption", "value": 0.0, "unit": "kW"},
        "incident_event": None,
        "diagnosis": None,
        "impact": None,
        "contractor_recommendation": None,
        "notifications": None,
        "final_report": None,
        "error": None,
        "next": "monitoring_agent",
    }))

    # Contractor-only request
    scenarios.append(("contractor_only", {
        "incident_id": str(uuid.uuid4()),
        "sensor_data": {"tower_id": "t1", "sensor_type": "water_pressure", "value": 0.3, "unit": "bar", "request_type": "contractor_review"},
        "incident_event": None,
        "diagnosis": None,
        "impact": None,
        "contractor_recommendation": None,
        "notifications": None,
        "final_report": None,
        "error": None,
        "next": "monitoring_agent",
    }))

    # Communication-only request
    scenarios.append(("communication_only", {
        "incident_id": str(uuid.uuid4()),
        "sensor_data": {"tower_id": "t1", "sensor_type": "water_pressure", "value": 0.3, "unit": "bar", "request_type": "communication_only"},
        "incident_event": None,
        "diagnosis": None,
        "impact": None,
        "contractor_recommendation": None,
        "notifications": None,
        "final_report": None,
        "error": None,
        "next": "monitoring_agent",
    }))

    loop = asyncio.get_event_loop()
    for name, state in scenarios:
        loop.run_until_complete(run_scenario(name, state))


if __name__ == "__main__":
    main()
