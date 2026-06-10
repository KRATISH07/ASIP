import uuid
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import String, Float, Boolean, Text, Numeric, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Contractor(Base):
    __tablename__ = "contractors"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    specializations: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list
    )  # ["water", "electrical", "civil"]
    rating: Mapped[float] = mapped_column(Float, nullable=False, default=3.0)
    avg_response_time_hrs: Mapped[float] = mapped_column(Float, nullable=False, default=4.0)
    total_jobs: Mapped[int] = mapped_column(nullable=False, default=0)
    success_rate: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    contact_info: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )  # {"phone": "...", "email": "...", "address": "..."}
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    assignments: Mapped[List["ContractorAssignment"]] = relationship(
        "ContractorAssignment", back_populates="contractor"
    )
    maintenance_records: Mapped[List["MaintenanceRecord"]] = relationship(
        "MaintenanceRecord", back_populates="contractor"
    )
    history: Mapped[List["ContractorHistory"]] = relationship(
        "ContractorHistory", back_populates="contractor"
    )


class ContractorAssignment(Base):
    __tablename__ = "contractor_assignments"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contractor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contractors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    estimated_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    estimated_time_hrs: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    selection_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    incident: Mapped["Incident"] = relationship("Incident", back_populates="contractor_assignment")
    contractor: Mapped["Contractor"] = relationship("Contractor", back_populates="assignments")
