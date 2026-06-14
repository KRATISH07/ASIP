"""
Unit tests for learning_service — V5 Intelligence Improvement Layer

All tests are pure: no DB, no network, no Chroma, no OpenAI.
Inputs are hand-crafted dicts that mirror what incident_memory returns.

Test cases:
    1. Overestimation bias → correction factor < 1
    2. Underestimation bias → correction factor > 1
    3. Accurate predictions → near-identity correction
    4. Insufficient samples → correction_applied=False, factor=1.0
    5. Adapted confidence replaces fake formula
    6. Aggregate metrics shape and bias label
    7. Empty input → graceful identity (no crash)
    8. Correction factor clamping (extreme outliers)
"""
import pytest
from app.services.learning_service import (
    compute_correction_factors,
    compute_aggregate_metrics,
    _signed_error_ratio,
    _accuracy_from_error,
    MIN_SAMPLES,
    CORRECTION_FACTOR_MIN,
    CORRECTION_FACTOR_MAX,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_record(
    predicted_outage: float | None = None,
    actual_outage: float | None = None,
    predicted_cost: float | None = None,
    actual_cost: float | None = None,
) -> dict:
    return {
        "predicted_outage_hrs": predicted_outage,
        "actual_outage_hrs": actual_outage,
        "predicted_cost": predicted_cost,
        "actual_cost": actual_cost,
    }


# ---------------------------------------------------------------------------
# Test 1 — Consistent overestimation → correction factor < 1
# ---------------------------------------------------------------------------

def test_overestimation_produces_downward_correction():
    """System predicted 12h, reality was 8h → bias positive → CF < 1."""
    records = [
        _make_record(predicted_outage=12.0, actual_outage=8.0,
                     predicted_cost=10000, actual_cost=7000),
        _make_record(predicted_outage=10.0, actual_outage=7.0,
                     predicted_cost=9000, actual_cost=6500),
        _make_record(predicted_outage=14.0, actual_outage=10.0,
                     predicted_cost=12000, actual_cost=9000),
    ]
    cf = compute_correction_factors(records)

    assert cf["correction_applied"] is True
    assert cf["outage_bias"] > 0, "Positive bias expected for overestimation"
    assert cf["outage_correction_factor"] < 1.0, "CF must be < 1 to reduce predictions"
    assert cf["cost_correction_factor"] < 1.0


# ---------------------------------------------------------------------------
# Test 2 — Consistent underestimation → correction factor > 1
# ---------------------------------------------------------------------------

def test_underestimation_produces_upward_correction():
    """System predicted 4h, reality was 9h → bias negative → CF > 1."""
    records = [
        _make_record(predicted_outage=4.0,  actual_outage=9.0,
                     predicted_cost=3000, actual_cost=8000),
        _make_record(predicted_outage=3.0,  actual_outage=7.0,
                     predicted_cost=2500, actual_cost=6000),
        _make_record(predicted_outage=5.0,  actual_outage=10.0,
                     predicted_cost=4000, actual_cost=9000),
    ]
    cf = compute_correction_factors(records)

    assert cf["correction_applied"] is True
    assert cf["outage_bias"] < 0, "Negative bias expected for underestimation"
    assert cf["outage_correction_factor"] > 1.0, "CF must be > 1 to increase predictions"
    assert cf["cost_correction_factor"] > 1.0


# ---------------------------------------------------------------------------
# Test 3 — Accurate predictions → near-identity correction
# ---------------------------------------------------------------------------

def test_accurate_predictions_near_identity_correction():
    """System predicted exactly right → bias ≈ 0, CF ≈ 1.0."""
    records = [
        _make_record(predicted_outage=8.0, actual_outage=8.0,
                     predicted_cost=5000, actual_cost=5000),
        _make_record(predicted_outage=4.0, actual_outage=4.0,
                     predicted_cost=3000, actual_cost=3000),
        _make_record(predicted_outage=6.0, actual_outage=6.0,
                     predicted_cost=4000, actual_cost=4000),
    ]
    cf = compute_correction_factors(records)

    assert cf["correction_applied"] is True
    assert abs(cf["outage_bias"]) < 0.01, "Bias should be ~0 for perfect predictions"
    assert abs(cf["outage_correction_factor"] - 1.0) < 0.01
    assert cf["adapted_confidence"] is not None
    assert cf["adapted_confidence"] > 0.95, "Perfect predictions → high confidence"


# ---------------------------------------------------------------------------
# Test 4 — Insufficient samples → no correction applied
# ---------------------------------------------------------------------------

def test_insufficient_samples_returns_identity():
    """Fewer than MIN_SAMPLES records → correction_applied=False, factor=1.0."""
    records = [
        _make_record(predicted_outage=10.0, actual_outage=5.0,
                     predicted_cost=8000, actual_cost=4000),
    ]
    assert len(records) < MIN_SAMPLES

    cf = compute_correction_factors(records)

    assert cf["correction_applied"] is False
    assert cf["outage_correction_factor"] == 1.0
    assert cf["cost_correction_factor"] == 1.0
    assert cf["adapted_confidence"] is None


# ---------------------------------------------------------------------------
# Test 5 — Adapted confidence is derived from accuracy, not sample count
# ---------------------------------------------------------------------------

def test_adapted_confidence_reflects_accuracy_not_count():
    """Even with many samples, poor accuracy → low confidence.
    This tests that the fake formula (0.30 + 0.12 * N) is NOT used.
    """
    # 5 records, all wildly wrong (predicted 24h, actual 2h)
    records = [
        _make_record(predicted_outage=24.0, actual_outage=2.0,
                     predicted_cost=20000, actual_cost=1000)
        for _ in range(5)
    ]
    cf = compute_correction_factors(records)

    # With 5 records the old formula would give: 0.30 + 0.12×5 = 0.90
    # But actual accuracy should be very low (prediction was 12× off)
    fake_formula_result = min(0.95, 0.30 + 0.12 * 5)
    assert cf["adapted_confidence"] is not None
    assert cf["adapted_confidence"] < fake_formula_result, (
        f"Adapted confidence ({cf['adapted_confidence']}) should be much lower than "
        f"fake formula ({fake_formula_result}) for wildly wrong predictions"
    )


# ---------------------------------------------------------------------------
# Test 6 — Aggregate metrics bias label and shape
# ---------------------------------------------------------------------------

def test_aggregate_metrics_shape_and_bias_label():
    """compute_aggregate_metrics returns correct shape and bias label."""
    records = [
        _make_record(predicted_outage=20.0, actual_outage=10.0,
                     predicted_cost=15000, actual_cost=8000),
        _make_record(predicted_outage=18.0, actual_outage=9.0,
                     predicted_cost=14000, actual_cost=7000),
        _make_record(predicted_outage=22.0, actual_outage=11.0,
                     predicted_cost=16000, actual_cost=9000),
    ]
    metrics = compute_aggregate_metrics(records)

    required_keys = {
        "learning_samples", "outage_sample_count", "cost_sample_count",
        "average_prediction_accuracy", "average_cost_accuracy",
        "prediction_bias", "outage_bias", "cost_bias",
        "outage_correction_factor", "cost_correction_factor",
        "correction_applied",
    }
    assert required_keys.issubset(metrics.keys())
    assert metrics["prediction_bias"] == "overestimation"
    assert metrics["learning_samples"] == 3
    assert metrics["correction_applied"] is True


# ---------------------------------------------------------------------------
# Test 7 — Empty input → graceful identity, no crash
# ---------------------------------------------------------------------------

def test_empty_input_returns_identity():
    """Empty list must not crash and must return all-1.0 factors."""
    cf = compute_correction_factors([])
    assert cf["correction_applied"] is False
    assert cf["outage_correction_factor"] == 1.0
    assert cf["cost_correction_factor"] == 1.0

    metrics = compute_aggregate_metrics([])
    assert metrics["learning_samples"] == 0
    assert metrics["prediction_bias"] == "insufficient_data"


# ---------------------------------------------------------------------------
# Test 8 — Correction factor clamping prevents extreme adjustments
# ---------------------------------------------------------------------------

def test_extreme_bias_correction_factor_clamped():
    """Even with extreme bias, correction factor must stay within [0.5, 2.0]."""
    # Predicted 1000h, actual 1h → extreme overestimation
    records = [
        _make_record(predicted_outage=1000.0, actual_outage=1.0,
                     predicted_cost=1000000, actual_cost=100)
        for _ in range(5)
    ]
    cf = compute_correction_factors(records)

    assert cf["outage_correction_factor"] >= CORRECTION_FACTOR_MIN
    assert cf["outage_correction_factor"] <= CORRECTION_FACTOR_MAX
    assert cf["cost_correction_factor"] >= CORRECTION_FACTOR_MIN
    assert cf["cost_correction_factor"] <= CORRECTION_FACTOR_MAX


# ---------------------------------------------------------------------------
# Unit tests for helper functions
# ---------------------------------------------------------------------------

def test_signed_error_ratio_overestimation():
    ratio = _signed_error_ratio(predicted=12.0, actual=8.0)
    assert ratio == pytest.approx(0.5, abs=0.001)  # (12-8)/8 = 0.5


def test_signed_error_ratio_underestimation():
    ratio = _signed_error_ratio(predicted=4.0, actual=8.0)
    assert ratio == pytest.approx(-0.5, abs=0.001)  # (4-8)/8 = -0.5


def test_accuracy_from_zero_error():
    assert _accuracy_from_error(0.0) == 1.0


def test_accuracy_from_full_error():
    assert _accuracy_from_error(1.5) == 0.0  # clamped at 0
