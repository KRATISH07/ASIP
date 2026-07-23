"""Learning Service — V5 Intelligence Improvement Layer

Pure-function module. No DB calls, no async, no LLM.
All DB I/O happens in the caller; this service only does math.

Engineering problem solved:
    The system stored prediction feedback (predicted vs actual) but never
    read it back to change future predictions. This module closes that loop.

Architecture:
    1. Caller fetches feedback records from incident_memory (DB I/O — not here)
    2. Caller passes records into compute_correction_factors()
    3. This module returns CorrectionFactors (bias, multiplier, confidence)
    4. Caller passes CorrectionFactors to predictive_service.predict_impact()
    5. predict_impact() applies the correction before returning

Math:
    Prediction Error (per incident):
        error_ratio_i = (predicted_i - actual_i) / max(1, actual_i)

    Systematic Bias (across N incidents):
        bias = mean(error_ratio_i)
          > 0  → system overestimates (predictions too high)
          < 0  → system underestimates (predictions too low)
          = 0  → unbiased

    Correction Factor:
        correction_factor = 1 / (1 + bias)
        new_prediction = base_prediction * correction_factor
        Example: bias = +0.20 → CF = 0.833 → prediction reduced 17%
        Example: bias = -0.25 → CF = 1.333 → prediction increased 33%

    Adapted Confidence:
        accuracy_i = max(0, 1 - |error_ratio_i|)
        adapted_confidence = mean(accuracy_i)
        This replaces the fake formula: 0.30 + 0.12 * len(history)

    Minimum sample requirement:
        Correction is only applied when N >= MIN_SAMPLES (default=3).
        Below that, raw predictions are returned unchanged.
        This prevents a single outlier from distorting future predictions.
"""
from statistics import mean, stdev
from typing import List, Optional, TypedDict

from app.core.logging import get_logger

logger = get_logger("learning_service")

# Minimum number of feedback records before corrections are applied.
# Below this threshold we return identity correction (factor=1.0)
# to avoid overfitting to sparse data.
MIN_SAMPLES = 3

# Hard clamp on correction factor to prevent extreme adjustments.
# A factor outside [0.5, 2.0] would indicate data quality problems.
CORRECTION_FACTOR_MIN = 0.5
CORRECTION_FACTOR_MAX = 2.0

# Hard thresholds for retraining. If rolling MAE exceeds these, should_retrain triggers True.
RETRAIN_THRESHOLD_DURATION_MAE = 12.0  # hours
RETRAIN_THRESHOLD_COST_MAE = 15000.0  # USD
ROLLING_WINDOW_SIZE = 100


class CorrectionFactors(TypedDict):
    """Output of compute_correction_factors().

    Fields
    ------
    outage_correction_factor:
        Multiply base outage prediction by this value.
        1.0 means no correction needed.
    cost_correction_factor:
        Multiply base cost prediction by this value.
    outage_bias:
        Mean signed error ratio for outage predictions.
        Positive = system overestimates. Negative = underestimates.
    cost_bias:
        Mean signed error ratio for cost predictions.
    adapted_confidence:
        Empirically derived confidence (0–1) based on historical accuracy.
        Replaces the fake formula. None when insufficient samples.
    outage_sample_count:
        Number of paired (predicted, actual) outage records used.
    cost_sample_count:
        Number of paired (predicted, actual) cost records used.
    correction_applied:
        False when sample count is below MIN_SAMPLES (no correction).
    """
    outage_correction_factor: float
    cost_correction_factor: float
    outage_bias: float
    cost_bias: float
    adapted_confidence: Optional[float]
    outage_sample_count: int
    cost_sample_count: int
    correction_applied: bool


def _signed_error_ratio(predicted: float, actual: float) -> float:
    """Compute signed relative error: (predicted - actual) / max(1, actual).

    Returns a value in (-inf, +inf) where:
        0.0  = perfect prediction
        +0.5 = overestimated by 50%
        -0.5 = underestimated by 50%
    """
    denom = max(1.0, abs(actual))
    return (predicted - actual) / denom


def _accuracy_from_error(error_ratio: float) -> float:
    """Convert a signed error ratio to an accuracy score in [0, 1]."""
    return max(0.0, 1.0 - abs(error_ratio))


