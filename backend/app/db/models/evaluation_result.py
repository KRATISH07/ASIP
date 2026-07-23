"""
DB model for storing LLM-as-judge evaluation results.

One row per incident per evaluation run. Tracks all four rubric dimensions and
the aggregate quality score, enabling quality trend analysis over time.

Use cases:
  - Alert when rolling 7-day avg drops below 3.5 (prompt regression)
  - Identify which incident types produce lowest quality reports
  - Demonstrate to evaluators: "we track and improve prompt quality over time"
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, UUID
from app.db.base import Base


class EvaluationResultRecord(Base):
    """Stores LLM-as-judge rubric scores for a supervisor-generated report."""

    __tablename__ = "evaluation_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Link back to the incident (nullable — allows offline batch evaluation)
    incident_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Rubric dimension scores (1-5)
    root_cause_specificity = Column(Integer, nullable=False)
    action_plan_completeness = Column(Integer, nullable=False)
    priority_correctness = Column(Integer, nullable=False)
    factual_consistency = Column(Integer, nullable=False)

    # Aggregate
    overall_quality = Column(Float, nullable=False)
    flagged = Column(Boolean, nullable=False, default=False, index=True)

    # Optional judge reasoning text
    judge_reasoning = Column(Text, nullable=True)

    # Audit timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<EvaluationResult id={self.id} "
            f"incident={self.incident_id} "
            f"quality={self.overall_quality:.1f} "
            f"flagged={self.flagged}>"
        )
