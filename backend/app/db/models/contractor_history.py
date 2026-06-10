import uuid
from typing import Optional
from decimal import Decimal
from sqlalchemy import String, Float, Boolean, Text, Numeric, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class ContractorHistory(Base):
    __tablename__ = "contractor_history"

    contractor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contractors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    incident_type: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    repair_duration_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    repair_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    resolution_success: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    resident_feedback_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    contractor = relationship("Contractor", back_populates="history")
