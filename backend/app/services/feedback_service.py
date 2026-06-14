"""Feedback Service — V4 Learning Loop

Stores post-resolution feedback (actual vs predicted values, decision accuracy)
into the incident_memory table. This enables future predictive models to learn
from real outcomes.

IMPORTANT: memory_service.py is protected and must NOT be modified.
This service handles the feedback write path independently.
"""
import uuid
from typing import Optional
from app.core.logging import get_logger

logger = get_logger("feedback_service")


def _compute_decision_accuracy(
    predicted_outage_hrs: Optional[float],
    actual_outage_hrs: Optional[float],
    predicted_cost: Optional[float],
    actual_cost: Optional[float],
) -> Optional[float]:
    """Compute a 0–1 accuracy score comparing predictions to actuals.

    Uses mean absolute percentage error (MAPE) inverted:
      accuracy = 1 - mean( |predicted - actual| / max(1, actual) )
    Clamped to [0, 1].
    Returns None when both pairs are unavailable.
    """
    errors = []
    if predicted_outage_hrs is not None and actual_outage_hrs is not None:
        denom = max(1.0, actual_outage_hrs)
        errors.append(abs(predicted_outage_hrs - actual_outage_hrs) / denom)
    if predicted_cost is not None and actual_cost is not None:
        denom = max(1.0, actual_cost)
        errors.append(abs(predicted_cost - actual_cost) / denom)

    if not errors:
        return None

    mape = sum(errors) / len(errors)
    return round(max(0.0, min(1.0, 1.0 - mape)), 3)


async def store_feedback(
    incident_uuid: str,
    actual_outage_hrs: Optional[float] = None,
    actual_cost: Optional[float] = None,
) -> dict:
    """Locate the IncidentMemory record for ``incident_uuid`` and write back
    actual outcome values + computed decision_accuracy.

    Returns a summary dict with the fields that were updated.
    """
    # Lazy import — avoids creating DB engine at module load time
    from app.db.session import AsyncSessionFactory
    from app.db.models.incident_memory import IncidentMemory
    from sqlalchemy import select

    try:
        incident_uuid_obj = uuid.UUID(str(incident_uuid))
    except Exception:
        raise ValueError(f"Invalid incident UUID: {incident_uuid!r}")

    async with AsyncSessionFactory() as db:
        stmt = select(IncidentMemory).where(
            IncidentMemory.incident_uuid == incident_uuid_obj
        ).order_by(IncidentMemory.created_at.desc()).limit(1)

        result = await db.execute(stmt)
        mem = result.scalar_one_or_none()

        if not mem:
            logger.warning("Feedback: no IncidentMemory found", incident_uuid=str(incident_uuid))
            return {"updated": False, "reason": "No memory record found for this incident"}

        # Read predicted values that were stored when the incident was processed
        predicted_outage_hrs = mem.predicted_outage_hrs
        predicted_cost = mem.predicted_cost

        accuracy = _compute_decision_accuracy(
            predicted_outage_hrs=predicted_outage_hrs,
            actual_outage_hrs=actual_outage_hrs,
            predicted_cost=predicted_cost,
            actual_cost=actual_cost,
        )

        mem.actual_outage_hrs  = actual_outage_hrs
        mem.actual_cost        = actual_cost
        mem.decision_accuracy  = accuracy

        await db.commit()
        await db.refresh(mem)

    logger.info(
        "Feedback stored",
        incident_uuid=str(incident_uuid),
        actual_outage_hrs=actual_outage_hrs,
        actual_cost=actual_cost,
        decision_accuracy=accuracy,
    )

    return {
        "updated":             True,
        "incident_uuid":       str(incident_uuid),
        "predicted_outage_hrs": predicted_outage_hrs,
        "actual_outage_hrs":   actual_outage_hrs,
        "predicted_cost":      predicted_cost,
        "actual_cost":         actual_cost,
        "decision_accuracy":   accuracy,
    }
