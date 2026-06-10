import enum
import uuid
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class ResidentRole(str, enum.Enum):
    owner = "owner"
    tenant = "tenant"


class Apartment(Base):
    __tablename__ = "apartments"

    tower_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("towers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    flat_number: Mapped[str] = mapped_column(String(20), nullable=False)
    floor: Mapped[int] = mapped_column(Integer, nullable=False)
    occupied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    tower: Mapped["Tower"] = relationship("Tower", back_populates="apartments")
    residents: Mapped[List["Resident"]] = relationship(
        "Resident", back_populates="apartment", cascade="all, delete-orphan"
    )


class Resident(Base):
    __tablename__ = "residents"

    apartment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("apartments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    role: Mapped[ResidentRole] = mapped_column(
        SAEnum(ResidentRole, name="resident_role_enum"),
        default=ResidentRole.tenant,
        nullable=False,
    )
    notification_prefs: Mapped[dict] = mapped_column(
        # JSONB: {"email": true, "sms": false, "push": true}
        __import__("sqlalchemy.dialects.postgresql", fromlist=["JSONB"]).JSONB,
        default=lambda: {"email": True, "sms": False, "push": True},
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    apartment: Mapped["Apartment"] = relationship("Apartment", back_populates="residents")
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="recipient"
    )
