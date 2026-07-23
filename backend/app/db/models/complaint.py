import enum
import uuid
from typing import Optional
from sqlalchemy import String, Float, Text, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class ComplaintCategory(str, enum.Enum):
    lift = "lift"
    smell = "smell"
    plumbing = "plumbing"
    electrical = "electrical"
    noise = "noise"
    structural = "structural"
    parking = "parking"
    security = "security"
    other = "other"


class ComplaintPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class ComplaintStatus(str, enum.Enum):
    submitted = "submitted"
    under_review = "under_review"
    converted_to_incident = "converted_to_incident"
    assigned = "assigned"
    resolved = "resolved"
    rejected = "rejected"


# Category → IncidentType mapping used during complaint conversion
CATEGORY_TO_INCIDENT_TYPE: dict[str, str] = {
    "lift":       "abnormal_infrastructure",
    "smell":      "abnormal_infrastructure",
    "plumbing":   "water_pressure_drop",
    "electrical": "power_outage",
    "noise":      "abnormal_infrastructure",
    "structural": "abnormal_infrastructure",
    "parking":    "abnormal_infrastructure",
    "security":   "abnormal_infrastructure",
    "other":      "abnormal_infrastructure",
}


class Complaint(Base):
    """
    Resident-reported complaint that may be manually reviewed and converted
    into a formal Incident triggering the LangGraph AI workflow.

    resident_id is a plain UUID (not a FK) to avoid cross-schema constraints
    between the tenant schema (complaints) and public schema (users).
    assigned_manager_id likewise references public.users.id without FK constraint.
    """
    __tablename__ = "complaints"

    # Resident who filed the complaint (plain UUID — no cross-schema FK)
    resident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[ComplaintCategory] = mapped_column(
        SAEnum(ComplaintCategory, name="complaint_category_enum"),
        nullable=False,
        index=True,
    )
    priority: Mapped[ComplaintPriority] = mapped_column(
        SAEnum(ComplaintPriority, name="complaint_priority_enum"),
        nullable=False,
        default=ComplaintPriority.medium,
    )
    status: Mapped[ComplaintStatus] = mapped_column(
        SAEnum(ComplaintStatus, name="complaint_status_enum"),
        nullable=False,
        default=ComplaintStatus.submitted,
        index=True,
    )
    # FK to the incident created when this complaint is converted
    linked_incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    ai_confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # Manager assigned to handle this complaint (plain UUID — no cross-schema FK)
    assigned_manager_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationship to the linked incident (lazy loaded)
    linked_incident: Mapped[Optional["Incident"]] = relationship(
        "Incident", foreign_keys=[linked_incident_id]
    )
