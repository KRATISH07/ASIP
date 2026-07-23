import pytest
from unittest.mock import AsyncMock, patch
from app.core.llm.fallback import invoke_with_fallback, _RULE_BASED_FALLBACKS

@pytest.mark.asyncio
async def test_fallback_level_1_success():
    """Test that fallback returns primary LLM result if it succeeds."""
    mock_primary = AsyncMock()
    mock_primary.model_name = "gpt-4"

    # Mock invoke_chain to return a successful dict
    with patch("app.core.llm.chain.invoke_chain", AsyncMock(return_value={"result": "primary_success"})) as mock_invoke:
        result = await invoke_with_fallback(
            prompt="Dummy Prompt",
            input_data={},
            primary_llm=mock_primary,
        )
        assert result == {"result": "primary_success"}
        mock_invoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_fallback_level_2_success():
    """Test that fallback uses fallback LLM if primary fails."""
    mock_primary = AsyncMock()
    mock_primary.model_name = "gpt-4"

    mock_fallback_llm = AsyncMock()
    mock_fallback_llm.model_name = "gpt-3.5-turbo"

    # We want first call of invoke_chain (primary) to raise, and second (fallback) to succeed
    side_effects = [Exception("Primary Failed"), {"result": "fallback_success"}]

    with (
        patch("app.core.llm.chain.invoke_chain", AsyncMock(side_effect=side_effects)) as mock_invoke,
        patch("langchain_openai.ChatOpenAI", return_value=mock_fallback_llm)
    ):
        result = await invoke_with_fallback(
            prompt="Dummy Prompt",
            input_data={},
            primary_llm=mock_primary,
            fallback_model="gpt-3.5-turbo",
        )
        assert result == {"result": "fallback_success"}
        assert mock_invoke.await_count == 2


@pytest.mark.asyncio
async def test_fallback_level_3_rule_based():
    """Test that fallback defaults to rule-based fallback if all LLMs fail."""
    mock_primary = AsyncMock()
    mock_primary.model_name = "gpt-4"

    # All calls to invoke_chain fail
    with (
        patch("app.core.llm.chain.invoke_chain", AsyncMock(side_effect=Exception("Failed"))),
        patch("langchain_openai.ChatOpenAI", side_effect=Exception("Cannot construct"))
    ):
        result = await invoke_with_fallback(
            prompt="Dummy Prompt",
            input_data={},
            primary_llm=mock_primary,
            agent_type="infrastructure",
        )
        # Should return rule-based fallback for infrastructure
        expected = _RULE_BASED_FALLBACKS["infrastructure"]
        assert result == expected
        assert result["_degraded"] is True
