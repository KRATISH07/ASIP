"""
Unit tests for ImpactAnalysisAgent.
"""
import pytest
from app.agents.impact_analysis import impact_analysis_agent
from app.agents.state import ASIPState


def make_state(severity: str, confidence: float = 0.9) -> ASIPState:
    return ASIPState(
        incident_id="test-impact-001",
        sensor_data={"tower_id": "00000000-0000-0000-0000-000000000001", "sensor_type": "water_pressure", "value": 0.3, "unit": "bar"},
        incident_event={"type": "water_pressure_drop", "severity": severity, "confidence": confidence, "description": "Test", "timestamp": "2026-06-09T00:00:00Z"},
        diagnosis=None,
        impact=None,
        contractor_recommendation=None,
        notifications=None,
        final_report=None,
        error=None,
        next="impact_agent",
    )


@pytest.mark.asyncio
async def test_critical_impact():
    state = make_state("critical")
    result = await impact_analysis_agent(state)
    assert result["impact"] is not None
    assert result["impact"]["estimated_residents"] == 350
    assert result["impact"]["priority"] in ["high", "critical"]


@pytest.mark.asyncio
async def test_low_impact():
    state = make_state("low", confidence=0.5)
    result = await impact_analysis_agent(state)
    assert result["impact"]["estimated_residents"] == 25
    assert result["impact"]["priority"] in ["low", "medium"]


@pytest.mark.asyncio
async def test_impact_keys_present():
    state = make_state("high")
    result = await impact_analysis_agent(state)
    impact = result["impact"]
    assert "affected_towers" in impact
    assert "affected_apartments" in impact
    assert "estimated_residents" in impact
    assert "severity_score" in impact
    assert "priority" in impact


@pytest.mark.asyncio
async def test_next_node_is_contractor():
    state = make_state("medium")
    result = await impact_analysis_agent(state)
    assert result["next"] == "contractor_agent"
