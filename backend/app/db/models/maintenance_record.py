import uuid
from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlalchemy import Text, Numeric, ForeignKey, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contractor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contractors.id", ondelete="SET NULL"), nullable=True, index=True
    )
    work_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cost_actual: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    duration_hrs: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    incident: Mapped["Incident"] = relationship("Incident", back_populates="maintenance_records")
    contractor: Mapped[Optional["Contractor"]] = relationship("Contractor", back_populates="maintenance_records")


class HistoricalIncident(Base):
    __tablename__ = "historical_incidents"

    original_incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    incident_type: Mapped[str] = mapped_column(nullable=False, index=True)
    severity: Mapped[str] = mapped_column(nullable=False)
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lessons_learned: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolution_time_hrs: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tower_name: Mapped[Optional[str]] = mapped_column(nullable=True)
    archived_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
