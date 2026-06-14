"""
SupervisorAgent: aggregates all agent outputs into the FinalDecisionReport.
Acts as the central intelligence layer — routes, resolves conflicts, summarises.
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.agents.state import ASIPState, FinalReport
from app.agents.llm import get_llm
from app.core.llm.chain import invoke_chain
import asyncio
import json
from app.core.logging import get_logger

logger = get_logger("supervisor_agent")

SUPERVISOR_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Supervisor AI of an infrastructure operations centre.
You receive outputs from multiple specialist agents and generate a comprehensive final decision report.

Respond with valid JSON:
{{
  "incident_summary": "string — 2-3 sentence executive summary",
  "root_cause": "string",
  "impact_summary": "string",
  "action_plan": "string — numbered steps",
  "estimated_resolution_hrs": float,
  "priority": "low | medium | high | critical"
}}"""),
    ("human", """
Incident: {incident_type} ({severity})
Description: {description}

Diagnosis:
- Probable Cause: {probable_cause}
- Recommended Action: {recommended_action}
- Confidence: {diagnosis_confidence}

Impact:
- Affected Residents: {residents}
- Severity Score: {severity_score}
- Priority: {priority}

Predictive Analysis (confidence: {prediction_confidence}):
- Predicted Residents Affected: {predicted_residents}
- Predicted Outage Hours: {predicted_outage_hrs}
- Escalation Probability: {escalation_probability}
- SLA Breach Risk: {sla_breach_risk}

Contractor Assignment:
- Contractor: {contractor_name}
- Estimated Cost: INR {cost}
- Estimated Time: {time_hrs} hrs

Notifications Drafted: {notification_count}

Past Incidents: {history}

Generate the final decision report as JSON.
"""),
])


