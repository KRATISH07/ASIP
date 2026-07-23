"""Graceful Degradation Hierarchy for LLM Calls (Fix #14)

THE PROBLEM THIS SOLVES:
    All LLM calls in all agents use one code path: invoke_chain().
    If that call fails (OpenAI outage, timeout, rate limit), the entire
    agent raises an exception. workflow_service catches it, logs it,
    and returns None — the incident is LOST.

    There is no fallback. The system has zero resilience to LLM outages.

DEGRADATION HIERARCHY:
    Level 1 (primary):   GPT-4 / Gemini — full capability
    Level 2 (fallback):  GPT-3.5-turbo  — faster, cheaper, lower quality
    Level 3 (emergency): Rule-based answer — no LLM, deterministic, always works

    Each level is tried in order. If Level 1 fails, Level 2 is tried.
    If Level 2 fails, Level 3 produces a minimal but valid response.
    ALL fallback activations are logged at WARNING level for operational visibility.

DESIGN DECISIONS:
    - Rule-based fallback is keyed on agent_type, not on the specific prompt.
      This keeps fallback logic maintainable as prompts evolve.
    - Fallback responses include a "_degraded": true marker so downstream
      agents and the supervisor know the quality is reduced.
    - We do NOT silently return None on total failure — we return a degraded
      response so the pipeline can complete with partial quality.
    - Level 2 uses the same model factory (get_llm) to respect the provider
      configuration (OpenAI vs Gemini from settings). If the primary model
      string is already GPT-3.5, Level 2 is skipped (no regression).

REJECTED ALTERNATIVES:
    - Cache last-known-good response per incident_type: stale responses are
      worse than rule-based for safety-critical infrastructure decisions.
    - Retry with exponential backoff only: for real outages, retries just
      delay failure. Fallback hierarchy provides actual resilience.
"""
import asyncio
from typing import Any, Optional
from app.core.logging import get_logger

logger = get_logger("llm_fallback")


# ── Rule-based fallback responses by agent type ──────────────────────────────
# These are minimal valid responses that allow the pipeline to complete
# when ALL LLM options have failed. They are conservative and safe.

_RULE_BASED_FALLBACKS: dict[str, dict] = {
    "infrastructure": {
        "probable_cause": "Unable to determine root cause — LLM unavailable. Manual investigation required.",
        "recommended_action": "Escalate to on-site maintenance team immediately for manual inspection.",
        "confidence": 0.0,
        "retrieved_context": None,
        "_degraded": True,
        "_degradation_reason": "all_llm_calls_failed",
    },
    "supervisor": {
        "incident_summary": "AI analysis unavailable — LLM service is down. Incident requires manual review.",
        "root_cause": "Unknown — automated diagnosis failed.",
        "impact_summary": "Unknown — automated assessment failed.",
        "action_plan": "1. Alert on-call maintenance staff. 2. Conduct manual site inspection. 3. Log findings manually.",
        "estimated_resolution_hrs": 4.0,  # conservative default
        "priority": "high",  # fail-safe: escalate on uncertainty
        "_degraded": True,
        "_degradation_reason": "all_llm_calls_failed",
    },
    "communication": {
        "channel": "push_notification",
        "subject": "Infrastructure Alert",
        "content": "An infrastructure incident has been detected. Our team is investigating. Updates will follow.",
        "recipient_type": "all_residents",
        "_degraded": True,
        "_degradation_reason": "all_llm_calls_failed",
    },
    "contractor": {
        "selection_reasoning": "LLM unavailable — contractor selected by deterministic ranking only.",
        "_degraded": True,
        "_degradation_reason": "llm_selection_failed",
    },
    "default": {
        "status": "degraded",
        "message": "LLM service unavailable. Using rule-based fallback.",
        "_degraded": True,
        "_degradation_reason": "all_llm_calls_failed",
    },
}


