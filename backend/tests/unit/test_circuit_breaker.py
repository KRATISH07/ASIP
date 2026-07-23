import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import BaseModel

from app.core.llm.circuit_breaker import get_circuit_breaker, CircuitBreaker
from app.core.llm.fallback import invoke_with_fallback, _RULE_BASED_FALLBACKS


class SimpleModel(BaseModel):
    name: str


class FakeOpenAILLM:
    def __init__(self, model_name="gpt-4", temperature=0.1):
        self.model_name = model_name
        self.temperature = temperature


def test_circuit_breaker_state_transitions():
    """Verify that the circuit breaker correctly cycles through CLOSED, OPEN, and HALF-OPEN states."""
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout_seconds=2.0)
    
    assert breaker.state == "CLOSED"
    assert breaker.allow_request() is True

    # 1. Record 2 failures - should still be CLOSED
    breaker.record_failure(ValueError("Error 1"))
    breaker.record_failure(ValueError("Error 2"))
    assert breaker.state == "CLOSED"
    assert breaker.allow_request() is True

    # 2. Record 3rd failure - should trip to OPEN
    breaker.record_failure(ValueError("Error 3"))
    assert breaker.state == "OPEN"
    assert breaker.allow_request() is False

    # 3. Wait/mock time to bypass timeout
    with patch("time.time", return_value=time.time() + 3.0):
        # allow_request check should transition state to HALF-OPEN
        assert breaker.allow_request() is True
        assert breaker.state == "HALF-OPEN"

        # 4. Recording success in HALF-OPEN closes the breaker
        breaker.record_success()
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 0


def test_circuit_breaker_half_open_failure():
    """Verify that a single failure in HALF-OPEN state immediately trips the breaker back to OPEN."""
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout_seconds=2.0)
    breaker.record_failure(ValueError("Error 1"))
    breaker.record_failure(ValueError("Error 2"))
    breaker.record_failure(ValueError("Error 3"))
    assert breaker.state == "OPEN"

    with patch("time.time", return_value=time.time() + 3.0):
        assert breaker.allow_request() is True
        assert breaker.state == "HALF-OPEN"

        # A single failure in HALF-OPEN trips the circuit breaker immediately
        breaker.record_failure(ValueError("Error 4"))
        assert breaker.state == "OPEN"
        assert breaker.allow_request() is False


@pytest.mark.asyncio
async def test_fallback_integration_with_circuit_breaker():
    """Verify that invoke_with_fallback short-circuits LLM calls when circuit is OPEN."""
    breaker = get_circuit_breaker()
    breaker.reset()

    # 1. Trip the circuit breaker by recording 5 failures
    for i in range(5):
        breaker.record_failure(Exception(f"Failure {i}"))
    
    assert breaker.state == "OPEN"

    # 2. Invoke with fallback - should immediately return the degraded rule-based fallback
    from langchain_core.prompts import ChatPromptTemplate
    dummy_prompt = ChatPromptTemplate.from_template("Hello")
    mock_llm = FakeOpenAILLM()

    with (
        patch("app.config.settings.llm_provider", "openai"),
        patch("instructor.from_openai") as mock_instructor
    ):
        result = await invoke_with_fallback(
            prompt=dummy_prompt,
            input_data={},
            primary_llm=mock_llm,
            response_model=SimpleModel,
            agent_type="infrastructure",
        )

        # Assert that the instructor client was never called (short-circuited)
        mock_instructor.assert_not_called()
        
        expected = _RULE_BASED_FALLBACKS["infrastructure"].copy()
        expected["_degraded"] = True
        expected["_degradation_reason"] = "circuit_breaker_open"
        assert result == expected

    # Reset breaker after testing
    breaker.reset()
