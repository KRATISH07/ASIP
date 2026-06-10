import uuid
from typing import Optional
from sqlalchemy import String, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.db.models.incident import IncidentType, IncidentSeverity


class IncidentMemory(Base):
    __tablename__ = "incident_memory"

    incident_uuid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    incident_type: Mapped[Optional[IncidentType]] = mapped_column(String, nullable=True, index=True)
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[Optional[IncidentSeverity]] = mapped_column(String, nullable=True, index=True)
    affected_residents: Mapped[Optional[int]] = mapped_column(nullable=True)
    contractor_used: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    repair_duration_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    resolution_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
