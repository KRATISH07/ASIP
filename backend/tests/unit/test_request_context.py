import asyncio
import pytest
from app.core.request_context import (
    set_request_context,
    get_trace_id,
    get_request_context,
)

def test_request_context_defaults():
    """Outside of async context, get_trace_id should return 'unset'."""
    assert get_trace_id() == "unset"
    ctx = get_request_context()
    assert ctx["trace_id"] == "unset"
    assert ctx["user_id"] is None


@pytest.mark.asyncio
async def test_request_context_propagation():
    """Test that context is isolated and propagates across async tasks."""
    
    async def worker_1():
        # Set context in task 1
        tid = set_request_context(trace_id="task_1_trace", user_id="user_1")
        assert tid == "task_1_trace"
        assert get_trace_id() == "task_1_trace"
        assert get_request_context()["user_id"] == "user_1"
        await asyncio.sleep(0.05)
        # Verify it persisted after sleep (async context propagation)
        assert get_trace_id() == "task_1_trace"

    async def worker_2():
        await asyncio.sleep(0.01)
        # Verify task 2 does not see task 1's context
        assert get_trace_id() == "unset"
        set_request_context(trace_id="task_2_trace", user_id="user_2")
        assert get_trace_id() == "task_2_trace"
        await asyncio.sleep(0.05)
        assert get_trace_id() == "task_2_trace"

    # Run concurrently
    await asyncio.gather(worker_1(), worker_2())
    # Outside, context should remain unset (isolated from workers)
    assert get_trace_id() == "unset"
