import pytest
import uuid
import json
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.feedback_service import store_feedback, _compute_decision_accuracy

def test_compute_decision_accuracy():
    """Verify MAPE accuracy calculation logic."""
    # Exact match: 0 difference
    assert _compute_decision_accuracy(4.0, 4.0, 100.0, 100.0) == 1.0

    # Underestimation: predicted=2, actual=4 -> error = (4-2)/4 = 0.5. accuracy = 1 - 0.5 = 0.5
    assert _compute_decision_accuracy(2.0, 4.0, None, None) == 0.5

    # Overestimation: predicted=6, actual=4 -> error = (6-4)/4 = 0.5. accuracy = 1 - 0.5 = 0.5
    assert _compute_decision_accuracy(6.0, 4.0, None, None) == 0.5

    # Both missing
    assert _compute_decision_accuracy(None, None, None, None) is None


@pytest.mark.asyncio
async def test_store_feedback_success(monkeypatch):
    """Test that store_feedback updates database memory record and reindexes Chroma."""
    
    # Mock database session
    class DummyIncidentMemory:
        def __init__(self):
            self.incident_uuid = uuid.uuid4()
            self.incident_type = "water_pressure_drop"
            self.predicted_outage_hrs = 4.0
            self.predicted_cost = 10000.0
            self.actual_outage_hrs = None
            self.actual_cost = None
            self.repair_duration_hours = None
            self.decision_accuracy = None
            self.prediction_accuracy = None
            self.created_at = MagicMock()

    dummy_mem = DummyIncidentMemory()

    class DummySession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def execute(self, stmt):
            mock_res = MagicMock()
            mock_res.scalar_one_or_none.return_value = dummy_mem
            return mock_res
        async def commit(self):
            pass
        async def refresh(self, obj):
            pass

    # Patch session factory
    import sys, types
    fake_db_mod = types.ModuleType("app.db.session")
    fake_db_mod.AsyncSessionFactory = lambda: DummySession()
    monkeypatch.setitem(sys.modules, "app.db.session", fake_db_mod)

    # Mock chroma http client
    mock_chroma_client = MagicMock()
    mock_collection = MagicMock()
    mock_chroma_client.get_collection.return_value = mock_collection

    mock_embeddings = MagicMock()
    mock_embeddings.embed_query.return_value = [0.1, 0.2, 0.3]

    with (
        patch("chromadb.HttpClient", return_value=mock_chroma_client),
        patch("app.agents.llm.get_embedding_model", return_value=mock_embeddings)
    ):
        result = await store_feedback(
            incident_uuid=str(dummy_mem.incident_uuid),
            actual_outage_hrs=6.0,
            actual_cost=12000.0,
        )

        assert result["updated"] is True
        assert result["actual_outage_hrs"] == 6.0
        assert result["actual_cost"] == 12000.0
        assert result["decision_accuracy"] is not None

        # Verify DB model was updated
        assert dummy_mem.actual_outage_hrs == 6.0
        assert dummy_mem.actual_cost == 12000.0
        assert dummy_mem.repair_duration_hours == 6.0  # database ground truth field updated

        # Verify Chroma was upserted with actuals
        mock_collection.upsert.assert_called_once()
        called_args = mock_collection.upsert.call_args[1]
        assert called_args["ids"] == [str(dummy_mem.incident_uuid)]
        
        doc_content = json.loads(called_args["documents"][0])
        assert doc_content["repair_duration_hours"] == 6.0
        assert doc_content["_ground_truth"] is True


@pytest.mark.asyncio
async def test_trigger_model_retrain_bypassed_in_testing():
    from app.services.feedback_service import _trigger_model_retrain_if_needed
    import asyncio
    
    # We patch subprocess execution to assert it's never called
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        await _trigger_model_retrain_if_needed()
        mock_exec.assert_not_called()


@pytest.mark.asyncio
async def test_trigger_model_retrain_triggered_when_should_retrain():
    from app.services.feedback_service import _trigger_model_retrain_if_needed
    from app.config import settings
    import os
    import sys
    import asyncio
    
    # Mock data to trigger retraining
    # Window MAE threshold is 12 hrs. We return error = 20 hrs.
    class MockMemoryRecord:
        def __init__(self):
            self.predicted_outage_hrs = 25.0
            self.actual_outage_hrs = 5.0
            self.predicted_cost = 1000.0
            self.actual_cost = 1000.0
            self.created_at = MagicMock()
            
    mock_memories = [MockMemoryRecord() for _ in range(5)]
    
    # Mock session
    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = mock_memories
    mock_db.execute = AsyncMock(return_value=mock_res)
    
    class AsyncSessionCM:
        async def __aenter__(self):
            return mock_db
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
            
    mock_process = AsyncMock()
    mock_process.pid = 99999
    
    # Save and temporarily remove pytest from sys.modules to bypass testing block
    import sys
    original_pytest = sys.modules.pop("pytest", None)
    
    try:
        with (
            # Temporarily force env to production
            patch.object(settings, "environment", "production"),
            patch("app.db.session.AsyncSessionFactory", return_value=AsyncSessionCM()),
            patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_process) as mock_exec
        ):
            await _trigger_model_retrain_if_needed()
            
            # Verify retraining subprocess was launched
            mock_exec.assert_called_once()
            called_args = mock_exec.call_args[0]
            assert called_args[0] == sys.executable
            assert "training_pipeline.py" in called_args[1]
    finally:
        # Restore original pytest module to registry
        if original_pytest is not None:
            sys.modules["pytest"] = original_pytest


