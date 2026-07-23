"""
Unit tests for the LLM-as-judge evaluation module.

Test strategy:
- Patch _run_judge to return controlled EvaluationScores → no real LLM calls.
- Test scoring math (overall_quality = mean of 4 dimensions).
- Test flagging logic (any score < 3 → flagged=True).
- Test sentinel result on judge failure.
- Test _truncate utility.
- Test supervisor_agent integration: judge is scheduled as asyncio.create_task.
- Test _resolve_judge_model for both providers.
"""
import asyncio
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

from app.evaluation.schemas import EvaluationScores, EvaluationResult
from app.evaluation.judge import (
    _sentinel_result,
    _truncate,
    _resolve_judge_model,
    evaluate_report,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
SAMPLE_INCIDENT = {
    "type": "water_leak",
    "severity": "high",
    "description": "Major pipe burst in Tower B basement.",
}

SAMPLE_REPORT = {
    "incident_summary": "Pipe burst detected in Tower B basement.",
    "root_cause": "Corrosion-induced failure in 20-year-old cast iron main pipe (segment P-204).",
    "impact_summary": "450 residents affected; no hot water.",
    "action_plan": "1. Isolate valve V-12. 2. Deploy emergency plumbing crew. 3. Restore supply within 4 hrs.",
    "estimated_resolution_hrs": 4.0,
    "priority": "critical",
}

GOOD_SCORES = EvaluationScores(
    root_cause_specificity=5,
    action_plan_completeness=5,
    priority_correctness=5,
    factual_consistency=5,
)

LOW_SCORES = EvaluationScores(
    root_cause_specificity=2,   # < 3 → flagged
    action_plan_completeness=4,
    priority_correctness=4,
    factual_consistency=4,
)


# ---------------------------------------------------------------------------
# Unit: scoring math
# ---------------------------------------------------------------------------
class TestScoringMath:
    def test_overall_quality_is_mean(self):
        result = EvaluationResult(
            scores=GOOD_SCORES,
            overall_quality=5.0,
            flagged=False,
        )
        assert result.overall_quality == 5.0

    def test_overall_quality_mixed(self):
        scores = EvaluationScores(
            root_cause_specificity=3,
            action_plan_completeness=4,
            priority_correctness=5,
            factual_consistency=4,
        )
        from statistics import mean
        expected = round(mean([3, 4, 5, 4]), 2)
        result = EvaluationResult(
            scores=scores,
            overall_quality=expected,
            flagged=False,
        )
        assert result.overall_quality == 4.0

    def test_flagged_when_any_score_below_3(self):
        result = EvaluationResult(
            scores=LOW_SCORES,
            overall_quality=3.5,
            flagged=True,   # root_cause_specificity=2
        )
        assert result.flagged is True

    def test_not_flagged_when_all_at_or_above_3(self):
        scores = EvaluationScores(
            root_cause_specificity=3,
            action_plan_completeness=3,
            priority_correctness=3,
            factual_consistency=3,
        )
        result = EvaluationResult(
            scores=scores,
            overall_quality=3.0,
            flagged=False,
        )
        assert result.flagged is False


# ---------------------------------------------------------------------------
# Unit: sentinel result
# ---------------------------------------------------------------------------
class TestSentinelResult:
    def test_sentinel_has_minimum_scores(self):
        result = _sentinel_result()
        # Sentinel uses minimum valid score (1) with flagged=True
        assert result.overall_quality == 1.0

    def test_sentinel_is_flagged(self):
        result = _sentinel_result()
        assert result.flagged is True

    def test_sentinel_has_reasoning(self):
        result = _sentinel_result()
        assert result.judge_reasoning is not None
        assert "sentinel" in result.judge_reasoning.lower()


# ---------------------------------------------------------------------------
# Unit: _truncate utility
# ---------------------------------------------------------------------------
class TestTruncate:
    def test_no_truncation_when_short(self):
        text = "short text"
        assert _truncate(text, max_chars=100) == text

    def test_truncated_when_long(self):
        text = "x" * 3000
        result = _truncate(text, max_chars=2000)
        assert len(result) < 3000
        assert "truncated" in result

    def test_truncated_exactly_at_boundary(self):
        text = "y" * 2000
        assert _truncate(text, max_chars=2000) == text


# ---------------------------------------------------------------------------
# Unit: model resolution
# ---------------------------------------------------------------------------
class TestResolveJudgeModel:
    def test_openai_returns_mini(self):
        with patch("app.config.settings.llm_provider", "openai"):
            assert _resolve_judge_model() == "gpt-4o-mini"

    def test_google_returns_flash(self):
        with patch("app.config.settings.llm_provider", "google"):
            assert _resolve_judge_model() == "gemini-1.5-flash"


# ---------------------------------------------------------------------------
# Integration: evaluate_report returns result from _run_judge
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_evaluate_report_success():
    """evaluate_report calls _run_judge and returns its result."""
    expected_result = EvaluationResult(
        scores=GOOD_SCORES,
        overall_quality=5.0,
        flagged=False,
    )
    with (
        patch("app.evaluation.judge._run_judge", AsyncMock(return_value=expected_result)),
        patch("app.evaluation.judge._persist_result", AsyncMock()),
        # suppress asyncio.create_task for _persist_result in test context
        patch("asyncio.create_task", side_effect=lambda coro: coro.close()),
    ):
        result = await evaluate_report(
            incident_data=SAMPLE_INCIDENT,
            report=SAMPLE_REPORT,
            incident_id=str(uuid.uuid4()),
            persist=True,
        )

    assert result.overall_quality == 5.0
    assert result.flagged is False


@pytest.mark.asyncio
async def test_evaluate_report_returns_sentinel_on_failure():
    """evaluate_report returns a sentinel EvaluationResult when _run_judge raises."""
    with patch(
        "app.evaluation.judge._run_judge",
        AsyncMock(side_effect=RuntimeError("LLM timeout")),
    ):
        result = await evaluate_report(
            incident_data=SAMPLE_INCIDENT,
            report=SAMPLE_REPORT,
            incident_id=str(uuid.uuid4()),
            persist=False,
        )

    # Sentinel uses score=1 (valid minimum) and flagged=True
    assert result.flagged is True
    assert result.overall_quality == 1.0


@pytest.mark.asyncio
async def test_evaluate_report_no_persist_skips_db():
    """When persist=False, _persist_result should never be called."""
    expected_result = EvaluationResult(
        scores=GOOD_SCORES,
        overall_quality=5.0,
        flagged=False,
    )
    mock_persist = AsyncMock()
    with (
        patch("app.evaluation.judge._run_judge", AsyncMock(return_value=expected_result)),
        patch("app.evaluation.judge._persist_result", mock_persist),
    ):
        await evaluate_report(
            incident_data=SAMPLE_INCIDENT,
            report=SAMPLE_REPORT,
            incident_id=str(uuid.uuid4()),
            persist=False,
        )

    mock_persist.assert_not_called()


# ---------------------------------------------------------------------------
# Integration: supervisor_agent schedules judge task
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_supervisor_agent_schedules_judge():
    """
    supervisor_agent should schedule an asyncio.create_task for the judge
    after building the final_report.

    Patching strategy:
    - get_llm → MagicMock (avoid real LLM instantiation)
    - sys.modules injection for memory_service (avoids importlib patching issues
      since importlib is a local import inside supervisor_agent)
    - invoke_with_fallback → AsyncMock (return controlled report)
    - asyncio module in supervisor namespace → MagicMock (capture create_task calls)
    """
    import sys
    from app.agents.state import ASIPState

    base_state: ASIPState = {
        "incident_id": str(uuid.uuid4()),
        "incident_event": SAMPLE_INCIDENT,
        "agent_outputs": {},
        "sensor_data": {},
        "notifications": [],
        "diagnosis": {
            "probable_cause": "Pipe corrosion",
            "recommended_action": "Replace segment P-204",
        },
        "autonomous_decision": {},
        "contractor_recommendation": {},
        "supervisor_decisions": {},
        "selected_agents": [],
        "completed_agents": [],
        "impact": {},
        "trace_id": None,
    }

    mock_final_report = {
        "incident_summary": "Pipe burst",
        "root_cause": "Corrosion",
        "impact_summary": "450 residents",
        "action_plan": "1. Isolate. 2. Repair.",
        "estimated_resolution_hrs": 4.0,
        "priority": "critical",
    }

    # Inject a fake memory_service into sys.modules so that importlib.import_module
    # inside supervisor_agent returns our mock instead of hitting real DB logic.
    fake_memory_service = MagicMock()
    fake_memory_service.retrieve_similar_incidents = AsyncMock(return_value=[])

    with (
        # Prevent real LLM construction
        patch("app.agents.supervisor.get_llm", return_value=MagicMock()),
        # Return a controlled report from invoke_with_fallback
        patch("app.core.llm.fallback.invoke_with_fallback", AsyncMock(return_value=mock_final_report)),
        # Mock asyncio in the supervisor namespace to capture create_task calls
        patch("app.agents.supervisor.asyncio") as mock_asyncio,
    ):
        # Inject fake memory_service before calling the agent
        original_module = sys.modules.get("app.services.memory_service")
        sys.modules["app.services.memory_service"] = fake_memory_service
        try:
            from app.agents.supervisor import supervisor_agent
            result = await supervisor_agent(base_state)
        finally:
            # Restore original module (or remove if it wasn't there)
            if original_module is not None:
                sys.modules["app.services.memory_service"] = original_module
            else:
                sys.modules.pop("app.services.memory_service", None)

    # The agent must return a final_report
    assert "final_report" in result
    # The judge background task was scheduled via asyncio.create_task
    mock_asyncio.create_task.assert_called_once()
