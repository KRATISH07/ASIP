"""
Sensor Buffer API — Store-and-Forward ingestion endpoints.

POST /sensor-buffer/upload   — batch upload of buffered sensor events
POST /sensor-buffer/replay   — retry failed events
GET  /sensor-buffer/stats    — buffer health metrics

Access control:
  upload / replay → sensor_gateway | admin
  stats           → manager | admin
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import require_roles
from app.db.models.user import User, UserRole
from app.schemas.sensor_buffer import (
    BufferUploadRequest,
    BufferUploadResponse,
    ReplayRequest,
    ReplayResponse,
    BufferStatsResponse,
)
from app.services import sensor_buffer_service
from app.core.logging import get_logger

logger = get_logger("sensor_buffer_api")

router = APIRouter(prefix="/sensor-buffer", tags=["Sensor Buffer"])


@router.post(
    "/upload",
    response_model=BufferUploadResponse,
    summary="Batch upload buffered sensor events from an edge gateway",
    description=(
        "Accepts a batch of sensor events stored locally by a gateway during "
        "network outage. Events are deduplicated via idempotency_key — duplicate "
        "uploads are silently skipped. Timestamps from the original reading are "
        "preserved exactly as received.\n\n"
        "**Access:** sensor_gateway or admin only."
    ),
)
async def upload_buffered_events(
    payload: BufferUploadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = require_roles(UserRole.sensor_gateway, UserRole.admin),
) -> BufferUploadResponse:
    events = [e.model_dump() for e in payload.events]
    result = await sensor_buffer_service.upload_events(events, db)
    logger.info(
        "Buffer upload complete",
        user=str(current_user.id),
        **result,
    )
    return BufferUploadResponse(**result)


@router.post(
    "/replay",
    response_model=ReplayResponse,
    summary="Retry failed buffered sensor events",
    description=(
        "Re-queues failed buffered events through the incident AI workflow. "
        "Succeeded events are marked `synced`; events that fail again remain "
        "`failed` with an updated retry count and error message.\n\n"
        "**Access:** sensor_gateway or admin only."
    ),
)
async def replay_failed_events(
    payload: ReplayRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = require_roles(UserRole.sensor_gateway, UserRole.admin),
) -> ReplayResponse:
    result = await sensor_buffer_service.replay_failed_events(db, limit=payload.limit)
    logger.info(
        "Buffer replay triggered",
        user=str(current_user.id),
        **result,
    )
    return ReplayResponse(**result)


@router.get(
    "/stats",
    response_model=BufferStatsResponse,
    summary="Get sensor buffer health statistics",
    description=(
        "Returns aggregate buffer metrics: pending/failed/synced event counts, "
        "replay success rate, and the age of the oldest unprocessed event.\n\n"
        "**Access:** manager or admin only."
    ),
)
async def get_buffer_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = require_roles(UserRole.manager, UserRole.admin),
) -> BufferStatsResponse:
    stats = await sensor_buffer_service.get_buffer_stats(db)
    return BufferStatsResponse(**stats)
