"""Learning Analytics API — V5

GET /analytics/learning
    Returns aggregate prediction accuracy, bias direction, and active
    correction factors. This endpoint is how engineers verify that the
    learning loop is working.

Architecture note:
    All DB I/O happens here (at the API layer), keeping learning_service.py
    a pure, testable function with no hidden dependencies.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import require_roles
from app.db.session import get_db
from app.db.models.user import User, UserRole
from app.db.models.incident_memory import IncidentMemory
from app.schemas.analytics import LearningAnalyticsResponse
from app.services.learning_service import compute_aggregate_metrics
from app.core.logging import get_logger

logger = get_logger("analytics_api")

router = APIRouter(prefix="/analytics", tags=["Learning Analytics"])


@router.get(
    "/learning",
    response_model=LearningAnalyticsResponse,
    summary="Get learning engine metrics and correction factors",
    description=(
        "Returns aggregate prediction accuracy, systematic bias direction, "
        "and the active correction factors that the learning engine applies "
        "to future predictions. All values are derived from real feedback "
        "records stored when incidents are resolved.\n\n"
        "**prediction_bias** values:\n"
        "- `overestimation` — system consistently predicts too high\n"
        "- `underestimation` — system consistently predicts too low\n"
        "- `accurate` — within 5% mean error\n"
        "- `insufficient_data` — fewer than 3 feedback records\n\n"
        "**correction_applied** = true means future predictions are being "
        "actively scaled by the correction factors shown."
    ),
)
async def get_learning_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = require_roles(UserRole.manager, UserRole.admin),
) -> LearningAnalyticsResponse:
    """Fetch all feedback records and compute aggregate learning metrics."""

    # Fetch records that have at least one feedback value
    stmt = (
        select(
            IncidentMemory.predicted_outage_hrs,
            IncidentMemory.actual_outage_hrs,
            IncidentMemory.predicted_cost,
            IncidentMemory.actual_cost,
        )
        .where(
            # Include records where at least one actual value was submitted
            (IncidentMemory.actual_outage_hrs.is_not(None))
            | (IncidentMemory.actual_cost.is_not(None))
        )
        .order_by(IncidentMemory.created_at.desc())
        .limit(200)  # cap to last 200 to keep computation fast
    )

    result = await db.execute(stmt)
    rows = result.mappings().all()
    feedback_records = [dict(r) for r in rows]

    metrics = compute_aggregate_metrics(feedback_records)

    logger.info(
        "Learning analytics requested",
        total_samples=metrics["learning_samples"],
        correction_applied=metrics["correction_applied"],
        bias=metrics["prediction_bias"],
        user_id=str(current_user.id),
    )

    return LearningAnalyticsResponse(**metrics)
