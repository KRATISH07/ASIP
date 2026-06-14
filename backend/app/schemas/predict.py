"""Pydantic schemas for the Predictive Impact Analysis API."""
from typing import Any, List, Optional
from pydantic import BaseModel, Field
from app.db.models.incident import IncidentType, IncidentSeverity


class PredictImpactRequest(BaseModel):
    """Request payload for POST /predict/impact."""

    incident_type: str = Field(
        ...,
        description="Type of incident e.g. water_pressure_drop, power_outage",
        examples=["water_pressure_drop"],
    )
    severity: str = Field(
        default="medium",
        description="Severity level: low | medium | high | critical",
        examples=["critical"],
    )


class ResourceRequirementsOut(BaseModel):
    """Estimated crew and equipment requirements."""

    crew: int = Field(..., description="Estimated crew size")
    special_equipment: List[str] = Field(
        default_factory=list,
        description="List of special equipment needed",
    )


class PredictImpactResponse(BaseModel):
    """Full prediction response returned by the predictive engine."""

    predicted_residents: int = Field(..., description="Estimated number of affected residents")
    predicted_outage_hrs: float = Field(..., description="Estimated outage duration in hours")
    predicted_severity: str = Field(..., description="Predicted severity label")
    escalation_probability: float = Field(
        ..., ge=0.0, le=1.0, description="Probability that the incident will escalate (0–1)"
    )
    estimated_repair_cost: float = Field(..., description="Estimated repair cost in INR")
    estimated_contractor_cost: float = Field(
        ..., description="Estimated contractor cost including margins in INR"
    )
    resource_requirements: ResourceRequirementsOut
    sla_breach_risk: float = Field(
        ..., ge=0.0, le=1.0, description="Risk of breaching the SLA (0–1)"
    )
    time_to_resolution_risk: float = Field(
        ..., ge=0.0, le=1.0, description="Normalized time-to-resolution risk (0–1)"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence of the prediction (0–1)"
    )
    reasoning: str = Field(..., description="Human-readable reasoning behind the prediction")
    historical_evidence: List[Any] = Field(
        default_factory=list,
        description="Similar historical incidents used for prediction",
    )
