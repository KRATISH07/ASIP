import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from app.db.models.incident import IncidentType, IncidentSeverity, IncidentStatus


class SensorDataPayload(BaseModel):
    """Incoming sensor reading that triggers the agent workflow."""
    tower_id: uuid.UUID
    sensor_type: str = Field(..., description="water_pressure | tank_level | power_consumption")
    value: float
    unit: str = Field(..., description="bar | liters | kW")
    timestamp: datetime
    metadata: Optional[dict] = None


class IncidentCreate(BaseModel):
    type: IncidentType
    severity: IncidentSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    tower_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    sensor_data: Optional[dict] = None


class IncidentUpdate(BaseModel):
    status: Optional[IncidentStatus] = None
    root_cause: Optional[str] = None
    resolved_at: Optional[datetime] = None


class ContractorAssignmentOut(BaseModel):
    contractor_id: uuid.UUID
    contractor_name: str
    estimated_cost: Optional[float] = None
    estimated_time_hrs: Optional[float] = None
    selection_reasoning: Optional[str] = None

    model_config = {"from_attributes": True}


class IncidentOut(BaseModel):
    id: uuid.UUID
    type: IncidentType
    severity: IncidentSeverity
    confidence: float
    status: IncidentStatus
    tower_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    root_cause: Optional[str] = None
    ai_decision: Optional[dict] = None
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    created_at: datetime
    contractor_assignment: Optional[ContractorAssignmentOut] = None

    model_config = {"from_attributes": True}


class IncidentListOut(BaseModel):
    items: List[IncidentOut]
    total: int
    page: int
    page_size: int
