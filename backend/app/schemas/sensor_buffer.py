import uuid
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Inbound schemas (upload / replay)
# ---------------------------------------------------------------------------

class BufferedSensorEvent(BaseModel):
    """A single sensor event stored by an edge gateway during connectivity loss."""
    sensor_id: str = Field(..., description="Unique sensor identifier on the device")
    idempotency_key: str = Field(
        ...,
        description="Gateway-generated unique key (e.g. sensor_id + timestamp). "
                    "Duplicate keys are silently skipped.",
    )
    payload: dict = Field(
        ...,
        description="Raw sensor reading payload (same shape as POST /incidents/sensor-data)",
    )
    event_timestamp: datetime = Field(
        ...,
        description="Original timestamp of the reading on the sensor device",
    )


class BufferUploadRequest(BaseModel):
    """Batch upload of buffered sensor events from an edge gateway."""
    events: List[BufferedSensorEvent] = Field(
        ...,
        description="List of buffered events to upload",
        min_length=1,
        max_length=1000,
    )


class ReplayRequest(BaseModel):
    """Request to retry failed buffer events."""
    limit: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of failed events to replay in this call",
    )


# ---------------------------------------------------------------------------
# Outbound schemas (responses)
# ---------------------------------------------------------------------------

class BufferUploadResponse(BaseModel):
    total_received: int
    successful: int
    failed: int
    duplicate_skipped: int


class ReplayResponse(BaseModel):
    replayed: int
    succeeded: int
    failed: int


class BufferStatsResponse(BaseModel):
    pending_count: int
    failed_count: int
    synced_count: int
    replay_success_rate: float = Field(
        description="Ratio of synced / (synced + failed). 0.0 when no data."
    )
    oldest_unsynced_age_seconds: Optional[float] = Field(
        default=None,
        description="Age in seconds of the oldest pending/failed event. "
                    "None when no unsynced events exist.",
    )
