"""
Unit tests for predictive_service.predict_impact()

The service is a pure function — all memory retrieval is the caller's
responsibility. Tests pass historical_context directly; no DB or Chroma
connections are needed.

Expected total: 6 new tests → 27 passing overall (21 existing + 6 new).
"""
import pytest
from app.services.predictive_service import predict_impact

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_incident(incident_type: str = "water_pressure_drop", severity: str = "critical") -> dict:
    return {"type": incident_type, "severity": severity}


def _hist_record(
    residents: float = 300,
    duration: float = 5.0,
    cost: float = 12000,
    escalation: float = 0.7,
) -> dict:
    return {
        "affected_residents": residents,
        "repair_duration_hours": duration,
        "repair_cost": cost,
        "escalation_probability": escalation,
    }


# ---------------------------------------------------------------------------
# Case 1 — No historical incidents
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_no_historical_incidents():
    """When history is empty the engine falls back to severity heuristics.
    Confidence should be exactly 0.30 (base value with 0 history records).
    """
    prediction = await predict_impact(
        incident_event=_make_incident(severity="critical"),
        historical_context=[],
    )

    assert prediction["confidence_score"] == 0.30
    # Should use heuristic defaults for critical severity
    assert prediction["predicted_residents"] == 350
    assert prediction["predicted_outage_hrs"] == 24.0
    assert prediction["estimated_repair_cost"] == 15000.0
    assert "No historical incidents found" in prediction["reasoning"]


# ---------------------------------------------------------------------------
# Case 2 — One historical incident
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_one_historical_incident():
    """With exactly 1 historical record, confidence = 0.30 + 0.12*1 = 0.42."""
    history = [_hist_record(residents=300, duration=6.0, cost=13000, escalation=0.75)]

    prediction = await predict_impact(
        incident_event=_make_incident(severity="high"),
        historical_context=history,
    )

    assert prediction["confidence_score"] == pytest.approx(0.42, abs=1e-9)
    assert prediction["predicted_residents"] == 300
    assert prediction["predicted_outage_hrs"] == pytest.approx(6.0, abs=1e-9)
    assert prediction["estimated_repair_cost"] == pytest.approx(13000.0, abs=1e-9)
    assert "1 similar historical incidents" in prediction["reasoning"]


# ---------------------------------------------------------------------------
# Case 3 — Multiple historical incidents (5 records)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_multiple_historical_incidents():
    """With 5 historical records, confidence = min(0.95, 0.30 + 0.12*5) = 0.90."""
    history = [_hist_record(residents=200 + i * 20, duration=4.0 + i, cost=10000 + i * 500) for i in range(5)]

    prediction = await predict_impact(
        incident_event=_make_incident(severity="medium"),
        historical_context=history,
    )

    assert prediction["confidence_score"] == pytest.approx(0.90, abs=1e-9)
    assert "5 similar historical incidents" in prediction["reasoning"]
    # Verify averages are used (not heuristic defaults)
    expected_residents = int(sum(200 + i * 20 for i in range(5)) / 5)  # 240
    assert prediction["predicted_residents"] == expected_residents


# ---------------------------------------------------------------------------
# Case 4 — Memory retrieval unavailable (exception from caller)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_memory_retrieval_unavailable():
    """When the caller can't fetch history it passes [] — engine must not crash
    and must return a complete prediction dict with all required keys.
    """
    prediction = await predict_impact(
        incident_event=_make_incident(severity="high"),
        historical_context=[],   # simulates retrieval failure handled by caller
    )

    required_keys = {
        "predicted_residents",
        "predicted_outage_hrs",
        "predicted_severity",
        "escalation_probability",
        "estimated_repair_cost",
        "estimated_contractor_cost",
        "resource_requirements",
        "sla_breach_risk",
        "time_to_resolution_risk",
        "confidence_score",
        "reasoning",
        "historical_evidence",
    }
    assert required_keys.issubset(prediction.keys())
    # Graceful degradation: should still return heuristic values
    assert prediction["predicted_residents"] == 180   # high severity default


# ---------------------------------------------------------------------------
# Case 5 — Confidence score always between 0 and 1
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_confidence_score_bounds():
    """confidence_score must be in [0, 1] for every possible history size
    including the capped-at-0.95 case with many records.
    """
    for n_records in (0, 1, 3, 5, 10, 20, 100):
        history = [_hist_record()] * n_records
        prediction = await predict_impact(
            incident_event=_make_incident(severity="medium"),
            historical_context=history,
        )
        score = prediction["confidence_score"]
        assert 0.0 <= score <= 1.0, f"confidence_score={score} out of bounds for {n_records} records"


# ---------------------------------------------------------------------------
# Case 6 — Invalid / missing severity must not crash
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("severity", [None, "", "unknown_severity", "CRITICAL", "HIGH"])
async def test_invalid_severity_does_not_crash(severity):
    """The engine must handle unknown or missing severity values gracefully,
    falling back to 'medium' heuristics without raising an exception.
    """
    incident = {"type": "power_outage", "severity": severity}
    prediction = await predict_impact(incident_event=incident, historical_context=[])

    # Must not raise; must return the complete response shape
    assert "confidence_score" in prediction
    assert "predicted_residents" in prediction
    assert 0.0 <= prediction["confidence_score"] <= 1.0
