"""Request Context — Correlation ID Propagation (Fix #5)

THE PROBLEM THIS SOLVES:
    There is no trace ID that propagates from the HTTP request through
    the LangGraph pipeline through every agent log. When a request takes
    45 seconds, you cannot determine which agent, which LLM call, or which
    DB operation was responsible.

    The agent_logs table exists but _save_agent_log() is never called.
    elapsed_ms on workflow_service is the entire observability surface.

    This makes production debugging impossible. You cannot answer:
    "Which component caused this request to take 58 seconds?"

SOLUTION:
    Python contextvars — a standard library mechanism for request-scoped
    context that propagates through async call chains without modifying
    function signatures.

    set_request_context() is called at the HTTP layer with a trace_id.
    get_trace_id() is called from any agent, service, or log statement.
    No function signature changes required — no ASIPState pollution.

DESIGN:
    - Uses contextvars.ContextVar — built into Python 3.7+, no dependencies
    - Works correctly across asyncio task boundaries (unlike threading.local)
    - Trace ID is either client-supplied (X-Request-ID header) or generated
    - The same trace_id is also injected into ASIPState["trace_id"] so it
      appears in any structured log that includes the state dict
"""
import uuid
from contextvars import ContextVar
from typing import Optional

# Module-level ContextVar — one per Python process, zero per-request overhead
_request_context: ContextVar[dict] = ContextVar(
    "request_context",
    default={"trace_id": "unset", "user_id": None},
)


def set_request_context(trace_id: Optional[str] = None, user_id: Optional[str] = None) -> str:
    """Set the request-scoped context. Call this at the HTTP endpoint layer.

    Returns the trace_id (generated if not provided) so it can be echoed
    in the HTTP response via X-Request-ID header.
    """
    tid = trace_id or str(uuid.uuid4())
    _request_context.set({"trace_id": tid, "user_id": user_id})
    return tid


def get_trace_id() -> str:
    """Return the trace ID for the current async context.

    Returns "unset" if called outside an HTTP request (e.g., in background
    tasks, tests, or CLI scripts). Never raises.
    """
    return _request_context.get().get("trace_id", "unset")


def get_request_context() -> dict:
    """Return the full request context dict."""
    return _request_context.get()
