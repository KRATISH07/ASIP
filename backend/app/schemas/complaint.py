import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.db.models.complaint import ComplaintCategory, ComplaintPriority, ComplaintStatus


class ComplaintCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=10)
    category: ComplaintCategory
    priority: ComplaintPriority = ComplaintPriority.medium
    # Resident's own UUID — set from JWT token claims at the service layer.
    # Clients do NOT send this; it is injected server-side from the auth token.


class ComplaintUpdate(BaseModel):
    status: Optional[ComplaintStatus] = None
    assigned_manager_id: Optional[uuid.UUID] = None
    resolution_notes: Optional[str] = None
    priority: Optional[ComplaintPriority] = None
    ai_confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class ComplaintConvertRequest(BaseModel):
    """Optional overrides when converting a complaint to a formal incident."""
    incident_type: Optional[str] = Field(
        default=None,
        description="Override the auto-inferred incident type. "
                    "Defaults to category-to-type mapping in the model.",
    )
    override_severity: Optional[str] = Field(
        default=None,
        description="Override auto-assigned severity (low / medium / high / critical).",
    )


class ComplaintOut(BaseModel):
    id: uuid.UUID
    resident_id: Optional[uuid.UUID]
    title: str
    description: str
    category: ComplaintCategory
    priority: ComplaintPriority
    status: ComplaintStatus
    linked_incident_id: Optional[uuid.UUID]
    ai_confidence_score: Optional[float]
    assigned_manager_id: Optional[uuid.UUID]
    resolution_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ComplaintListOut(BaseModel):
    items: List[ComplaintOut]
    total: int
    page: int
    page_size: int


class ComplaintStatsOut(BaseModel):
    total_complaints: int
    open: int
    under_review: int
    resolved: int
    converted_to_incidents: int
    avg_resolution_time_hours: Optional[float]


class ComplaintConvertResponse(BaseModel):
    complaint_id: uuid.UUID
    incident_id: str
    workflow_queued: bool
