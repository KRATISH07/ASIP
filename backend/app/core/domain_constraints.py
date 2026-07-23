"""Domain Constraint Validation for AI Outputs (Fix #11)

THE PROBLEM THIS SOLVES:
    predictive_service can return physically impossible values:
    - predicted_outage_hrs = -2.3 (negative time)
    - predicted_residents = 9500 (more than could live in a building)
    - estimated_repair_cost = 0.0 (free repair — arithmetic edge case)
    - sla_breach_risk = -0.15 (negative risk)

    These flow directly into:
    1. LLM prompts (GPT-4 reasons from impossible data)
    2. incident_memory (V8 trains on corrupted labels)
    3. learning_service (negative correction factors break math)

    A negative correction_factor = 1/(1+bias) can arise when bias <= -1.0,
    which can happen if predicted_outage_hrs is negative. The next prediction
    is multiplied by a negative factor. The system produces negative outage times
    with high confidence.

DESIGN:
    Pure function. Applied as the final step of predict_impact().
    Logs WARNING when clamping occurs — clamp events indicate upstream data
    quality problems (bad history, bad sensor data) that should be investigated.
"""
from typing import Any
from app.core.logging import get_logger

logger = get_logger("domain_constraints")


# Physical domain constraints for infrastructure predictions
# Based on realistic residential society operations
MAX_OUTAGE_HRS = 168.0           # 1 week: maximum plausible infrastructure outage
MIN_OUTAGE_HRS = 0.25            # 15 minutes: minimum meaningful incident
MAX_RESIDENTS = 10_000           # maximum plausible residents in a society
MIN_RESIDENTS = 0
MAX_REPAIR_COST_INR = 50_000_000 # INR 5 crore: maximum plausible repair
MIN_REPAIR_COST_INR = 0.0        # free is technically possible (warranty)
CONFIDENCE_MIN = 0.0
CONFIDENCE_MAX = 1.0
PROBABILITY_MIN = 0.0
PROBABILITY_MAX = 1.0
RISK_MIN = 0.0
RISK_MAX = 1.0


def validate_prediction(prediction: dict[str, Any]) -> dict[str, Any]:
    """Clamp all prediction values to physically meaningful ranges.

    Returns a new dict with all values validated. The original dict is
    not mutated.

    Logs WARNING for each clamped field, because clamping indicates either:
    - Bad historical data (negative repair durations stored in memory)
    - Arithmetic edge cases in the prediction formulas
    - Data pipeline corruption

    Any clamping event should be investigated, not silently accepted.
    """
    pred = dict(prediction)
    clamped_fields = []

    def _clamp(key: str, lo: float, hi: float) -> None:
        val = pred.get(key)
        if val is None:
            return
        try:
            fval = float(val)
        except (TypeError, ValueError):
            return
        clamped = max(lo, min(hi, fval))
        if clamped != fval:
            clamped_fields.append((key, fval, clamped))
        pred[key] = round(clamped, 4)

    _clamp("predicted_outage_hrs",        MIN_OUTAGE_HRS,       MAX_OUTAGE_HRS)
    _clamp("predicted_residents",         MIN_RESIDENTS,        MAX_RESIDENTS)
    _clamp("estimated_repair_cost",       MIN_REPAIR_COST_INR,  MAX_REPAIR_COST_INR)
    _clamp("estimated_contractor_cost",   MIN_REPAIR_COST_INR,  MAX_REPAIR_COST_INR)
    _clamp("confidence_score",            CONFIDENCE_MIN,       CONFIDENCE_MAX)
    _clamp("escalation_probability",      PROBABILITY_MIN,      PROBABILITY_MAX)
    _clamp("sla_breach_risk",             RISK_MIN,             RISK_MAX)
    _clamp("time_to_resolution_risk",     RISK_MIN,             RISK_MAX)

    if clamped_fields:
        logger.warning(
            "Prediction values clamped to domain constraints — "
            "indicates upstream data quality issues",
            clamped={k: {"original": orig, "clamped": c} for k, orig, c in clamped_fields},
        )

    return pred
