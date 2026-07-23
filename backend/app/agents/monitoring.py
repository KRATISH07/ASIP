"""
MonitoringAgent: analyses raw sensor data, detects anomalies,
classifies incident type, estimates severity and confidence.
"""
import json
from datetime import datetime, timezone
from app.agents.state import ASIPState
from app.core.logging import get_logger
from app.agents.llm import get_llm

logger = get_logger("monitoring_agent")

THRESHOLDS = {
    "water_pressure": {"low_critical": 0.5, "low_high": 1.0, "high_critical": 8.0},
    "tank_level": {"overflow_critical": 95.0, "shortage_high": 10.0, "shortage_critical": 5.0},
    "power_consumption": {"overload_critical": 95.0, "overload_high": 85.0, "outage": 0.0},
}

SENSOR_TYPE_MAP = {
    "water_pressure": "water_pressure_drop",
    "tank_level_high": "tank_overflow",
    "tank_level_low": "water_shortage",
    "power_consumption_low": "power_outage",
    "power_consumption_high": "power_overload",
}


async def monitoring_agent(state: ASIPState) -> ASIPState:
    logger.info("MonitoringAgent: analysing sensor data", incident_id=state["incident_id"])

    # Manual complaints are pre-populated with incident_event; bypass rules and route forward
    if state.get("incident_event"):
        logger.info("MonitoringAgent: manual complaint detected, routing to decider", incident_id=state["incident_id"])
        return state

    sensor = state["sensor_data"]
    sensor_type = sensor.get("sensor_type", "")
    value = float(sensor.get("value", 0))

    incident_event = None

    # Rule-based anomaly detection (deterministic, fast, no LLM cost)
    if sensor_type == "water_pressure":
        if value <= THRESHOLDS["water_pressure"]["low_critical"]:
            incident_event = _make_event("water_pressure_drop", "critical", 0.97, value, "bar")
        elif value <= THRESHOLDS["water_pressure"]["low_high"]:
            incident_event = _make_event("water_pressure_drop", "high", 0.90, value, "bar")
        elif value >= THRESHOLDS["water_pressure"]["high_critical"]:
            incident_event = _make_event("abnormal_infrastructure", "high", 0.85, value, "bar")

    elif sensor_type == "tank_level":
        if value >= THRESHOLDS["tank_level"]["overflow_critical"]:
            incident_event = _make_event("tank_overflow", "critical", 0.98, value, "%")
        elif value <= THRESHOLDS["tank_level"]["shortage_critical"]:
            incident_event = _make_event("water_shortage", "critical", 0.96, value, "%")
        elif value <= THRESHOLDS["tank_level"]["shortage_high"]:
            incident_event = _make_event("water_shortage", "high", 0.88, value, "%")

    elif sensor_type == "power_consumption":
        if value <= THRESHOLDS["power_consumption"]["outage"]:
            incident_event = _make_event("power_outage", "critical", 0.99, value, "kW")
        elif value >= THRESHOLDS["power_consumption"]["overload_critical"]:
            incident_event = _make_event("power_overload", "critical", 0.95, value, "kW")
        elif value >= THRESHOLDS["power_consumption"]["overload_high"]:
            incident_event = _make_event("power_overload", "high", 0.87, value, "kW")

    if incident_event:
        logger.info(
            "Incident detected",
            type=incident_event["type"],
            severity=incident_event["severity"],
            confidence=incident_event["confidence"],
        )
        return {**state, "incident_event": incident_event, "next": "infrastructure_agent"}

    logger.info("No anomaly detected — sensor reading within normal range")
    return {**state, "next": "__end__"}


def _make_event(inc_type: str, severity: str, confidence: float, value: float, unit: str) -> dict:
    return {
        "type": inc_type,
        "severity": severity,
        "confidence": confidence,
        "description": f"Sensor reading: {value} {unit}. Anomaly classified as {inc_type}.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
