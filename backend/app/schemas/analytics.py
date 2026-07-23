"""Pydantic schemas for the V5 Learning Analytics API."""
from typing import Optional
from pydantic import BaseModel, Field


class LearningAnalyticsResponse(BaseModel):
    """Response for GET /analytics/learning."""

    learning_samples: int = Field(
        ..., description="Total number of feedback records used for analysis"
    )
    outage_sample_count: int = Field(
        ..., description="Number of paired (predicted, actual) outage records"
    )
    cost_sample_count: int = Field(
        ..., description="Number of paired (predicted, actual) cost records"
    )
    average_prediction_accuracy: Optional[float] = Field(
        default=None,
        description="Mean outage prediction accuracy (0–1). None if < 3 samples.",
    )
    average_cost_accuracy: Optional[float] = Field(
        default=None,
        description="Mean cost prediction accuracy (0–1). None if < 3 samples.",
    )
    prediction_bias: str = Field(
        ...,
        description=(
            "Dominant bias direction: 'overestimation' | 'underestimation' | "
            "'accurate' | 'insufficient_data'"
        ),
    )
    outage_bias: Optional[float] = Field(
        default=None,
        description=(
            "Mean signed error ratio for outage predictions. "
            "Positive = overestimating. Negative = underestimating."
        ),
    )
    cost_bias: Optional[float] = Field(
        default=None,
        description="Mean signed error ratio for cost predictions.",
    )
    outage_correction_factor: float = Field(
        ...,
        description=(
            "Multiplier applied to raw outage predictions. "
            "1.0 = no correction. < 1 = reduce predictions. > 1 = increase."
        ),
    )
    cost_correction_factor: float = Field(
        ...,
        description="Multiplier applied to raw cost predictions.",
    )
    correction_applied: bool = Field(
        ...,
        description="True when enough samples exist for correction to be active.",
    )
    duration_mae: Optional[float] = Field(
        default=None,
        description="Rolling Mean Absolute Error for outage duration predictions."
    )
    cost_mae: Optional[float] = Field(
        default=None,
        description="Rolling Mean Absolute Error for cost predictions."
    )
    should_retrain: bool = Field(
        default=False,
        description="Flags if the model performance has degraded past acceptable thresholds."
    )
    retrain_reasons: list[str] = Field(
        default_factory=list,
        description="Descriptions of why retraining was triggered."
    )
