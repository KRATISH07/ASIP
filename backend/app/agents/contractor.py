"""
ContractorAgent: ranks and selects the best contractor for the incident
based on specialization, rating, response time, and historical performance.
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.agents.state import ASIPState, ContractorRecommendation
from app.agents.llm import get_llm
from app.core.llm.chain import invoke_chain
from app.core.logging import get_logger
from app.services import contractor_service
from app.db.session import AsyncSessionFactory
import importlib

logger = get_logger("contractor_agent")


CONTRACTOR_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a contractor selection AI for a residential society.
You will receive a list of contractor candidates with numeric score breakdowns and historical evidence.
Rank and select the best contractor for the incident. Explain your reasoning briefly.

Return valid JSON:
{
  "contractor_id": "string",
  "contractor_name": "string",
  "estimated_cost": float,
  "estimated_time_hrs": float,
  "selection_reasoning": "string"
}
"""),
    ("human", """
Incident Type: {incident_type}
Severity: {severity}
Impact: {impact_summary}

Contractor Candidates (with score breakdown):
{contractors}

Historical Incidents (retrieved from memory):
{historical_incidents}

Select the best contractor and provide a short reason.
"""),
])


async def contractor_agent(state: ASIPState) -> ASIPState:
    logger.info("ContractorAgent: selecting contractor", incident_id=state["incident_id"])

    # Defensive defaults: `state` may omit keys or contain None (contractor-only flows)
    incident_event = state.get("incident_event") or {}
    impact = state.get("impact") or {}
    incident_type = incident_event.get("type", "")

    # Retrieve similar incidents from memory (if available)
    try:
        memory_service = importlib.import_module("app.services.memory_service")
        # ensure we pass a dict to the memory service
        mem_query = {"incident_type": incident_type}
        if isinstance(impact, dict):
            mem_query.update(impact)
        history = await memory_service.retrieve_similar_incidents(mem_query, k=5)
        history = history or []
    except Exception:
        history = []

    # Compute ranked contractors using DB-driven scoring
    try:
        async with AsyncSessionFactory() as db:
            candidates = await contractor_service.rank_contractors(db, incident_type=incident_type, k=5, impact=impact)
            candidates = candidates or []
    except Exception as e:
        logger.error("ContractorAgent: scoring failed", error=str(e))
        candidates = []

    # Prepare LLM payload with candidates and history
    payload = {
        "incident_type": incident_type,
        "severity": incident_event.get("severity", "unknown"),
        "impact_summary": f"{impact.get('estimated_residents', 0)} residents affected, priority: {impact.get('priority', 'unknown')}",
        "contractors": str(candidates),
        "historical_incidents": str(history),
    }

    llm = get_llm(temperature=0.1)
    try:
        recommendation: ContractorRecommendation = await invoke_chain(CONTRACTOR_PROMPT, llm, JsonOutputParser(), payload)
        logger.info("Contractor selected via LLM", name=recommendation.get("contractor_name"))
    except Exception:
        # Fallback: pick top ranked candidate
        top = candidates[0] if candidates else None
        if top:
            # historical_evidence may be empty; guard against IndexError
            first_hist = (top.get("historical_evidence") or [{}])[0] if isinstance(top, dict) else {}
            est_cost = float(first_hist.get("repair_cost", 0) or 0)
            est_time = float((top.get("breakdown") or {}).get("repair_time_score", 0) or 0)
            recommendation = {
                "contractor_id": top.get("contractor_id"),
                "contractor_name": top.get("name"),
                "estimated_cost": est_cost,
                "estimated_time_hrs": est_time,
                "selection_reasoning": "Selected based on data-driven score breakdown.",
            }
        else:
            recommendation = {
                "contractor_id": None,
                "contractor_name": "No contractor available",
                "estimated_cost": 0.0,
                "estimated_time_hrs": 0.0,
                "selection_reasoning": "No available contractors",
            }

    return {**state, "contractor_recommendation": recommendation, "next": "communication_agent"}
