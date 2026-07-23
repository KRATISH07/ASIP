import uuid
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Tenant(Base):
    """
    Tenant database model for registering housing societies (tenants).
    Resides permanently inside the 'public' schema.
    """
    __tablename__ = "tenants"
    __table_args__ = {"schema": "public"}

    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    schema_name: Mapped[str] = mapped_column(String(63), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
