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

# Import the LLM judge here — imported lazily inside the agent to avoid
# circular import issues at module load time.
def _get_judge():
    from app.evaluation.judge import evaluate_report
    return evaluate_report

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

Autonomous Decision:
- Immediate Escalation Required: {escalation_required}
- Resident Notification Required: {notify_residents}
- Backup System Activation: {backup_activation}
- Contractor Auto-Dispatch: {auto_dispatch}
- Risk Score: {risk_score}

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
    if "impact_agent" in agent_outputs:
        imp = agent_outputs["impact_agent"].get("output") or {}
        if isinstance(imp, dict):
            residents = imp.get("estimated_residents", 0)
            severity_score = imp.get("severity_score", 0.0)
            priority = imp.get("priority", "medium")

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

    # V4: Autonomous Decision — defensive extraction (two fallback paths)
    autonomous_decision: dict = state.get("autonomous_decision") or {}
    if not autonomous_decision and "decision_agent" in agent_outputs:
        autonomous_decision = (agent_outputs["decision_agent"].get("output") or {})
        if not isinstance(autonomous_decision, dict):
            autonomous_decision = {}

    # Fallback to state fields if agent_outputs were not available
    if not probable_cause or not recommended_action:
        diagnosis_state = state.get("diagnosis") or {}
        if not probable_cause:
            probable_cause = diagnosis_state.get("probable_cause", "Under investigation")
        if not recommended_action:
            recommended_action = diagnosis_state.get("recommended_action", "Pending")

    llm = get_llm(task_type="supervisor", temperature=0.1)
    try:
        import importlib
        memory_service = importlib.import_module("app.services.memory_service")
        hist = await memory_service.retrieve_similar_incidents({"incident_type": incident_event.get("type")}, k=3) or []

        # Impact prediction fields (from V3)
        impact_prediction = (state.get("impact") or {}).get("impact_prediction") or {}
        if not impact_prediction and "impact_agent" in agent_outputs:
            impact_prediction = ((agent_outputs["impact_agent"].get("output") or {}).get("impact_prediction") or {})

        payload = {
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
            # V3 predictive fields
            "prediction_confidence":  impact_prediction.get("confidence_score", 0.0),
            "predicted_residents":    impact_prediction.get("predicted_residents", residents),
            "predicted_outage_hrs":   impact_prediction.get("predicted_outage_hrs", 0.0),
            "escalation_probability": impact_prediction.get("escalation_probability", 0.0),
            "sla_breach_risk":        impact_prediction.get("sla_breach_risk", 0.0),
            # V4 autonomous decision fields
            "escalation_required": autonomous_decision.get("requires_immediate_escalation", False),
            "notify_residents":    autonomous_decision.get("should_notify_residents", False),
            "backup_activation":   autonomous_decision.get("should_activate_backup_system", False),
            "auto_dispatch":       autonomous_decision.get("auto_dispatch_contractor", False),
            "risk_score":          autonomous_decision.get("estimated_risk_score", 0.0),
        }
        try:
            from app.core.llm.fallback import invoke_with_fallback
            from app.agents.schemas import SupervisorReportSchema
            final_report: FinalReport = await invoke_with_fallback(
                prompt=SUPERVISOR_PROMPT,
                input_data=payload,
                parser=JsonOutputParser(),
                agent_type="supervisor",
                primary_llm=llm,
                response_model=SupervisorReportSchema,
            )
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

    # Attach the prediction block (V3) — defensive, never crashes
    impact_prediction_for_report = (state.get("impact") or {}).get("impact_prediction") or {}
    if not impact_prediction_for_report and "impact_agent" in agent_outputs:
        impact_prediction_for_report = ((agent_outputs["impact_agent"].get("output") or {}).get("impact_prediction") or {})
    if impact_prediction_for_report:
        final_report["prediction"] = {
            "predicted_residents":       impact_prediction_for_report.get("predicted_residents", residents),
            "predicted_outage_hrs":      impact_prediction_for_report.get("predicted_outage_hrs", 0.0),
            "estimated_cost":            impact_prediction_for_report.get("estimated_repair_cost", 0.0),
            "estimated_contractor_cost": impact_prediction_for_report.get("estimated_contractor_cost", 0.0),
            "confidence_score":          impact_prediction_for_report.get("confidence_score", 0.0),
            "escalation_probability":    impact_prediction_for_report.get("escalation_probability", 0.0),
            "sla_breach_risk":           impact_prediction_for_report.get("sla_breach_risk", 0.0),
        }

    # Attach the autonomous decision block (V4) — defensive, never crashes
    if autonomous_decision:
        final_report["decision"] = {
            "auto_dispatch":          autonomous_decision.get("auto_dispatch_contractor", False),
            "backup_activation":      autonomous_decision.get("should_activate_backup_system", False),
            "risk_score":             autonomous_decision.get("estimated_risk_score", 0.0),
            "requires_escalation":    autonomous_decision.get("requires_immediate_escalation", False),
            "notify_residents":       autonomous_decision.get("should_notify_residents", False),
            "notification_priority":  autonomous_decision.get("notification_priority", "low"),
            "recommended_contractor": autonomous_decision.get("recommended_contractor"),
        }

    # Record supervisor decision summary
    decisions = state.get("supervisor_decisions", {}) or {}
    decisions.update({
        "selected_agents": state.get("selected_agents", []),
        "completed_agents": state.get("completed_agents", []),
        "agent_outputs": list(agent_outputs.keys()),
    })

    # ---------------------------------------------------------
    # P10: LLM-as-judge — fire-and-forget background evaluation
    # Does NOT block the main workflow. Any failure is logged only.
    # ---------------------------------------------------------
    _incident_id = str(state.get("incident_id", ""))
    _incident_event = state.get("incident_event", {})
    asyncio.create_task(
        _get_judge()(
            incident_data=_incident_event,
            report=final_report,
            incident_id=_incident_id,
            persist=True,
        )
    )
    logger.info(
        "LLM-judge evaluation task scheduled",
        incident_id=_incident_id,
    )

    return {**state, "final_report": final_report, "supervisor_decisions": decisions, "next": "__end__"}


