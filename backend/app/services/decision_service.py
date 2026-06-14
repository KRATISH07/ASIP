"""Autonomous Decision Engine Service

Pure rule-based function. No LLM, no DB, no Chroma.
Callers supply all context; this service only computes a decision.

Decision logic priority order:
  1. Compute risk score (composite of severity + prediction signals)
  2. Apply escalation rule
  3. Apply notification rule
  4. Apply backup system rule
  5. Apply auto-dispatch rule
  6. Build human-readable reasoning string
"""
from typing import Any, Dict, List, Optional
from app.core.logging import get_logger

logger = get_logger("decision_service")

# Severity weights used in risk score computation
_SEVERITY_WEIGHT: Dict[str, float] = {
    "critical": 1.00,
    "high":     0.75,
    "medium":   0.50,
    "low":      0.25,
}

# Thresholds
_ESCALATION_RISK_THRESHOLD   = 0.80   # risk_score above this → always escalate
_RESIDENT_NOTIFY_THRESHOLD   = 100    # predicted residents above this → notify
_BACKUP_OUTAGE_THRESHOLD_HRS = 6.0   # predicted outage above this → activate backup
_AUTO_DISPATCH_MIN_RISK      = 0.50   # risk_score above this → auto-dispatch


async def make_decision(
    incident_event: Dict[str, Any],
    impact_prediction: Dict[str, Any],
    contractor_candidates: List[Dict[str, Any]],
    historical_context: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Compute an autonomous decision for the given incident.

    Parameters
    ----------
    incident_event:
        Dict with at least ``type`` and ``severity``.
    impact_prediction:
        Output from ``predictive_service.predict_impact()`` —
        expects ``predicted_residents``, ``predicted_outage_hrs``,
        ``escalation_probability``, ``sla_breach_risk``, ``confidence_score``.
    contractor_candidates:
        Ranked list from ``contractor_service.rank_contractors()``.
        Used to check availability and pick a recommended contractor.
    historical_context:
        Pre-fetched similar incidents. Kept for future ML use; not used in
        the current rule engine.

    Returns
    -------
    dict with keys:
        requires_immediate_escalation, should_notify_residents,
        notification_priority, should_activate_backup_system,
        auto_dispatch_contractor, recommended_contractor,
        estimated_risk_score, decision_reasoning
    """
    incident_event       = incident_event or {}
    impact_prediction    = impact_prediction or {}
    contractor_candidates = contractor_candidates or []

    severity = (incident_event.get("severity") or "medium").lower()
    incident_type = incident_event.get("type") or "unknown"

    # ── Extract prediction signals ──────────────────────────────────────────
    predicted_residents  = float(impact_prediction.get("predicted_residents", 0) or 0)
    predicted_outage_hrs = float(impact_prediction.get("predicted_outage_hrs", 0) or 0)
    escalation_prob      = float(impact_prediction.get("escalation_probability", 0) or 0)
    sla_breach_risk      = float(impact_prediction.get("sla_breach_risk", 0) or 0)
    prediction_confidence = float(impact_prediction.get("confidence_score", 0.3) or 0.3)

    severity_weight = _SEVERITY_WEIGHT.get(severity, _SEVERITY_WEIGHT["medium"])

    # ── Risk score (0.0 – 1.0 composite) ───────────────────────────────────
    # Weights: severity 40%, escalation probability 30%, SLA risk 20%, confidence 10%
    estimated_risk_score = round(
        0.40 * severity_weight
        + 0.30 * escalation_prob
        + 0.20 * sla_breach_risk
        + 0.10 * prediction_confidence,
        3,
    )
    # Clamp to [0, 1]
    estimated_risk_score = min(1.0, max(0.0, estimated_risk_score))

    # ── Rule 1: Escalation ─────────────────────────────────────────────────
    requires_immediate_escalation = (
        severity == "critical"
        or estimated_risk_score >= _ESCALATION_RISK_THRESHOLD
    )

    # ── Rule 2: Resident notification ──────────────────────────────────────
    should_notify_residents = (
        severity in ("critical", "high")
        or predicted_residents >= _RESIDENT_NOTIFY_THRESHOLD
        or requires_immediate_escalation
    )

    # ── Rule 3: Notification priority mirrors incident severity ─────────────
    notification_priority = severity if should_notify_residents else "low"

    # ── Rule 4: Backup system activation ───────────────────────────────────
    should_activate_backup_system = (
        severity == "critical"
        and predicted_outage_hrs >= _BACKUP_OUTAGE_THRESHOLD_HRS
    )

    # ── Rule 5: Auto-dispatch contractor ───────────────────────────────────
    contractor_available = bool(contractor_candidates)
    auto_dispatch_contractor = (
        contractor_available
        and (
            severity in ("critical", "high")
            or estimated_risk_score >= _AUTO_DISPATCH_MIN_RISK
        )
    )

    # Recommended contractor: top of ranked list (or None)
    recommended_contractor: Optional[str] = None
    if contractor_candidates:
        top = contractor_candidates[0]
        if isinstance(top, dict):
            recommended_contractor = top.get("name") or top.get("contractor_name")

    # ── Build reasoning string ──────────────────────────────────────────────
    reasoning_parts: List[str] = [
        f"Incident: {incident_type} (severity={severity})",
        f"Risk score: {estimated_risk_score:.2f} "
        f"[severity={severity_weight}, escalation_prob={escalation_prob:.2f}, "
        f"sla_risk={sla_breach_risk:.2f}, confidence={prediction_confidence:.2f}]",
    ]

    if requires_immediate_escalation:
        reasoning_parts.append(
            "Escalation triggered: "
            + ("severity=critical" if severity == "critical" else f"risk_score={estimated_risk_score:.2f} ≥ {_ESCALATION_RISK_THRESHOLD}")
        )
    if should_notify_residents:
        reasoning_parts.append(
            f"Resident notification required: {int(predicted_residents)} predicted residents affected"
        )
    if should_activate_backup_system:
        reasoning_parts.append(
            f"Backup system activation required: predicted outage {predicted_outage_hrs:.1f}h ≥ {_BACKUP_OUTAGE_THRESHOLD_HRS}h threshold"
        )
    if auto_dispatch_contractor:
        reasoning_parts.append(
            f"Auto-dispatching contractor: {recommended_contractor or 'top candidate'}"
        )
    else:
        reasoning_parts.append(
            "Auto-dispatch skipped: "
            + ("no contractors available" if not contractor_available else "risk below threshold")
        )

    decision_reasoning = "; ".join(reasoning_parts)

    decision = {
        "requires_immediate_escalation": requires_immediate_escalation,
        "should_notify_residents":       should_notify_residents,
        "notification_priority":         notification_priority,
        "should_activate_backup_system": should_activate_backup_system,
        "auto_dispatch_contractor":      auto_dispatch_contractor,
        "recommended_contractor":        recommended_contractor,
        "estimated_risk_score":          estimated_risk_score,
        "decision_reasoning":            decision_reasoning,
    }

    logger.info(
        "Autonomous decision computed",
        incident_type=incident_type,
        severity=severity,
        risk_score=estimated_risk_score,
        escalation=requires_immediate_escalation,
        auto_dispatch=auto_dispatch_contractor,
    )

    return decision
