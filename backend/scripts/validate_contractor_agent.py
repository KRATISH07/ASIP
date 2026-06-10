"""Run contractor_agent with patched memory retrieval and LLM to validate memory integration.
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import types
# Provide lightweight stub for missing langchain_openai to avoid runtime import errors in test environment
stub_mod = types.ModuleType("langchain_openai")
def _ChatOpenAI(*a, **k):
    class Dummy:
        pass
    return Dummy()
stub_mod.ChatOpenAI = _ChatOpenAI
sys.modules["langchain_openai"] = stub_mod

from app.agents.contractor import contractor_agent
from app.db.session import AsyncSessionFactory

# Patch memory_service.retrieve_similar_incidents to return sample memories and log call
import importlib
memory_service = importlib.import_module('app.services.memory_service')

async def fake_retrieve_similar_incidents(query, k=5):
    print('DEBUG: memory retrieve called with', query)
    return [{"resolution_summary": "Replaced pump", "contractor_used": "AquaFix Pro"}]

memory_service.retrieve_similar_incidents = fake_retrieve_similar_incidents

# Patch LLM invoke_chain to force fallback (raise error)
from app.core import llm as core_llm
from app.core.llm import chain as llm_chain

async def raise_invoke(*args, **kwargs):
    raise RuntimeError('Forced LLM failure for validation')

llm_chain.invoke_chain = raise_invoke

async def main():
    state = {
        "incident_id": "00000000-0000-0000-0000-000000000000",
        "sensor_data": {"tower_id": "t1"},
        "incident_event": {"type": "water_leak", "severity": "critical"},
        "impact": {"estimated_residents": 50, "priority": "high"},
        "contractor_recommendation": None,
        "notifications": None,
        "final_report": None,
        "error": None,
        "next": "contractor_agent",
    }

    res = await contractor_agent(state)
    import json
    print('Contractor agent result:')
    print(json.dumps(res.get('contractor_recommendation'), indent=2))

if __name__ == '__main__':
    asyncio.run(main())
