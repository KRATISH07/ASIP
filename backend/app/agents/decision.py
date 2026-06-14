"""
DecisionAgent: reads accumulated pipeline state (incident, impact prediction,
contractor recommendation) and calls the autonomous decision engine to
produce an AutonomousDecision that the supervisor will include in the
final report.

All state access uses .get() — no direct indexing.
"""
from app.agents.state import ASIPState
from app.core.logging import get_logger
from app.services.decision_service import make_decision

logger = get_logger("decision_agent")


async def decision_agent(state: ASIPState) -> ASIPState:
    logger.info("DecisionAgent: computing autonomous decision", incident_id=state.get("incident_id"))

    # Defensive extraction — none of these are guaranteed to be present
    incident_event    = state.get("incident_event") or {}
    impact            = state.get("impact") or {}
    contractor_rec    = state.get("contractor_recommendation") or {}

    # Pull full impact_prediction block if the impact agent attached it
    impact_prediction = impact.get("impact_prediction") or {}

    # Build contractor candidates list from the single recommendation we have.
    # In future this can be extended to accept the full ranked list from the
    # contractor agent via agent_outputs.
    contractor_candidates: list = []
    if contractor_rec and isinstance(contractor_rec, dict):
        contractor_candidates = [contractor_rec]

    # Also check agent_outputs for the ranked candidates list
    agent_outputs = state.get("agent_outputs") or {}
    contractor_output = (agent_outputs.get("contractor_agent") or {}).get("output") or {}
    if isinstance(contractor_output, dict) and contractor_output:
        # contractor_output may be the full recommendation; use it as sole candidate
        if contractor_output not in contractor_candidates:
            contractor_candidates.insert(0, contractor_output)

    try:
        autonomous_decision = await make_decision(
            incident_event=incident_event,
            impact_prediction=impact_prediction,
            contractor_candidates=contractor_candidates,
        )
        logger.info(
            "Autonomous decision ready",
            risk_score=autonomous_decision.get("estimated_risk_score"),
            escalation=autonomous_decision.get("requires_immediate_escalation"),
        )
    except Exception as e:
        logger.error("DecisionAgent: make_decision failed, using safe fallback", error=str(e))
        autonomous_decision = {
            "requires_immediate_escalation": False,
            "should_notify_residents":       False,
            "notification_priority":         "low",
            "should_activate_backup_system": False,
            "auto_dispatch_contractor":      False,
            "recommended_contractor":        None,
            "estimated_risk_score":          0.0,
            "decision_reasoning":            f"Decision engine error: {str(e)}",
        }

    return {**state, "autonomous_decision": autonomous_decision, "next": "supervisor_agent"}
