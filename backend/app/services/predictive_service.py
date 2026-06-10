"""Predictive Impact Service

Lightweight rule-based predictive engine that uses historical memories
to produce impact and cost predictions. This is intentionally simple and
deterministic so it can be unit-tested and iterated on.
"""
from typing import Any, Dict, List
from statistics import mean
from app.core.logging import get_logger

logger = get_logger("predictive_service")


async def predict_impact(incident_event: Dict[str, Any], sensor_data: Dict[str, Any], k: int = 5) -> Dict[str, Any]:
    """Return a dict of predictions for the given incident.

    - `incident_event` may contain `type`, `severity`, and other metadata.
    - `sensor_data` contains the infrastructure context (tower id, etc).

    The implementation queries the memory service for similar incidents
    and falls back to simple heuristics when no history is available.
    """
    # Lazy import to avoid heavy dependencies at module import time
    try:
        from app.services import memory_service
    except Exception:
        memory_service = None

    incident_type = (incident_event or {}).get("type") or (incident_event or {}).get("incident_type")
    severity = (incident_event or {}).get("severity") or "medium"

    # Default heuristics
    severity_defaults = {
        "critical": {"residents": 350, "outage_hrs": 24, "base_cost": 15000, "escalation": 0.9},
        "high": {"residents": 180, "outage_hrs": 8, "base_cost": 8000, "escalation": 0.6},
        "medium": {"residents": 90, "outage_hrs": 4, "base_cost": 4000, "escalation": 0.3},
        "low": {"residents": 25, "outage_hrs": 1, "base_cost": 1500, "escalation": 0.1},
    }

    default = severity_defaults.get(severity, severity_defaults["medium"])

    history: List[Dict[str, Any]] = []
    try:
        if memory_service is not None and incident_type:
            history = await memory_service.retrieve_similar_incidents({"incident_type": incident_type}, k=k)
            history = history or []
    except Exception as e:
        logger.warning("Predictive service: memory retrieval failed", error=str(e))
        history = []

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

    residents_hist = _get_vals("affected_residents")
    duration_hist = _get_vals("repair_duration_hours")
    cost_hist = _get_vals("repair_cost")

    predicted_residents = int(mean(residents_hist)) if residents_hist else default["residents"]
    predicted_outage_hrs = float(mean(duration_hist)) if duration_hist else float(default["outage_hrs"])
    estimated_repair_cost = float(mean(cost_hist)) if cost_hist else float(default["base_cost"])

    # Contractor cost: heuristic - slightly above repair cost to include margins
    estimated_contractor_cost = round(estimated_repair_cost * 1.15, 2)

    # Escalation probability: from history or severity default
    escalation_prob = mean(_get_vals("escalation_probability")) if _get_vals("escalation_probability") else default["escalation"]

    # Simple SLA risk: if outage hours > threshold, risk increases
    sla_threshold = 6.0 if severity in ("high", "critical") else 12.0
    sla_breach_risk = min(0.99, max(0.0, (predicted_outage_hrs - sla_threshold) / max(1.0, sla_threshold)))

    # Time-to-resolution risk: modeled as normalized outage hours
    time_to_resolution_risk = min(0.99, predicted_outage_hrs / max(1.0, predicted_outage_hrs + 4.0))

    # Confidence: more history -> higher confidence
    hist_count = len(history)
    confidence = min(0.95, 0.3 + 0.12 * hist_count)

    reasoning_parts = []
    if hist_count:
        reasoning_parts.append(f"Used {hist_count} similar historical incidents")
    else:
        reasoning_parts.append("No historical incidents found; used severity heuristics")

    reasoning_parts.append(f"Severity: {severity}")

    prediction = {
        "predicted_residents": predicted_residents,
        "predicted_outage_hrs": round(predicted_outage_hrs, 2),
        "predicted_severity": severity,
        "escalation_probability": round(float(escalation_prob), 2),
        "estimated_repair_cost": round(float(estimated_repair_cost), 2),
        "estimated_contractor_cost": float(estimated_contractor_cost),
        "resource_requirements": {"crew": max(1, int(predicted_residents // 50)), "special_equipment": []},
        "sla_breach_risk": round(float(sla_breach_risk), 3),
        "time_to_resolution_risk": round(float(time_to_resolution_risk), 3),
        "confidence_score": round(float(confidence), 2),
        "reasoning": "; ".join(reasoning_parts),
        "historical_evidence": history,
    }

    logger.info("Predictive impact generated", **{
        "predicted_residents": prediction["predicted_residents"],
        "predicted_outage_hrs": prediction["predicted_outage_hrs"],
        "confidence": prediction["confidence_score"],
    })

    return prediction
