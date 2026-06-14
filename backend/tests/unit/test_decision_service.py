"""
Unit tests for decision_service.make_decision()

The service is a pure async function — no DB, no Chroma, no LLM.
All tests pass inputs directly; zero mocking of infrastructure needed.

Target: 6 new tests → ≥37 passing overall.
"""
import pytest
from app.services.decision_service import make_decision

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_incident(severity: str = "critical", incident_type: str = "water_pressure_drop") -> dict:
    return {"type": incident_type, "severity": severity}


def _make_prediction(
    predicted_residents: int = 350,
    predicted_outage_hrs: float = 24.0,
    escalation_probability: float = 0.9,
    sla_breach_risk: float = 0.8,
    confidence_score: float = 0.85,
) -> dict:
    return {
        "predicted_residents":    predicted_residents,
        "predicted_outage_hrs":   predicted_outage_hrs,
        "escalation_probability": escalation_probability,
        "sla_breach_risk":        sla_breach_risk,
        "confidence_score":       confidence_score,
    }


def _make_contractor(name: str = "FastFix Ltd") -> dict:
    return {"name": name, "contractor_name": name, "final_score": 0.92}


# ---------------------------------------------------------------------------
# Test 1 — Critical incident → escalation = True
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_critical_incident_triggers_escalation():
    decision = await make_decision(
        incident_event=_make_incident(severity="critical"),
        impact_prediction=_make_prediction(),
        contractor_candidates=[_make_contractor()],
    )
    assert decision["requires_immediate_escalation"] is True
    assert decision["should_notify_residents"] is True
    assert decision["notification_priority"] == "critical"


# ---------------------------------------------------------------------------
# Test 2 — Low severity → escalation = False
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_low_severity_no_escalation():
    decision = await make_decision(
        incident_event=_make_incident(severity="low"),
        impact_prediction=_make_prediction(
            predicted_residents=10,
            predicted_outage_hrs=1.0,
            escalation_probability=0.05,
            sla_breach_risk=0.0,
            confidence_score=0.3,
        ),
        contractor_candidates=[],
    )
    assert decision["requires_immediate_escalation"] is False
    assert decision["should_activate_backup_system"] is False


# ---------------------------------------------------------------------------
# Test 3 — No contractor candidates → auto_dispatch = False
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_no_contractors_no_auto_dispatch():
    decision = await make_decision(
        incident_event=_make_incident(severity="critical"),
        impact_prediction=_make_prediction(),
        contractor_candidates=[],   # empty list
    )
    assert decision["auto_dispatch_contractor"] is False
    assert decision["recommended_contractor"] is None


# ---------------------------------------------------------------------------
# Test 4 — High confidence + many residents → notify_residents = True
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_high_confidence_many_residents_triggers_notification():
    decision = await make_decision(
        incident_event=_make_incident(severity="medium"),
        impact_prediction=_make_prediction(
            predicted_residents=250,   # above 100 threshold
            confidence_score=0.88,
        ),
        contractor_candidates=[],
    )
    assert decision["should_notify_residents"] is True


# ---------------------------------------------------------------------------
# Test 5 — Low risk incident → backup system NOT activated
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_low_risk_no_backup_activation():
    decision = await make_decision(
        incident_event=_make_incident(severity="medium"),
        impact_prediction=_make_prediction(
            predicted_outage_hrs=2.0,   # below 6h backup threshold
            escalation_probability=0.1,
            sla_breach_risk=0.0,
        ),
        contractor_candidates=[],
    )
    assert decision["should_activate_backup_system"] is False


# ---------------------------------------------------------------------------
# Test 6 — All inputs None / missing → graceful fallback, no crash
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_missing_inputs_graceful_fallback():
    """All inputs are None or empty — engine must not crash and must return
    a complete dict with all required keys."""
    decision = await make_decision(
        incident_event=None,
        impact_prediction=None,
        contractor_candidates=None,
    )

    required_keys = {
        "requires_immediate_escalation",
        "should_notify_residents",
        "notification_priority",
        "should_activate_backup_system",
        "auto_dispatch_contractor",
        "recommended_contractor",
        "estimated_risk_score",
        "decision_reasoning",
    }
    assert required_keys.issubset(decision.keys())
    assert 0.0 <= decision["estimated_risk_score"] <= 1.0
    assert isinstance(decision["decision_reasoning"], str)
