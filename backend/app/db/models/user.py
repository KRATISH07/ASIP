import enum
import uuid
from typing import Optional
from sqlalchemy import String, Boolean, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    maintenance = "maintenance"
    # New roles for Real Society Operations phase
    resident = "resident"
    sensor_gateway = "sensor_gateway"
    contractor = "contractor"


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role_enum"),
        default=UserRole.manager,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Optional link to the residents table (set when role=resident).
    # Plain UUID — no FK constraint to avoid cross-schema FK from public→tenant schema.
    resident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Optional link to the contractors table (set when role=contractor).
    # Plain UUID — no FK constraint to avoid cross-schema FK from public→tenant schema.
    contractor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
