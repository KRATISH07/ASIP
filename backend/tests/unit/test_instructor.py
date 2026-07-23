import pytest
import unittest.mock as _mock
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import BaseModel, Field

from app.core.llm.fallback import invoke_with_fallback, _RULE_BASED_FALLBACKS
from app.agents.schemas import SupervisorReportSchema


class SimpleModel(BaseModel):
    name: str
    age: int = Field(ge=0)


class FakeOpenAILLM:
    def __init__(self, model_name="gpt-4", temperature=0.1):
        self.model_name = model_name
        self.temperature = temperature


@pytest.mark.asyncio
async def test_instructor_success():
    """Test that invoke_with_fallback uses instructor and returns dict when OpenAI is used."""
    mock_llm = FakeOpenAILLM()

    # Setup the mock instructor client and return object
    mock_client = MagicMock()
    mock_pydantic_res = SimpleModel(name="Test Agent", age=5)

    with (
        patch("instructor.from_openai", return_value=mock_client) as mock_from_openai,
        patch("app.config.settings.llm_provider", "openai")
    ):
        mock_client.chat.completions.create = AsyncMock(return_value=mock_pydantic_res)

        from langchain_core.prompts import ChatPromptTemplate
        dummy_prompt = ChatPromptTemplate.from_template("Hello {name}")

        result = await invoke_with_fallback(
            prompt=dummy_prompt,
            input_data={"name": "World"},
            primary_llm=mock_llm,
            response_model=SimpleModel,
        )

        assert result == {"name": "Test Agent", "age": 5}
        mock_from_openai.assert_called_once()
        mock_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_instructor_bypass_for_mocks():
    """Test that invoke_with_fallback bypasses instructor and uses invoke_chain if LLM is a mock."""
    mock_llm = AsyncMock() # A mock subclass that triggers is_mock check

    with (
        patch("app.core.llm.chain.invoke_chain", AsyncMock(return_value={"result": "bypass_success"})) as mock_invoke,
        patch("instructor.from_openai") as mock_from_openai,
        patch("app.config.settings.llm_provider", "openai")
    ):
        from langchain_core.prompts import ChatPromptTemplate
        dummy_prompt = ChatPromptTemplate.from_template("Hello {name}")

        result = await invoke_with_fallback(
            prompt=dummy_prompt,
            input_data={"name": "World"},
            primary_llm=mock_llm,
            response_model=SimpleModel,
        )

        assert result == {"result": "bypass_success"}
        mock_invoke.assert_awaited_once()
        mock_from_openai.assert_not_called()


@pytest.mark.asyncio
async def test_instructor_failure_graceful_fallback():
    """Test that if instructor call fails, the fallback hierarchy degrades to rule-based fallback."""
    mock_llm = FakeOpenAILLM()

    mock_client = MagicMock()

    with (
        patch("instructor.from_openai", return_value=mock_client),
        patch("app.config.settings.llm_provider", "openai"),
        patch("langchain_openai.ChatOpenAI", side_effect=Exception("Cannot construct fallback"))
    ):
        # chat completion raises exception (e.g. rate limit / validation failed)
        mock_client.chat.completions.create = AsyncMock(side_effect=ValueError("Validation failed"))

        from langchain_core.prompts import ChatPromptTemplate
        dummy_prompt = ChatPromptTemplate.from_template("Hello")

        result = await invoke_with_fallback(
            prompt=dummy_prompt,
            input_data={},
            primary_llm=mock_llm,
            response_model=SimpleModel,
            agent_type="supervisor",
        )

        # Should fall back to the supervisor rule-based fallback response
        assert result == _RULE_BASED_FALLBACKS["supervisor"]
        assert result["_degraded"] is True
