import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def reset_circuit_breaker():
    from app.core.llm.circuit_breaker import get_circuit_breaker
    get_circuit_breaker().reset()
    yield
    get_circuit_breaker().reset()

