import enum
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Float, DateTime, Text, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class IncidentType(str, enum.Enum):
    water_pressure_drop = "water_pressure_drop"
    water_shortage = "water_shortage"
    tank_overflow = "tank_overflow"
    power_outage = "power_outage"
    power_overload = "power_overload"
    abnormal_infrastructure = "abnormal_infrastructure"


class IncidentSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class IncidentStatus(str, enum.Enum):
    detected = "detected"
    analyzing = "analyzing"
    action_planned = "action_planned"
    in_progress = "in_progress"
    resolved = "resolved"
    escalated = "escalated"


class Incident(Base):
    __tablename__ = "incidents"

    type: Mapped[IncidentType] = mapped_column(
        SAEnum(IncidentType, name="incident_type_enum"), nullable=False, index=True
    )
    severity: Mapped[IncidentSeverity] = mapped_column(
        SAEnum(IncidentSeverity, name="incident_severity_enum"), nullable=False, index=True
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[IncidentStatus] = mapped_column(
        SAEnum(IncidentStatus, name="incident_status_enum"),
        nullable=False,
        default=IncidentStatus.detected,
        index=True,
    )
    tower_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("towers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sensor_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ai_decision: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    tower: Mapped[Optional["Tower"]] = relationship("Tower", back_populates="incidents")
    contractor_assignment: Mapped[Optional["ContractorAssignment"]] = relationship(
        "ContractorAssignment", back_populates="incident", uselist=False
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="incident"
    )
    agent_logs: Mapped[List["AgentLog"]] = relationship(
        "AgentLog", back_populates="incident"
    )
    maintenance_records: Mapped[List["MaintenanceRecord"]] = relationship(
        "MaintenanceRecord", back_populates="incident"
    )
