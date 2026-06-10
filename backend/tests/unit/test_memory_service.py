import pytest
import uuid
import json
from types import SimpleNamespace

import app.services.memory_service as memory_service


class DummySession:
    def __init__(self):
        self.added = []
        self.flushed = False
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        self.flushed = True

    async def commit(self):
        self.committed = True


@pytest.mark.asyncio
async def test_store_incident_memory(monkeypatch):
    ds = DummySession()

    # Patch the DB session factory used inside the service (lazy import) by
    # inserting a fake module into sys.modules before the service imports it.
    import sys, types
    fake_db_mod = types.ModuleType("app.db.session")
    fake_db_mod.AsyncSessionFactory = lambda: ds
    monkeypatch.setitem(sys.modules, "app.db.session", fake_db_mod)

    state = {
        "incident_id": str(uuid.uuid4()),
        "incident_event": {"type": "water_pressure_drop", "severity": "critical"},
        "impact": {"estimated_residents": 120},
        "contractor_recommendation": {"contractor_name": "AquaFix"},
        "final_report": {"incident_summary": "Summary", "root_cause": "Pump failure", "estimated_resolution_hrs": 4.0},
    }

    mem = await memory_service.store_incident_memory(state)

    assert isinstance(mem, memory_service.IncidentMemory)


@pytest.mark.asyncio
async def test_retrieve_similar_incidents(monkeypatch):
    # Fake retriever
    class FakeDoc:
        def __init__(self, content):
            self.page_content = content

    class FakeRetriever:
        def __init__(self, docs):
            self._docs = docs

        def get_relevant_documents(self, query):
            return self._docs

    sample = {"incident_uuid": str(uuid.uuid4()), "resolution_summary": "Replaced pump", "contractor_used": "AquaFix", "repair_duration_hours": 5}
    docs = [FakeDoc(json.dumps(sample))]

    # Inject a fake app.rag.retriever module into sys.modules to avoid importing langchain_chroma
    import sys, types
    fake_mod = types.ModuleType("app.rag.retriever")
    fake_mod.get_retriever = lambda k=3: FakeRetriever(docs)
    sys.modules["app.rag.retriever"] = fake_mod

    results = await memory_service.retrieve_similar_incidents({"incident_type": "water_pressure_drop"}, k=1)

    assert isinstance(results, list)
    assert results and results[0]["resolution_summary"] == "Replaced pump"
