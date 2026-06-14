"""Pydantic schemas for the Autonomous Decision Engine API."""
from typing import Optional
from pydantic import BaseModel, Field


class DecisionRequest(BaseModel):
    """Request payload for POST /decision/analyze."""

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


class DecisionResponse(BaseModel):
    """Full autonomous decision response."""

    requires_immediate_escalation: bool = Field(
        ..., description="Whether the incident requires immediate escalation"
    )
    should_notify_residents: bool = Field(
        ..., description="Whether residents should be notified"
    )
    notification_priority: str = Field(
        ..., description="Priority level for resident notifications"
    )
    should_activate_backup_system: bool = Field(
        ..., description="Whether backup infrastructure systems should be activated"
    )
    auto_dispatch_contractor: bool = Field(
        ..., description="Whether a contractor should be automatically dispatched"
    )
    recommended_contractor: Optional[str] = Field(
        default=None, description="Name of the recommended contractor (if available)"
    )
    estimated_risk_score: float = Field(
        ..., ge=0.0, le=1.0, description="Composite risk score (0–1)"
    )
    decision_reasoning: str = Field(
        ..., description="Human-readable reasoning for the decision"
    )
