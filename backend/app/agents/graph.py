"""
LangGraph workflow builder for ASIP.

Graph topology (supervisor-driven):
  monitoring_agent
       │
  supervisor_decider  (select agents)
       │
  selected agents (dynamic)
       │
  supervisor_agent (aggregate)
       │
    __end__
"""
from langgraph.graph import StateGraph, END
from app.agents.state import ASIPState
from app.agents.monitoring import monitoring_agent
from app.agents.infrastructure import infrastructure_agent
from app.agents.impact_analysis import impact_analysis_agent
from app.agents.contractor import contractor_agent
from app.agents.communication import communication_agent
from app.agents.decision import decision_agent
from app.agents.supervisor import supervisor_agent, supervisor_decider
from typing import Callable, Dict, Any


def build_graph() -> StateGraph:
    graph = StateGraph(ASIPState)

    # We'll register wrapper executors for each agent so the supervisor
    # can track outputs and mark completed agents.
    AGENTS = [
        "infrastructure_agent",
        "impact_agent",
        "contractor_agent",
        "communication_agent",
        "decision_agent",
    ]

    def _extract_agent_output(agent_key: str, state: ASIPState) -> Dict[str, Any]:
        """Create a standardized agent output record from the state's fields.

        This keeps existing agent implementations unchanged while providing a
        consistent shape for the supervisor to aggregate.
        """
        if agent_key == "infrastructure_agent":
            diag = state.get("diagnosis") or {}
            return {
                "agent_name": "infrastructure_agent",
                "decision": diag.get("probable_cause"),
                "confidence": float(diag.get("confidence", 0.0) or 0.0),
                "reasoning": diag.get("recommended_action"),
                "output": diag,
            }

        if agent_key == "impact_agent":
            imp = state.get("impact") or {}
            return {
                "agent_name": "impact_agent",
                "decision": imp.get("priority"),
                "confidence": float(imp.get("severity_score", 0.0) or 0.0),
                "reasoning": f"{imp.get('estimated_residents', 0)} residents affected",
                "output": imp,
            }

        if agent_key == "contractor_agent":
            rec = state.get("contractor_recommendation") or {}
            return {
                "agent_name": "contractor_agent",
                "decision": rec.get("contractor_name"),
                "confidence": 0.8,
                "reasoning": rec.get("selection_reasoning"),
                "output": rec,
            }

        if agent_key == "communication_agent":
            notifs = state.get("notifications") or []
            return {
                "agent_name": "communication_agent",
                "decision": "notifications_generated" if notifs else "none",
                "confidence": 0.9 if notifs else 0.0,
                "reasoning": f"{len(notifs)} notification drafts",
                "output": notifs,
            }

        if agent_key == "decision_agent":
            dec = state.get("autonomous_decision") or {}
            return {
                "agent_name": "decision_agent",
                "decision": "escalate" if dec.get("requires_immediate_escalation") else "monitor",
                "confidence": float(dec.get("estimated_risk_score", 0.0)),
                "reasoning": dec.get("decision_reasoning"),
                "output": dec,
            }

        # Fallback generic record
        return {"agent_name": agent_key, "decision": None, "confidence": 0.0, "reasoning": None, "output": None}

    def _wrap_agent(agent_func: Callable[[ASIPState], ASIPState], agent_key: str):
        async def _executor(state: ASIPState) -> ASIPState:
            new_state = await agent_func(state)

            # Ensure orchestration fields exist
            selected = new_state.get("selected_agents", []) or []
            completed = new_state.get("completed_agents", []) or []
            outputs = new_state.get("agent_outputs", {}) or {}

            # Extract a standardized output for this agent and record completion
            outputs[agent_key] = _extract_agent_output(agent_key, new_state)
            if agent_key not in completed:
                completed.append(agent_key)

            new_state["completed_agents"] = completed
            new_state["agent_outputs"] = outputs

            # Do not set `next` here; routing uses selected/completed lists
            return new_state

        return _executor

    # Register nodes (wrapping agents so outputs are tracked)
    graph.add_node("monitoring_agent", _wrap_agent(monitoring_agent, "monitoring_agent"))
    graph.add_node("supervisor_decider", supervisor_decider)
    graph.add_node("infrastructure_agent", _wrap_agent(infrastructure_agent, "infrastructure_agent"))
    graph.add_node("impact_agent", _wrap_agent(impact_analysis_agent, "impact_agent"))
    graph.add_node("contractor_agent", _wrap_agent(contractor_agent, "contractor_agent"))
    graph.add_node("communication_agent", _wrap_agent(communication_agent, "communication_agent"))
    graph.add_node("decision_agent", _wrap_agent(decision_agent, "decision_agent"))
    graph.add_node("supervisor_agent", supervisor_agent)

    # Entry point
    graph.set_entry_point("monitoring_agent")

    # After monitoring, route to supervisor if incident detected, else end
    def _monitoring_router(state: ASIPState) -> str:
        return "supervisor_decider" if state.get("incident_event") else "__end__"

    graph.add_conditional_edges(
        "monitoring_agent",
        _monitoring_router,
        {"supervisor_decider": "supervisor_decider", "__end__": END},
    )

    # Router that picks the next selected agent (or supervisor aggregator when done)
    def _next_selected_agent(state: ASIPState) -> str:
        selected = state.get("selected_agents") or []
        completed = state.get("completed_agents") or []
        remaining = [a for a in selected if a not in completed]
        if remaining:
            return remaining[0]
        return "supervisor_agent"

    # Build mapping for conditional edges (map possible returns to nodes)
    mapping = {name: name for name in AGENTS}
    mapping.update({"supervisor_agent": "supervisor_agent", "__end__": END})

    # After the decider, jump to the first selected agent (or aggregator)
    graph.add_conditional_edges("supervisor_decider", _next_selected_agent, mapping)

    # After each agent node decide next selected agent
    for a in AGENTS:
        graph.add_conditional_edges(a, _next_selected_agent, mapping)

    # Final aggregator -> END
    graph.add_edge("supervisor_agent", END)

    return graph.compile()
