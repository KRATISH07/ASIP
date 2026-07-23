"""Agent Routing Configuration (Fix #12 — Open/Closed Principle)

THE PROBLEM THIS SOLVES:
    supervisor_decider contains hardcoded routing:
        if "water" in itype: selected = [agents...]
        elif "power" in itype: selected = [agents...]
        else: selected = [agents...]

    All three branches select IDENTICAL agent lists. The routing is dead code.
    Adding a new incident type (gas_leak, elevator_failure, fire_alarm) requires
    modifying supervisor.py — a core orchestration file. This violates the
    Open/Closed Principle: the system is closed to extension without modification.

    Additionally, routing ignores severity — a "low" severity water_pressure_drop
    runs the same 5-agent pipeline as a critical one. This is expensive.

THE FIX:
    Routing table as pure Python configuration.
    Adding a new incident type = adding one dict entry here.
    No supervisor.py changes required.
    Routing is now independently testable.

MATCHING RULES:
    Rules are evaluated in order — first match wins.
    Pattern matching: "*" matches any value, otherwise exact string match.
    The most specific rules should come first.

DESIGN DECISION — Why not DB-driven config?
    DB-driven routing would allow runtime changes without redeployment.
    Rejected because: routing changes are architectural — they should go
    through code review, not be changeable at runtime by an API call.
    A bad routing config at runtime could silently disable entire agent pipelines.
    Configuration-as-code with code review is safer for orchestration decisions.

REJECTED ALTERNATIVES:
    - Regular expression matching on incident_type: overkill for a finite enum.
    - ML-based routing (let LLM decide which agents to run): interesting but
      introduces an LLM call before the pipeline starts, adding latency and
      a new failure point for the routing layer itself.
"""
from typing import Optional

# Routing table: (incident_type_pattern, severity_pattern) → [agent_names]
# Rules evaluated top-to-bottom. First match wins.
# "*" matches any string value.
AGENT_ROUTING_TABLE: list[dict] = [
    # Low severity: skip heavy infrastructure analysis — just notify + decide
    {
        "incident_type": "*",
        "severity":      "low",
        "agents":        ["communication_agent", "decision_agent"],
        "reason":        "Low severity incidents do not require infrastructure diagnosis or contractor dispatch",
    },

    # Contractor review requests: explicit routing override from API
    {
        "incident_type": "*",
        "request_type":  "contractor_review",
        "agents":        ["contractor_agent", "decision_agent"],
        "reason":        "Explicit contractor review request — skip monitoring and diagnosis",
    },

    # Communication-only requests
    {
        "incident_type": "*",
        "request_type":  "communication_only",
        "agents":        ["communication_agent"],
        "reason":        "Explicit communication-only request",
    },

    # Water incidents: full pipeline
    {
        "incident_type": "water_pressure_drop",
        "severity":      "*",
        "agents":        ["infrastructure_agent", "impact_agent", "contractor_agent",
                          "communication_agent", "decision_agent"],
        "reason":        "Water pressure drops require infrastructure diagnosis and contractor dispatch",
    },
    {
        "incident_type": "water_shortage",
        "severity":      "*",
        "agents":        ["infrastructure_agent", "impact_agent", "contractor_agent",
                          "communication_agent", "decision_agent"],
        "reason":        "Water shortage requires full incident analysis",
    },
    {
        "incident_type": "tank_overflow",
        "severity":      "*",
        "agents":        ["infrastructure_agent", "impact_agent", "contractor_agent",
                          "communication_agent", "decision_agent"],
        "reason":        "Tank overflow may damage property — full pipeline required",
    },

    # Power incidents: full pipeline
    {
        "incident_type": "power_outage",
        "severity":      "*",
        "agents":        ["infrastructure_agent", "impact_agent", "contractor_agent",
                          "communication_agent", "decision_agent"],
        "reason":        "Power outages affect all residents — full pipeline required",
    },
    {
        "incident_type": "power_overload",
        "severity":      "*",
        "agents":        ["infrastructure_agent", "impact_agent", "contractor_agent",
                          "communication_agent", "decision_agent"],
        "reason":        "Power overloads risk equipment damage — full pipeline required",
    },

    # Default catch-all: full pipeline for unknown incident types
    {
        "incident_type": "*",
        "severity":      "*",
        "agents":        ["infrastructure_agent", "impact_agent", "contractor_agent",
                          "communication_agent", "decision_agent"],
        "reason":        "Default: unknown incident type — full pipeline for safety",
    },
]


def resolve_agents(
    incident_type: str,
    severity: str,
    request_type: Optional[str] = None,
) -> tuple[list[str], str]:
    """Resolve which agents to run for the given incident parameters.

    Returns (agent_list, reason_string) for the first matching rule.

    Parameters
    ----------
    incident_type : str
        The IncidentType enum value (e.g., "water_pressure_drop")
    severity : str
        The IncidentSeverity enum value (e.g., "critical")
    request_type : str | None
        Optional override from sensor_data["request_type"]

    Returns
    -------
    (agents, reason): list of agent names and the routing reason string
    """
    for rule in AGENT_ROUTING_TABLE:
        # Check request_type override first (most specific)
        if "request_type" in rule:
            if request_type == rule["request_type"]:
                return rule["agents"], rule["reason"]
            continue  # request_type rules don't fall through to pattern rules

        type_match = (rule["incident_type"] == "*" or rule["incident_type"] == incident_type)
        sev_match  = (rule["severity"] == "*"      or rule["severity"] == severity)

        if type_match and sev_match:
            return rule["agents"], rule["reason"]

    # Should never reach here due to catch-all rule, but be safe
    return ["infrastructure_agent", "impact_agent", "contractor_agent",
            "communication_agent", "decision_agent"], "fallback: no rule matched"
