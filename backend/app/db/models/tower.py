import enum
import uuid
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class InfrastructureType(str, enum.Enum):
    water = "water"
    power = "power"
    both = "both"


class Tower(Base):
    __tablename__ = "towers"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    floors: Mapped[int] = mapped_column(Integer, nullable=False)
    total_apartments: Mapped[int] = mapped_column(Integer, nullable=False)
    infrastructure_type: Mapped[InfrastructureType] = mapped_column(
        SAEnum(InfrastructureType, name="infrastructure_type_enum"),
        nullable=False,
        default=InfrastructureType.both,
    )
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    apartments: Mapped[List["Apartment"]] = relationship(
        "Apartment", back_populates="tower", cascade="all, delete-orphan"
    )
    incidents: Mapped[List["Incident"]] = relationship(
        "Incident", back_populates="tower"
    )
