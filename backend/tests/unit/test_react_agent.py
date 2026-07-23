import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import AIMessage
from app.agents.infrastructure import (
    infrastructure_agent, 
    _run_react_loop,
    search_knowledge_base,
    retrieve_historical_incidents,
    get_sensor_history
)
from app.agents.state import ASIPState

@pytest.mark.asyncio
async def test_search_knowledge_base_tool():
    # Test RAG retrieval tool
    with patch("app.rag.retriever.get_retriever") as mock_get_retriever:
        mock_retriever = MagicMock()
        mock_doc = MagicMock()
        mock_doc.page_content = "Maintenance procedure for pumps: check pressure levels."
        mock_retriever.invoke.return_value = [mock_doc]
        mock_get_retriever.return_value = mock_retriever
        
        result = await search_knowledge_base.ainvoke({"query": "pump"})
        assert "check pressure levels" in result
        mock_retriever.invoke.assert_called_once_with("pump")

@pytest.mark.asyncio
async def test_retrieve_historical_incidents_tool():
    # Test memory retrieval tool
    with patch("app.services.memory_service.retrieve_similar_incidents", new_callable=AsyncMock) as mock_retrieve:
        mock_retrieve.return_value = [
            {
                "incident_type": "water_pressure_drop",
                "severity": "high",
                "root_cause": "Main line burst",
                "resolution_summary": "Replaced section of pipe",
                "actual_outage_hrs": 4.5
            }
        ]
        
        result = await retrieve_historical_incidents.ainvoke({"incident_type": "water_pressure_drop"})
        assert "Main line burst" in result
        assert "Replaced section of pipe" in result

@pytest.mark.asyncio
async def test_get_sensor_history_tool():
    # Test sensor history trend tool
    result = await get_sensor_history.ainvoke({"sensor_type": "water_pressure", "hours": 5})
    assert "Pressure:" in result
    assert "bar" in result

@pytest.mark.asyncio
async def test_run_react_loop_execution():
    # Mock LLM and bind_tools
    mock_llm = MagicMock()
    mock_llm_with_tools = AsyncMock()
    mock_llm.bind_tools.return_value = mock_llm_with_tools
    
    # Setup call sequence for ReAct loop:
    # 1. Model makes a tool call to search knowledge base
    # 2. Model returns final diagnosis JSON
    call1 = MagicMock(spec=AIMessage)
    call1.content = ""
    call1.tool_calls = [
        {
            "name": "search_knowledge_base",
            "args": {"query": "pump motor fault"},
            "id": "call_123"
        }
    ]
    
    call2 = MagicMock(spec=AIMessage)
    call2.content = """
    {
      "probable_cause": "Pump motor capacitor failed",
      "recommended_action": "Replace pump capacitor",
      "confidence": 0.85,
      "retrieved_context": "Found manuals indicating pump capacitor faults cause drops."
    }
    """
    call2.tool_calls = []
    
    mock_llm_with_tools.ainvoke.side_effect = [call1, call2]
    
    incident_event = {"type": "water_pressure_drop", "severity": "medium"}
    state: ASIPState = {
        "incident_id": str(uuid.uuid4()),
        "sensor_data": {"sensor_type": "water_pressure", "value": 0.4},
        "incident_event": incident_event,
        "diagnosis": None,
        "next": "monitoring_agent"
    }
    with patch("app.rag.retriever.get_retriever") as mock_get_retriever:
        mock_retriever = MagicMock()
        mock_doc = MagicMock()
        mock_doc.page_content = "Manual states capacitor failure is common."
        mock_retriever.invoke.return_value = [mock_doc]
        mock_get_retriever.return_value = mock_retriever
        
        result = await _run_react_loop(mock_llm, incident_event, state)
        
        assert result["probable_cause"] == "Pump motor capacitor failed"
        assert result["confidence"] == 0.85
        assert mock_llm_with_tools.ainvoke.call_count == 2
        mock_retriever.invoke.assert_called_once_with("pump motor fault")

@pytest.mark.asyncio
async def test_infrastructure_agent_entrypoint_with_react():
    incident_event = {"type": "water_pressure_drop", "severity": "medium"}
    state: ASIPState = {
        "incident_id": str(uuid.uuid4()),
        "sensor_data": {"sensor_type": "water_pressure", "value": 0.4},
        "incident_event": incident_event,
        "diagnosis": None,
        "next": "monitoring_agent"
    }
    
    # Mock get_llm to return a real-looking model (not a Mock subclass)
    class FakeLLM:
        def __init__(self):
            self.model_name = "gpt-4"
        def bind_tools(self, tools):
            pass
            
    fake_llm = FakeLLM()
    
    # Mock get_llm and _run_react_loop
    with (
        patch("app.agents.infrastructure.get_llm", return_value=fake_llm),
        patch("app.agents.infrastructure._run_react_loop", new_callable=AsyncMock) as mock_react
    ):
        mock_react.return_value = {
            "probable_cause": "Faulty motor",
            "recommended_action": "Fix it",
            "confidence": 0.90,
            "retrieved_context": "None"
        }
        
        updated_state = await infrastructure_agent(state)
        
        assert updated_state["diagnosis"]["probable_cause"] == "Faulty motor"
        mock_react.assert_called_once_with(fake_llm, incident_event, state)


@pytest.mark.asyncio
async def test_get_sensor_history_with_context_only_current_value():
    from app.agents.infrastructure import _SENSOR_CONTEXT, get_sensor_history
    
    # Inject context with current value only
    token = _SENSOR_CONTEXT.set({
        "sensor_data": {"tower_id": str(uuid.uuid4()), "sensor_type": "water_pressure", "value": 0.4},
        "incident_type": "water_pressure_drop"
    })
    
    try:
        result = await get_sensor_history.ainvoke({"sensor_type": "water_pressure", "hours": 5})
        assert "Current sensor reading:" in result
        assert "water_pressure: 0.4" in result
    finally:
        _SENSOR_CONTEXT.reset(token)


@pytest.mark.asyncio
async def test_get_sensor_history_with_real_database_readings():
    from app.agents.infrastructure import _SENSOR_CONTEXT, get_sensor_history
    from datetime import datetime
    
    tower_id = str(uuid.uuid4())
    
    # Inject context with tower_id
    token = _SENSOR_CONTEXT.set({
        "sensor_data": {"tower_id": tower_id, "sensor_type": "water_pressure", "value": 0.4},
        "incident_type": "water_pressure_drop"
    })
    
    # Mock AsyncSessionFactory and DB query
    mock_db = AsyncMock()
    mock_result = MagicMock()
    # Mock records returned by DB: (detected_at, sensor_data)
    mock_result.all.return_value = [
        (datetime(2026, 6, 27, 10, 0), {"value": 0.5, "sensor_type": "water_pressure"}),
        (datetime(2026, 6, 27, 11, 0), {"value": 0.4, "sensor_type": "water_pressure"}),
    ]
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Mock AsyncSessionFactory to yield mock_db
    class AsyncSessionCM:
        async def __aenter__(self):
            return mock_db
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
            
    with patch("app.db.session.AsyncSessionFactory", return_value=AsyncSessionCM()):
        try:
            result = await get_sensor_history.ainvoke({"sensor_type": "water_pressure", "hours": 2})
            assert "Actual hourly readings" in result
            assert "2026-06-27 10:00 - water_pressure: 0.5" in result
            assert "2026-06-27 11:00 - water_pressure: 0.4" in result
        finally:
            _SENSOR_CONTEXT.reset(token)

