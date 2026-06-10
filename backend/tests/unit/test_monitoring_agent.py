"""
Tests for MonitoringAgent anomaly detection logic.
"""
import pytest
import asyncio
from app.agents.monitoring import monitoring_agent
from app.agents.state import ASIPState


def make_state(sensor_type: str, value: float, tower_id: str = "00000000-0000-0000-0000-000000000001") -> ASIPState:
    return ASIPState(
        incident_id="test-001",
        sensor_data={"tower_id": tower_id, "sensor_type": sensor_type, "value": value, "unit": "bar"},
        incident_event=None,
        diagnosis=None,
        impact=None,
        contractor_recommendation=None,
        notifications=None,
        final_report=None,
        error=None,
        next="monitoring_agent",
    )


@pytest.mark.asyncio
async def test_critical_water_pressure_detected():
    state = make_state("water_pressure", 0.3)
    result = await monitoring_agent(state)
    assert result["incident_event"] is not None
    assert result["incident_event"]["type"] == "water_pressure_drop"
    assert result["incident_event"]["severity"] == "critical"
    assert result["next"] == "infrastructure_agent"


@pytest.mark.asyncio
async def test_high_water_pressure_detected():
    state = make_state("water_pressure", 0.8)
    result = await monitoring_agent(state)
    assert result["incident_event"] is not None
    assert result["incident_event"]["severity"] == "high"


@pytest.mark.asyncio
async def test_normal_water_pressure_no_incident():
    state = make_state("water_pressure", 3.5)
    result = await monitoring_agent(state)
    assert result["incident_event"] is None
    assert result["next"] == "__end__"


@pytest.mark.asyncio
async def test_power_outage_detected():
    state = make_state("power_consumption", 0.0)
    result = await monitoring_agent(state)
    assert result["incident_event"]["type"] == "power_outage"
    assert result["incident_event"]["severity"] == "critical"


@pytest.mark.asyncio
async def test_tank_overflow_detected():
    state = make_state("tank_level", 97.0)
    result = await monitoring_agent(state)
    assert result["incident_event"]["type"] == "tank_overflow"
    assert result["incident_event"]["severity"] == "critical"


@pytest.mark.asyncio
async def test_water_shortage_detected():
    state = make_state("tank_level", 4.0)
    result = await monitoring_agent(state)
    assert result["incident_event"]["type"] == "water_shortage"
    assert result["incident_event"]["severity"] == "critical"


@pytest.mark.asyncio
async def test_confidence_range():
    state = make_state("water_pressure", 0.3)
    result = await monitoring_agent(state)
    confidence = result["incident_event"]["confidence"]
    assert 0.0 <= confidence <= 1.0
