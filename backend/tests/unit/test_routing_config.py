import pytest
from app.routing_config import resolve_agents

def test_resolve_low_severity():
    """All low severity incidents should only run communication and decision agents."""
    agents, reason = resolve_agents(incident_type="water_pressure_drop", severity="low")
    assert agents == ["communication_agent", "decision_agent"]
    assert "Low severity" in reason


def test_resolve_request_type_override():
    """Explicit request types should resolve directly to override lists."""
    agents, reason = resolve_agents(
        incident_type="power_outage",
        severity="critical",
        request_type="contractor_review",
    )
    assert agents == ["contractor_agent", "decision_agent"]
    assert "Explicit contractor review" in reason

    agents, reason = resolve_agents(
        incident_type="water_shortage",
        severity="high",
        request_type="communication_only",
    )
    assert agents == ["communication_agent"]
    assert "Explicit communication-only" in reason


def test_resolve_water_incidents():
    """Water incident types should resolve to full pipeline for non-low severity."""
    agents, reason = resolve_agents(incident_type="water_pressure_drop", severity="high")
    assert len(agents) == 5
    assert "infrastructure_agent" in agents
    assert "contractor_agent" in agents

    agents, reason = resolve_agents(incident_type="water_shortage", severity="critical")
    assert len(agents) == 5
    assert "impact_agent" in agents


def test_resolve_power_incidents():
    """Power incident types should resolve to full pipeline for non-low severity."""
    agents, reason = resolve_agents(incident_type="power_outage", severity="medium")
    assert len(agents) == 5
    assert "contractor_agent" in agents


def test_resolve_unknown_incident_type():
    """Unknown incident types should fall back to full pipeline default rule."""
    agents, reason = resolve_agents(incident_type="gas_leak", severity="medium")
    assert len(agents) == 5
    assert "Default: unknown incident type" in reason
