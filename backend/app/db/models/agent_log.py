import uuid
from typing import Optional
from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class AgentLog(Base):
    __tablename__ = "agent_logs"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    input_payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    output_payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="success", nullable=False)

    # Relationships
    incident: Mapped["Incident"] = relationship("Incident", back_populates="agent_logs")
