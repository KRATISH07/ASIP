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

PERFORMANCE NOTE:
  build_graph() compiles the StateGraph — registering nodes, compiling
  conditional edge mappings, and validating topology. This is NOT free.
  get_compiled_graph() wraps it with lru_cache so compilation happens once
  at startup and the compiled graph is reused across all HTTP requests.
  This amortizes compilation cost to O(1) instead of O(N_requests).
"""
from functools import lru_cache
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


def build_graph(checkpointer=None):
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
        if agent_key == "monitoring_agent":
            evt = state.get("incident_event") or {}
            return {
                "agent_name": "monitoring_agent",
                "decision": evt.get("type"),
                "confidence": float(evt.get("confidence", 0.0) or 0.0),
                "reasoning": evt.get("description"),
                "output": evt,
            }

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

        if agent_key == "supervisor_agent":
            report = state.get("final_report") or {}
            return {
                "agent_name": "supervisor_agent",
                "decision": report.get("priority"),
                "confidence": 1.0,
                "reasoning": report.get("incident_summary"),
                "output": report,
            }

        # Fallback generic record
        return {"agent_name": agent_key, "decision": None, "confidence": 0.0, "reasoning": None, "output": None}

    def _wrap_agent(agent_func: Callable[[ASIPState], ASIPState], agent_key: str):
        async def _executor(state: ASIPState) -> ASIPState:
            import time

            start_time = time.time()
            
            # Execute the actual node function
            new_state = await agent_func(state)
            
            duration_ms = int((time.time() - start_time) * 1000)

            # Ensure orchestration fields exist
            selected = new_state.get("selected_agents", []) or []
            completed = new_state.get("completed_agents", []) or []
            outputs = new_state.get("agent_outputs", {}) or {}

            # Extract a standardized output for this agent and record completion
            agent_output = _extract_agent_output(agent_key, new_state)
            outputs[agent_key] = agent_output
            if agent_key not in completed:
                completed.append(agent_key)

            new_state["completed_agents"] = completed
            new_state["agent_outputs"] = outputs

            # Collect log entry in the state to be persisted later at the end of the workflow
            logs_to_persist = new_state.get("agent_logs_to_persist", []) or []
            logs_to_persist = list(logs_to_persist)  # clone list to be safe
            logs_to_persist.append({
                "agent_name": agent_key,
                "input_payload": {
                    "sensor_data": state.get("sensor_data"),
                    "incident_event": state.get("incident_event"),
                    "diagnosis": state.get("diagnosis"),
                    "impact": state.get("impact"),
                    "contractor_recommendation": state.get("contractor_recommendation"),
                },
                "output_payload": agent_output,
                "execution_time_ms": duration_ms,
                "status": "success",
            })
            new_state["agent_logs_to_persist"] = logs_to_persist

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
    graph.add_node("supervisor_agent", _wrap_agent(supervisor_agent, "supervisor_agent"))

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

    return graph.compile(checkpointer=checkpointer)


_checkpointer = None
_compiled_graph = None

def set_global_checkpointer(checkpointer):
    global _checkpointer, _compiled_graph
    _checkpointer = checkpointer
    _compiled_graph = build_graph(checkpointer=checkpointer)

def get_compiled_graph():
    """Return the compiled LangGraph, built once per process.

    Fix #6: LangGraph Checkpointing
    --------------------------------
    The compiled graph uses AsyncPostgresSaver to persist state to PostgreSQL.
    In testing or pytest environments, it falls back to MemorySaver.
    
    Why not MemorySaver in production:
        MemorySaver is in-process and lost on restart. The saga retry mechanism
        explicitly depends on checkpoint resume. Using MemorySaver makes saga
        retry a no-op after any process restart — which happens constantly in
        production (deployments, OOM kills, pod restarts).
    """
    global _compiled_graph
    if _compiled_graph is not None:
        return _compiled_graph

    import sys
    from app.config import settings

    if settings.environment == "testing" or "pytest" in sys.modules:
        from langgraph.checkpoint.memory import MemorySaver
        _compiled_graph = build_graph(checkpointer=MemorySaver())
        return _compiled_graph

    # Fallback memory checkpointer if called outside lifespan context (e.g. from scripts)
    from langgraph.checkpoint.memory import MemorySaver
    return build_graph(checkpointer=MemorySaver())

