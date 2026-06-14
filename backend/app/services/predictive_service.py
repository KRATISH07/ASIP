"""Predictive Impact Service

Lightweight rule-based predictive engine that uses historical memories
to produce impact and cost predictions. This is intentionally simple and
deterministic so it can be unit-tested and iterated on.

IMPORTANT: This service is a pure function — it does NOT internally fetch
memory or touch any DB session. Callers are responsible for retrieving
historical context and passing it in via `historical_context`.
This avoids async event-loop bugs in the memory layer.
"""
from typing import Any, Dict, List, Optional
from statistics import mean
from app.core.logging import get_logger

logger = get_logger("predictive_service")


async def predict_impact(
    incident_event: Dict[str, Any],
    sensor_data: Optional[Dict[str, Any]] = None,
    historical_context: Optional[List[Dict[str, Any]]] = None,
    k: int = 5,
    correction_factors: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Return a dict of predictions for the given incident.

    Parameters
    ----------
    incident_event:
        Dict containing at minimum ``type`` and ``severity``.
    sensor_data:
        Optional infrastructure context (tower id, etc.).
    historical_context:
        Pre-fetched list of similar historical incident dicts.
    k:
        Kept for backwards-compatible signature.
    correction_factors:
        Optional output of learning_service.compute_correction_factors().
        When provided, outage and cost predictions are scaled by the
        computed correction multipliers and confidence is adapted from
        historical accuracy rather than the count-based heuristic.
        When None (default), behavior is identical to V3.
    """
    incident_event = incident_event or {}
    sensor_data = sensor_data or {}
    history: List[Dict[str, Any]] = historical_context if historical_context is not None else []

    incident_type = incident_event.get("type") or incident_event.get("incident_type")
    severity = incident_event.get("severity") or "medium"

    # Normalise unknown severity values to "medium" to avoid KeyError
    severity_defaults = {
        "critical": {"residents": 350, "outage_hrs": 24, "base_cost": 15000, "escalation": 0.9},
        "high":     {"residents": 180, "outage_hrs": 8,  "base_cost": 8000,  "escalation": 0.6},
        "medium":   {"residents": 90,  "outage_hrs": 4,  "base_cost": 4000,  "escalation": 0.3},
        "low":      {"residents": 25,  "outage_hrs": 1,  "base_cost": 1500,  "escalation": 0.1},
    }
    default = severity_defaults.get(severity, severity_defaults["medium"])

    # Helpers to extract numeric fields from history
    def _get_vals(key: str) -> List[float]:
        vals = []
        for h in history:
            v = h.get(key)
            try:
                if v is not None:
                    vals.append(float(v))
            except Exception:
                continue
        return vals

    residents_hist  = _get_vals("affected_residents")
    duration_hist   = _get_vals("repair_duration_hours")
    cost_hist       = _get_vals("repair_cost")
    escalation_vals = _get_vals("escalation_probability")

    predicted_residents      = int(mean(residents_hist))      if residents_hist  else default["residents"]
    predicted_outage_hrs     = float(mean(duration_hist))     if duration_hist   else float(default["outage_hrs"])
    estimated_repair_cost    = float(mean(cost_hist))         if cost_hist       else float(default["base_cost"])
    escalation_prob          = mean(escalation_vals)          if escalation_vals else default["escalation"]

    # Contractor cost: heuristic — slightly above repair cost to include margins
    estimated_contractor_cost = round(estimated_repair_cost * 1.15, 2)

    # SLA risk: if outage hours > threshold, risk increases
    sla_threshold = 6.0 if severity in ("high", "critical") else 12.0
    sla_breach_risk = min(0.99, max(0.0, (predicted_outage_hrs - sla_threshold) / max(1.0, sla_threshold)))

    # Time-to-resolution risk: normalized outage hours
    time_to_resolution_risk = min(0.99, predicted_outage_hrs / max(1.0, predicted_outage_hrs + 4.0))

    # Confidence: use empirically adapted value from learning engine when available.
    # Otherwise fall back to count-based heuristic (preserved for backward compat).
    hist_count = len(history)
    cf = correction_factors or {}
    adapted_confidence = cf.get("adapted_confidence")  # None when < MIN_SAMPLES

    # Apply learning corrections when the engine has enough data
    if cf.get("correction_applied"):
        raw_outage = predicted_outage_hrs
        raw_cost   = estimated_repair_cost
        predicted_outage_hrs  = round(predicted_outage_hrs  * cf.get("outage_correction_factor", 1.0), 2)
        estimated_repair_cost = round(estimated_repair_cost * cf.get("cost_correction_factor",   1.0), 2)
        estimated_contractor_cost = round(estimated_repair_cost * 1.15, 2)
        logger.info(
            "Learning correction applied",
            outage_before=raw_outage,
            outage_after=predicted_outage_hrs,
            cost_before=raw_cost,
            cost_after=estimated_repair_cost,
            outage_cf=cf.get("outage_correction_factor"),
            cost_cf=cf.get("cost_correction_factor"),
        )

    if adapted_confidence is not None:
        confidence = adapted_confidence
    else:
        # V3 fallback: more history → higher confidence (fake but consistent)
        confidence = min(0.95, 0.30 + 0.12 * hist_count)

    reasoning_parts = []
    if hist_count:
        reasoning_parts.append(f"Used {hist_count} similar historical incidents")
    else:
        reasoning_parts.append("No historical incidents found; used severity heuristics")
    reasoning_parts.append(f"Severity: {severity}")

    prediction = {
        "predicted_residents":        predicted_residents,
        "predicted_outage_hrs":       round(predicted_outage_hrs, 2),
        "predicted_severity":         severity,
        "escalation_probability":     round(float(escalation_prob), 2),
        "estimated_repair_cost":      round(float(estimated_repair_cost), 2),
        "estimated_contractor_cost":  float(estimated_contractor_cost),
        "resource_requirements":      {
            "crew": max(1, int(predicted_residents // 50)),
            "special_equipment": [],
        },
        "sla_breach_risk":            round(float(sla_breach_risk), 3),
        "time_to_resolution_risk":    round(float(time_to_resolution_risk), 3),
        "confidence_score":           round(float(confidence), 2),
        "reasoning":                  "; ".join(reasoning_parts),
        "historical_evidence":        history,
    }

    logger.info(
        "Predictive impact generated",
        predicted_residents=prediction["predicted_residents"],
        predicted_outage_hrs=prediction["predicted_outage_hrs"],
        confidence=prediction["confidence_score"],
    )

    return prediction