def _compute_bias_and_correction(
    predicted_vals: List[float],
    actual_vals: List[float],
) -> tuple[float, float, Optional[float], int]:
    """Core computation for a single metric (outage or cost).

    Returns
    -------
    (bias, correction_factor, adapted_confidence, sample_count)
    """
    pairs = [
        (p, a)
        for p, a in zip(predicted_vals, actual_vals)
        if p is not None and a is not None
    ]
    n = len(pairs)

    if n < MIN_SAMPLES:
        return 0.0, 1.0, None, n

    error_ratios = [_signed_error_ratio(p, a) for p, a in pairs]
    bias = mean(error_ratios)

    # Correction factor: inverse of (1 + bias)
    # Clamp to prevent extreme adjustments from outlier-heavy datasets
    raw_factor = 1.0 / (1.0 + bias) if (1.0 + bias) != 0 else 1.0
    correction_factor = max(CORRECTION_FACTOR_MIN, min(CORRECTION_FACTOR_MAX, raw_factor))

    # Adapted confidence: mean accuracy across all samples
    accuracies = [_accuracy_from_error(e) for e in error_ratios]
    adapted_confidence = round(mean(accuracies), 3)

    return round(bias, 4), round(correction_factor, 4), adapted_confidence, n


def compute_correction_factors(
    feedback_records: List[dict],
) -> CorrectionFactors:
    """Compute bias, correction factors, and adapted confidence from feedback records.

    Parameters
    ----------
    feedback_records:
        List of dicts from incident_memory, each containing any subset of:
        - predicted_outage_hrs (float | None)
        - actual_outage_hrs    (float | None)
        - predicted_cost       (float | None)
        - actual_cost          (float | None)

    Returns
    -------
    CorrectionFactors dict. If fewer than MIN_SAMPLES records contain paired
    values, correction_applied=False and all factors are 1.0 (identity).

    Notes
    -----
    This function is deliberately synchronous and pure — it contains zero
    I/O, zero side effects, and is fully deterministic for a given input.
    """
    if not feedback_records:
        logger.debug("learning_service: no feedback records — returning identity correction")
        return _identity_correction()

    outage_predicted = []
    outage_actual = []
    cost_predicted = []
    cost_actual = []

    for rec in feedback_records:
        pred_out = rec.get("predicted_outage_hrs")
        act_out = rec.get("actual_outage_hrs")
        pred_cost = rec.get("predicted_cost")
        act_cost = rec.get("actual_cost")

        if pred_out is not None and act_out is not None:
            try:
                outage_predicted.append(float(pred_out))
                outage_actual.append(float(act_out))
            except (TypeError, ValueError):
                pass

        if pred_cost is not None and act_cost is not None:
            try:
                cost_predicted.append(float(pred_cost))
                cost_actual.append(float(act_cost))
            except (TypeError, ValueError):
                pass

    outage_bias, outage_cf, outage_conf, outage_n = _compute_bias_and_correction(
        outage_predicted, outage_actual
    )
    cost_bias, cost_cf, cost_conf, cost_n = _compute_bias_and_correction(
        cost_predicted, cost_actual
    )

    # Adapted confidence: average across both metrics (whichever are available)
    confidences = [c for c in [outage_conf, cost_conf] if c is not None]
    adapted_confidence = round(mean(confidences), 3) if confidences else None

    correction_applied = (outage_n >= MIN_SAMPLES or cost_n >= MIN_SAMPLES)

    result: CorrectionFactors = {
        "outage_correction_factor": outage_cf,
        "cost_correction_factor":   cost_cf,
        "outage_bias":              outage_bias,
        "cost_bias":                cost_bias,
        "adapted_confidence":       adapted_confidence,
        "outage_sample_count":      outage_n,
        "cost_sample_count":        cost_n,
        "correction_applied":       correction_applied,
    }

    logger.info(
        "Correction factors computed",
        outage_cf=outage_cf,
        cost_cf=cost_cf,
        outage_bias=outage_bias,
        cost_bias=cost_bias,
        adapted_confidence=adapted_confidence,
        outage_samples=outage_n,
        cost_samples=cost_n,
        correction_applied=correction_applied,
    )
    return result