async def supervisor_decider(state: ASIPState) -> ASIPState:
    """Decide which agents should run for the given incident.

    Fix #12: Routing is now driven by AGENT_ROUTING_TABLE in routing_config.py.
    Adding a new incident type requires only a new entry in routing_config.py —
    no changes to this file. This follows the Open/Closed Principle.

    Previously: three hardcoded branches all selecting identical agent lists.
    Now: config-driven resolution with per-type, per-severity specificity.
    """
    logger.info(
        "SupervisorAgent (decider): selecting agents",
        incident_id=state["incident_id"],
        trace_id=state.get("trace_id"),
    )

    incident_event = state.get("incident_event")
    if not incident_event:
        return {**state, "selected_agents": [], "completed_agents": [], "agent_outputs": {}, "supervisor_decisions": {}, "next": "__end__"}

    incident_type = incident_event.get("type", "unknown")
    severity      = incident_event.get("severity", "medium")
    request_type  = state.get("sensor_data", {}).get("request_type")

    # Config-driven routing: resolve from AGENT_ROUTING_TABLE
    from app.routing_config import resolve_agents
    selected, routing_reason = resolve_agents(
        incident_type=incident_type,
        severity=severity,
        request_type=request_type,
    )

    logger.info(
        "Agent routing resolved",
        incident_type=incident_type,
        severity=severity,
        agents_selected=selected,
        routing_reason=routing_reason,
        trace_id=state.get("trace_id"),
    )

    base = {
        "selected_agents":    selected,
        "completed_agents":   [],
        "agent_outputs":      {},
        "supervisor_decisions": {},
    }
    base["next"] = selected[0] if selected else "supervisor_agent"

    return {**state, **base}
