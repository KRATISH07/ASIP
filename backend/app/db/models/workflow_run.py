import enum
import uuid
from typing import Optional
from sqlalchemy import String, Integer, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class WorkflowRunStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    compensating = "compensating"


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    status: Mapped[WorkflowRunStatus] = mapped_column(
        SAEnum(WorkflowRunStatus, name="workflow_run_status_enum"),
        nullable=False,
        default=WorkflowRunStatus.pending,
        index=True,
    )
    current_step: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    completed_steps: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    failed_at_step: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