def evaluate_model_performance(
    feedback_records: List[dict],
    window_size: int = ROLLING_WINDOW_SIZE
) -> dict:
    """Compute rolling MAE over the most recent feedback records and determine if retraining is needed."""
    records = list(feedback_records)
    # Get the most recent records up to window_size
    recent_records = records[-window_size:] if len(records) > window_size else records
    
    outage_errors = []
    cost_errors = []
    
    for rec in recent_records:
        pred_out = rec.get("predicted_outage_hrs")
        act_out = rec.get("actual_outage_hrs")
        pred_cost = rec.get("predicted_cost")
        act_cost = rec.get("actual_cost")
        
        if pred_out is not None and act_out is not None:
            try:
                outage_errors.append(abs(float(pred_out) - float(act_out)))
            except (TypeError, ValueError):
                pass
                
        if pred_cost is not None and act_cost is not None:
            try:
                cost_errors.append(abs(float(pred_cost) - float(act_cost)))
            except (TypeError, ValueError):
                pass
                
    duration_mae = mean(outage_errors) if outage_errors else None
    cost_mae = mean(cost_errors) if cost_errors else None
    
    should_retrain = False
    reasons = []
    
    if duration_mae is not None and duration_mae > RETRAIN_THRESHOLD_DURATION_MAE:
        should_retrain = True
        reasons.append(f"Duration MAE ({duration_mae:.2f} hrs) exceeded threshold ({RETRAIN_THRESHOLD_DURATION_MAE} hrs)")
        
    if cost_mae is not None and cost_mae > RETRAIN_THRESHOLD_COST_MAE:
        should_retrain = True
        reasons.append(f"Cost MAE (${cost_mae:.2f}) exceeded threshold (${RETRAIN_THRESHOLD_COST_MAE})")
        
    return {
        "duration_mae": round(duration_mae, 3) if duration_mae is not None else None,
        "cost_mae": round(cost_mae, 3) if cost_mae is not None else None,
        "should_retrain": should_retrain,
        "reasons": reasons,
        "sample_count": len(recent_records)
    }


def compute_aggregate_metrics(feedback_records: List[dict]) -> dict:
    """Compute aggregate learning metrics for the analytics endpoint.

    Returns a summary suitable for GET /analytics/learning response.
    """
    if not feedback_records:
        return {
            "learning_samples":             0,
            "outage_sample_count":          0,
            "cost_sample_count":            0,
            "average_prediction_accuracy":  None,
            "average_cost_accuracy":        None,
            "prediction_bias":              "insufficient_data",
            "outage_bias":                  None,
            "cost_bias":                    None,
            "outage_correction_factor":     1.0,
            "cost_correction_factor":       1.0,
            "correction_applied":           False,
            "duration_mae":                 None,
            "cost_mae":                     None,
            "should_retrain":               False,
            "retrain_reasons":              [],
        }

    factors = compute_correction_factors(feedback_records)
    eval_res = evaluate_model_performance(feedback_records)

    # Classify bias direction
    def _bias_label(bias: float) -> str:
        if abs(bias) < 0.05:
            return "accurate"
        return "overestimation" if bias > 0 else "underestimation"

    # Average outage accuracy and cost accuracy separately
    outage_accuracies = []
    cost_accuracies = []
    for rec in feedback_records:
        pred_out = rec.get("predicted_outage_hrs")
        act_out  = rec.get("actual_outage_hrs")
        pred_cst = rec.get("predicted_cost")
        act_cst  = rec.get("actual_cost")
        if pred_out is not None and act_out is not None:
            try:
                outage_accuracies.append(_accuracy_from_error(
                    _signed_error_ratio(float(pred_out), float(act_out))
                ))
            except (TypeError, ValueError):
                pass
        if pred_cst is not None and act_cst is not None:
            try:
                cost_accuracies.append(_accuracy_from_error(
                    _signed_error_ratio(float(pred_cst), float(act_cst))
                ))
            except (TypeError, ValueError):
                pass

    # Dominant bias label: use whichever metric has more samples
    if factors["outage_sample_count"] >= factors["cost_sample_count"]:
        dominant_bias_label = _bias_label(factors["outage_bias"])
    else:
        dominant_bias_label = _bias_label(factors["cost_bias"])

    return {
        "learning_samples":             len(feedback_records),
        "outage_sample_count":          factors["outage_sample_count"],
        "cost_sample_count":            factors["cost_sample_count"],
        "average_prediction_accuracy":  round(mean(outage_accuracies), 3) if outage_accuracies else None,
        "average_cost_accuracy":        round(mean(cost_accuracies), 3)   if cost_accuracies   else None,
        "prediction_bias":              dominant_bias_label,
        "outage_bias":                  factors["outage_bias"],
        "cost_bias":                    factors["cost_bias"],
        "outage_correction_factor":     factors["outage_correction_factor"],
        "cost_correction_factor":       factors["cost_correction_factor"],
        "correction_applied":           factors["correction_applied"],
        "duration_mae":                 eval_res["duration_mae"],
        "cost_mae":                     eval_res["cost_mae"],
        "should_retrain":               eval_res["should_retrain"],
        "retrain_reasons":              eval_res["reasons"],
    }


def _identity_correction() -> CorrectionFactors:
    """Return no-op correction factors (all 1.0) when insufficient data exists."""
    return {
        "outage_correction_factor": 1.0,
        "cost_correction_factor":   1.0,
        "outage_bias":              0.0,
        "cost_bias":                0.0,
        "adapted_confidence":       None,
        "outage_sample_count":      0,
        "cost_sample_count":        0,
        "correction_applied":       False,
    }
