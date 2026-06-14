"""Feedback API — V4 Learning Loop

POST /incidents/{incident_uuid}/feedback
  Record actual resolution outcomes so future predictions can learn from them.
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.dependencies import get_current_user, require_manager_or_above
from app.db.models.user import User
from app.services import feedback_service
from app.core.logging import get_logger

logger = get_logger("feedback_api")

router = APIRouter(prefix="/incidents", tags=["Feedback"])


class FeedbackRequest(BaseModel):
    """Actual resolution outcome recorded after an incident is closed."""

    actual_outage_hrs: Optional[float] = Field(
        default=None,
        description="Actual outage duration in hours (post-resolution)",
        examples=[3.5],
    )
    actual_cost: Optional[float] = Field(
        default=None,
        description="Actual repair/contractor cost in INR (post-resolution)",
        examples=[12500.0],
    )


class FeedbackResponse(BaseModel):
    updated: bool
    incident_uuid: Optional[str] = None
    predicted_outage_hrs: Optional[float] = None
    actual_outage_hrs: Optional[float] = None
    predicted_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    decision_accuracy: Optional[float] = None
    reason: Optional[str] = None


@router.post(
    "/{incident_uuid}/feedback",
    response_model=FeedbackResponse,
    summary="Record actual resolution outcome for learning loop",
    description=(
        "After an incident is resolved, submit actual outage duration and cost. "
        "The system computes decision_accuracy by comparing predicted vs actual "
        "values and stores the result in incident_memory for future model improvement. "
        "Requires Manager or Admin role."
    ),
)
async def submit_feedback(
    incident_uuid: uuid.UUID,
    payload: FeedbackRequest,
    current_user: User = Depends(require_manager_or_above),
) -> FeedbackResponse:
    try:
        result = await feedback_service.store_feedback(
            incident_uuid=str(incident_uuid),
            actual_outage_hrs=payload.actual_outage_hrs,
            actual_cost=payload.actual_cost,
        )
        return FeedbackResponse(**result)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error("Feedback API error", error=str(e), incident_uuid=str(incident_uuid))
        raise HTTPException(status_code=500, detail="Failed to store feedback")
