"""
Pydantic schemas for LLM-as-judge evaluation results.

Each rubric dimension is scored 1-5:
  1 = very poor  |  3 = acceptable  |  5 = excellent

Scores below 3 in any dimension trigger the 'flagged' flag so operators can
review and improve the underlying prompt or routing logic.
"""
from typing import Optional
from pydantic import BaseModel, Field


class EvaluationScores(BaseModel):
    """Rubric scores returned by the judge LLM (1-5 per dimension)."""

    root_cause_specificity: int = Field(
        ge=1, le=5,
        description=(
            "Is the root cause specific and technical (5) or vague/generic (1)?"
        ),
    )
    action_plan_completeness: int = Field(
        ge=1, le=5,
        description=(
            "Are the action steps numbered, ordered, and actionable (5), "
            "or missing / unordered (1)?"
        ),
    )
    priority_correctness: int = Field(
        ge=1, le=5,
        description=(
            "Given the incident severity and residents affected, is the priority "
            "label correct (5) or clearly wrong (1)?"
        ),
    )
    factual_consistency: int = Field(
        ge=1, le=5,
        description=(
            "Are all claims in the report consistent with the incident data "
            "provided (5), or do they contain hallucinations/contradictions (1)?"
        ),
    )


class EvaluationResult(BaseModel):
    """Full evaluation output including aggregates and flag."""

    scores: EvaluationScores
    overall_quality: float = Field(
        ge=1.0, le=5.0,
        description="Mean of all four dimension scores.",
    )
    flagged: bool = Field(
        description="True when any dimension score < 3 — needs human review.",
    )
    judge_reasoning: Optional[str] = Field(
        None,
        description="Optional free-text explanation from the judge model.",
    )
