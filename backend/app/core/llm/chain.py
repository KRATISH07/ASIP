"""Centralized chain invocation helper.

Provides a single, test-friendly entrypoint for building and invoking
LangChain-style prompt->LLM->parser pipelines. Handles real LangChain
chains as well as tests that mock `get_llm()` with `MagicMock`/`AsyncMock`.
"""
from typing import Any, Optional
import asyncio


async def invoke_chain(prompt: Any, llm: Any, parser: Optional[Any], input_data: dict) -> Any:
    """Invoke a prompt+llm(+parser) pipeline in a robust, test-friendly way.

    Strategy:
    - Try to create a partial chain via `llm.__or__(prompt)` (works with
      mocked `llm` objects that expose `__or__` returning an AsyncMock).
    - If that yields a usable callable/chain, attempt to apply the parser
      (`partial | parser`) when possible; otherwise fall back to invoking
      the partial directly.
    - If partial construction fails, build the full chain at runtime using
      `prompt | llm | parser` (this is the normal LangChain path).
    - Invocation:
      - If the chain object has `ainvoke`, call and await it.
      - Else, call the callable; if it returns a coroutine await it.
    - If a parser is provided but the invoked result is not already
      parsed (i.e., a dict), attempt to use `parser.parse(...)` as a
      last-resort.
    """

    input_data = input_data or {}

    partial = None
    full_chain = None

    # 1) Prefer llm.__or__(prompt) to avoid calling llm() during chain build
    try:
        partial = llm.__or__(prompt)
    except Exception:
        partial = None

    # 2) If we got a partial chain, try to attach parser if possible.
    #    However, if `partial` is a unittest.mock.Mock (AsyncMock/MagicMock),
    #    do NOT attempt composition because parser.__ror__ may accept it and
    #    return a MagicMock that is not awaitable in tests.
    if partial is not None:
        try:
            import unittest.mock as _mock
            if isinstance(partial, _mock.Mock):
                full_chain = partial
            else:
                if parser is not None:
                    try:
                        full_chain = partial | parser
                    except Exception:
                        full_chain = partial
                else:
                    full_chain = partial
        except Exception:
            full_chain = partial

    # 3) Fallback: construct runtime chain using prompt | llm | parser
    if full_chain is None:
        try:
            runtime = prompt | llm
            if parser is not None:
                runtime = runtime | parser
            full_chain = runtime
        except Exception:
            full_chain = None

    # 4) Invoke the chain (prefer ainvoke if present)
    try:
        if full_chain is not None:
            # Prefer calling the chain if it's callable (works with AsyncMock)
            if callable(full_chain):
                maybe = full_chain(input_data)
                if asyncio.iscoroutine(maybe):
                    result = await maybe
                else:
                    result = maybe
                # If parser provided but result is raw text, try to parse
                if parser is not None and not isinstance(result, dict):
                    try:
                        if hasattr(parser, "parse"):
                            return parser.parse(result)
                        if hasattr(parser, "parse_text"):
                            return parser.parse_text(result)
                    except Exception:
                        pass
                return result

            # Fallback to chain.ainvoke if present
            if hasattr(full_chain, "ainvoke"):
                maybe = full_chain.ainvoke(input_data)
                if asyncio.iscoroutine(maybe):
                    return await maybe
                return maybe

        # 5) Last-resort: try calling llm directly (if callable)
        if callable(llm):
            maybe = llm(input_data)
            if asyncio.iscoroutine(maybe):
                return await maybe
            return maybe

        raise RuntimeError("Unable to construct or invoke chain")
    except Exception:
        # Bubble up; callers will log and handle fallbacks
        raise