async def supervisor_agent(state: ASIPState) -> ASIPState:
    logger.info("SupervisorAgent: aggregating agent outputs and generating final report", incident_id=state["incident_id"])

    incident_event = state.get("incident_event", {})

    # Prefer aggregated outputs from agent_outputs if present
    agent_outputs = state.get("agent_outputs", {}) or {}

    # Infrastructure diagnosis
    probable_cause = None
    recommended_action = None
    diagnosis_confidence = 0.0
    if "infrastructure_agent" in agent_outputs:
        infra = agent_outputs["infrastructure_agent"].get("output") or {}
        if isinstance(infra, dict):
            probable_cause = infra.get("probable_cause")
            recommended_action = infra.get("recommended_action")
            diagnosis_confidence = infra.get("confidence", 0.0)

    # Impact
    residents = 0
    severity_score = 0.0
    priority = "medium"
    impact_prediction: dict = {}
    if "impact_agent" in agent_outputs:
        imp = agent_outputs["impact_agent"].get("output") or {}
        if isinstance(imp, dict):
            residents = imp.get("estimated_residents", 0)
            severity_score = imp.get("severity_score", 0.0)
            priority = imp.get("priority", "medium")
            # Defensive extraction — impact_prediction may not always be present
            impact_prediction = imp.get("impact_prediction") or {}

    # Also check the raw state impact field for the prediction block
    if not impact_prediction:
        impact_state = state.get("impact") or {}
        impact_prediction = impact_state.get("impact_prediction") or {}

    # Contractor
    contractor = state.get("contractor_recommendation") or {}
    if "contractor_agent" in agent_outputs:
        rec = agent_outputs["contractor_agent"].get("output") or {}
        if isinstance(rec, dict):
            contractor = rec

    # Notifications
    notifications = state.get("notifications") or []
    if "communication_agent" in agent_outputs and not notifications:
        comm_out = agent_outputs["communication_agent"].get("output") or []
        if isinstance(comm_out, list):
            notifications = comm_out

    # Fallback to state fields if agent_outputs were not available
    if not probable_cause or not recommended_action:
        diagnosis_state = state.get("diagnosis") or {}
        if not probable_cause:
            probable_cause = diagnosis_state.get("probable_cause", "Under investigation")
        if not recommended_action:
            recommended_action = diagnosis_state.get("recommended_action", "Pending")

    llm = get_llm(temperature=0.1)
    try:
        import importlib
        memory_service = importlib.import_module("app.services.memory_service")
        hist = await memory_service.retrieve_similar_incidents({"incident_type": incident_event.get("type")}, k=3) or []
        payload = {
            # Include historical incidents for supervisor reasoning
            "history": "\n\n".join([json.dumps(h) for h in hist]),
            "incident_type": incident_event.get("type", "Unknown"),
            "severity": incident_event.get("severity", "Unknown"),
            "description": incident_event.get("description", "N/A"),
            "probable_cause": probable_cause,
            "recommended_action": recommended_action,
            "diagnosis_confidence": diagnosis_confidence,
            "residents": residents,
            "severity_score": severity_score,
            "priority": priority,
            "contractor_name": contractor.get("contractor_name", "TBD"),
            "cost": contractor.get("estimated_cost", 0),
            "time_hrs": contractor.get("estimated_time_hrs", 0),
            "notification_count": len(notifications),
            # Predictive analysis fields for LLM reasoning
            "prediction_confidence": impact_prediction.get("confidence_score", 0.0),
            "predicted_residents":   impact_prediction.get("predicted_residents", residents),
            "predicted_outage_hrs":  impact_prediction.get("predicted_outage_hrs", 0.0),
            "escalation_probability": impact_prediction.get("escalation_probability", 0.0),
            "sla_breach_risk":       impact_prediction.get("sla_breach_risk", 0.0),
        }
        try:
            final_report: FinalReport = await invoke_chain(SUPERVISOR_PROMPT, llm, JsonOutputParser(), payload)
            logger.info("Final report generated", priority=final_report.get("priority"))
        except Exception:
            raise
    except Exception as e:
        logger.error("SupervisorAgent LLM call failed", error=str(e))
        final_report = {
            "incident_summary": f"Incident: {incident_event.get('type')} ({incident_event.get('severity')})",
            "root_cause": probable_cause or "Unknown",
            "impact_summary": f"{residents} residents affected",
            "action_plan": recommended_action or "Manual inspection required",
            "estimated_resolution_hrs": contractor.get("estimated_time_hrs", 4.0),
            "priority": priority,
        }

    # Attach the prediction block to the final report (defensive — never crashes)
    if impact_prediction:
        final_report["prediction"] = {
            "predicted_residents":       impact_prediction.get("predicted_residents", residents),
            "predicted_outage_hrs":      impact_prediction.get("predicted_outage_hrs", 0.0),
            "estimated_cost":            impact_prediction.get("estimated_repair_cost", 0.0),
            "estimated_contractor_cost": impact_prediction.get("estimated_contractor_cost", 0.0),
            "confidence_score":          impact_prediction.get("confidence_score", 0.0),
            "escalation_probability":    impact_prediction.get("escalation_probability", 0.0),
            "sla_breach_risk":           impact_prediction.get("sla_breach_risk", 0.0),
        }

    # Record supervisor decision summary
    decisions = state.get("supervisor_decisions", {}) or {}
    decisions.update({
        "selected_agents": state.get("selected_agents", []),
        "completed_agents": state.get("completed_agents", []),
        "agent_outputs": list(agent_outputs.keys()),
    })

    return {**state, "final_report": final_report, "supervisor_decisions": decisions, "next": "__end__"}


async def supervisor_decider(state: ASIPState) -> ASIPState:
    """Decide which agents should run for the given incident.

    This function inspects the `incident_event` and any explicit `request_type`
    in `sensor_data` and populates `selected_agents`, `completed_agents`, and
    `agent_outputs` placeholders. It sets `next` to the first selected agent
    (or to the aggregator when no agents are required).
    """
    logger.info("SupervisorAgent (decider): selecting agents", incident_id=state["incident_id"])

    incident_event = state.get("incident_event")
    if not incident_event:
        # Nothing to do
        return {**state, "selected_agents": [], "completed_agents": [], "agent_outputs": {}, "supervisor_decisions": {}, "next": "__end__"}

    selected: list = []
    req = state.get("sensor_data", {}).get("request_type")
    if req == "contractor_review":
        selected = ["contractor_agent"]
    elif req == "communication_only":
        selected = ["communication_agent"]
    elif incident_event.get("severity") == "low":
        # Minor incidents -> only notify
        selected = ["communication_agent"]
    else:
        itype = incident_event.get("type", "")
        if "water" in itype or "tank" in itype:
            selected = ["infrastructure_agent", "impact_agent", "contractor_agent", "communication_agent"]
        elif "power" in itype:
            selected = ["infrastructure_agent", "impact_agent", "contractor_agent", "communication_agent"]
        else:
            selected = ["infrastructure_agent", "impact_agent", "contractor_agent", "communication_agent"]

    # Initialize orchestration fields
    base = {"selected_agents": selected, "completed_agents": [], "agent_outputs": {}, "supervisor_decisions": {}}
    if selected:
        base["next"] = selected[0]
    else:
        base["next"] = "supervisor_agent"

    return {**state, **base}
