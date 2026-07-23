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

    llm = get_llm(task_type="extraction", temperature=0.1)
    from app.core.llm.fallback import invoke_with_fallback
    from app.agents.schemas import ContractorSelection
    recommendation: dict = await invoke_with_fallback(
        prompt=CONTRACTOR_PROMPT,
        input_data=payload,
        parser=JsonOutputParser(),
        agent_type="contractor",
        primary_llm=llm,
        response_model=ContractorSelection,
    )
    # Ensure the mathematically best contractor candidate is selected, resolving any LLM hallucinations or selection variance
    top = candidates[0] if candidates else None
    
    if top:
        # Resolve metrics and cost predictions
        first_hist = (top.get("historical_evidence") or [{}])[0] if isinstance(top, dict) else {}
        est_cost = float(recommendation.get("estimated_cost") or first_hist.get("repair_cost") or 0)
        est_time = float(recommendation.get("estimated_time_hrs") or top.get("avg_response_time_hrs") or 0)
        
        # Build the final contractor recommendation dictionary using database-verified fields
        recommendation = {
            "contractor_id": top.get("contractor_id"),
            "contractor_name": top.get("name"),
            "estimated_cost": est_cost,
            "estimated_time_hrs": est_time,
            "selection_reasoning": recommendation.get("selection_reasoning") or f"Selected {top.get('name')} based on situational priority and historical score breakdown.",
        }
    else:
        recommendation = {
            "contractor_id": None,
            "contractor_name": "No contractor available",
            "estimated_cost": 0.0,
            "estimated_time_hrs": 0.0,
            "selection_reasoning": "No available contractors found.",
        }

    return {**state, "contractor_recommendation": recommendation, "next": "communication_agent"}
