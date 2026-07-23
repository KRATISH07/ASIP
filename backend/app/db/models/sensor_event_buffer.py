import enum
import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class SyncStatus(str, enum.Enum):
    pending = "pending"
    synced = "synced"
    failed = "failed"


class SensorEventBuffer(Base):
    """
    Durable buffer for sensor events uploaded by edge gateways.

    Edge gateways store events locally when connectivity is lost and flush
    them later via POST /sensor-buffer/upload. This table holds all buffered
    events and tracks their processing state.

    Idempotency: idempotency_key must be unique — duplicate uploads are silently
    skipped (INSERT ... ON CONFLICT DO NOTHING) and counted as duplicate_skipped.
    """
    __tablename__ = "sensor_event_buffer"

    sensor_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    event_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    sync_status: Mapped[SyncStatus] = mapped_column(
        SAEnum(SyncStatus, name="sync_status_enum"),
        nullable=False,
        default=SyncStatus.pending,
        index=True,
    )
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_attempt_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