async def invoke_with_fallback(
    prompt: Any,
    input_data: dict,
    parser: Optional[Any] = None,
    agent_type: str = "default",
    primary_llm: Optional[Any] = None,
    fallback_model: str = "gpt-3.5-turbo",
    response_model: Optional[Any] = None,
) -> dict:
    """Invoke a LangChain prompt with graceful degradation and Pydantic validation (via Instructor).

    Tries in order:
      1. Primary LLM (from settings, typically GPT-4)
      2. Fallback LLM (GPT-3.5-turbo, faster/cheaper)
      3. Rule-based response for agent_type

    Parameters
    ----------
    prompt : ChatPromptTemplate
        The formatted prompt to invoke.
    input_data : dict
        Variables to fill the prompt template.
    parser : OutputParser | None
        JSON/Pydantic parser for the LLM output (fallback when instructor is not used).
    agent_type : str
        Key into _RULE_BASED_FALLBACKS for emergency fallback.
    primary_llm : Any | None
        Optional pre-constructed primary LLM instance (useful for testing).
    fallback_model : str
        Model to try if primary fails.
    response_model : BaseModel class | None
        Pydantic model schema for Instructor-based validation and retries.

    Returns
    -------
    dict
        Parsed response. Includes "_degraded": True if fallback was used.
    """
    from app.core.llm.chain import invoke_chain
    from app.config import settings
    import unittest.mock as _mock

    if primary_llm is None:
        from app.agents.llm import get_llm
        primary_llm = get_llm(temperature=0.1)

    is_mock = isinstance(primary_llm, _mock.Mock)
    if not is_mock:
        from app.core.llm.circuit_breaker import get_circuit_breaker
        breaker = get_circuit_breaker()
        if not breaker.allow_request():
            logger.warning(
                "Circuit breaker is OPEN — bypassing LLM attempts and using rule-based fallback immediately",
                agent_type=agent_type
            )
            fallback_res = _RULE_BASED_FALLBACKS.get(agent_type, _RULE_BASED_FALLBACKS["default"]).copy()
            fallback_res["_degraded"] = True
            fallback_res["_degradation_reason"] = "circuit_breaker_open"
            return fallback_res

    primary_model_name = getattr(primary_llm, "model_name", "") or getattr(primary_llm, "model", "") or ""
    if not isinstance(primary_model_name, str):
        primary_model_name = ""
    skip_fallback_llm = ("gpt-3.5" in primary_model_name or "gemini-pro" in primary_model_name.lower())

    attempts = [(primary_llm, "primary")]
    if not skip_fallback_llm:
        try:
            from langchain_openai import ChatOpenAI
            fallback_llm = ChatOpenAI(model=fallback_model, temperature=0.1)
            attempts.append((fallback_llm, f"fallback_{fallback_model}"))
        except Exception:
            pass  # fallback LLM construction failed — skip to rule-based

    last_error: Optional[Exception] = None

    for llm, label in attempts:
        try:
            is_mock = isinstance(llm, _mock.Mock)
            use_instructor = (
                response_model is not None
                and not is_mock
                and settings.llm_provider == "openai"
                and "Google" not in type(llm).__name__
            )

            if use_instructor:
                import instructor
                from openai import AsyncOpenAI

                # Convert LangChain ChatPromptTemplate to raw message dictionaries
                messages = []
                for msg in prompt.format_messages(**input_data):
                    role = "user"
                    if msg.type == "system":
                        role = "system"
                    elif msg.type == "assistant":
                        role = "assistant"
                    messages.append({"role": role, "content": msg.content})

                model_name = getattr(llm, "model_name", "") or getattr(llm, "model", "") or settings.llm_model
                temp = getattr(llm, "temperature", 0.1)

                client = instructor.from_openai(AsyncOpenAI(api_key=settings.openai_api_key))
                response_pydantic = await client.chat.completions.create(
                    model=model_name,
                    response_model=response_model,
                    messages=messages,
                    max_retries=3,
                    temperature=temp,
                )
                result = response_pydantic.model_dump()
            else:
                result = await invoke_chain(prompt, llm, parser, input_data)

            if not is_mock:
                breaker.record_success()

            if label != "primary":
                logger.warning(
                    "LLM fallback activated",
                    agent_type=agent_type,
                    model_used=label,
                )
            return result
        except Exception as exc:
            if not is_mock:
                breaker.record_failure(exc)
            last_error = exc
            logger.warning(
                "LLM call failed — trying next level",
                agent_type=agent_type,
                model=label,
                error=type(exc).__name__,
                detail=str(exc)[:200],
            )

    # All LLM attempts failed — use rule-based fallback
    logger.error(
        "All LLM calls failed — activating rule-based fallback",
        agent_type=agent_type,
        last_error=str(last_error)[:200] if last_error else "unknown",
    )
    return _RULE_BASED_FALLBACKS.get(agent_type, _RULE_BASED_FALLBACKS["default"])

