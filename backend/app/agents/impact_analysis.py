"""
ImpactAnalysisAgent: determines affected towers/apartments/residents
and calculates incident priority score.
"""
from app.agents.state import ASIPState, ImpactReport
from app.core.logging import get_logger

logger = get_logger("impact_agent")

SEVERITY_SCORES = {"low": 0.25, "medium": 0.50, "high": 0.75, "critical": 1.0}
PRIORITY_MAP = {(0.0, 0.4): "low", (0.4, 0.7): "medium", (0.7, 0.9): "high", (0.9, 1.1): "critical"}


async def impact_analysis_agent(state: ASIPState) -> ASIPState:
    logger.info("ImpactAnalysisAgent: calculating impact", incident_id=state["incident_id"])

    incident_event = state.get("incident_event")
    sensor_data = state.get("sensor_data", {})

    # In production this would query the DB for tower/apartment data.
    # For now we use simulated impact based on severity.
    severity = incident_event["severity"] if incident_event else "medium"
    severity_score = SEVERITY_SCORES.get(severity, 0.5)

    # Simulated impact calculation
    if severity == "critical":
        affected_apartments = 120
        estimated_residents = 350
    elif severity == "high":
        affected_apartments = 60
        estimated_residents = 180
    elif severity == "medium":
        affected_apartments = 30
        estimated_residents = 90
    else:
        affected_apartments = 10
        estimated_residents = 25

    tower_id = str(sensor_data.get("tower_id", "Unknown Tower"))
    affected_towers = [tower_id]

    # Priority calculation: severity score * confidence
    confidence = incident_event.get("confidence", 0.8) if incident_event else 0.5
    priority_score = severity_score * confidence

    priority = "medium"
    for (low, high), label in PRIORITY_MAP.items():
        if low <= priority_score < high:
            priority = label
            break

    impact: ImpactReport = {
        "affected_towers": affected_towers,
        "affected_apartments": affected_apartments,
        "estimated_residents": estimated_residents,
        "severity_score": round(priority_score, 3),
        "priority": priority,
    }

    # Enrich impact with predictive estimates (memory-enhanced) when available.
    try:
        from app.services.predictive_service import predict_impact

        preds = await predict_impact(incident_event or {}, sensor_data or {}, k=5)
        # Attach full prediction under `impact_prediction` and merge key fields
        impact["impact_prediction"] = preds
        # Overlay a few convenient fields so downstream agents (contractor selection)
        # can consume predictions transparently via `impact`.
        if preds.get("predicted_residents"):
            impact["estimated_residents"] = int(preds.get("predicted_residents"))
        if preds.get("predicted_outage_hrs"):
            impact["predicted_outage_hrs"] = float(preds.get("predicted_outage_hrs"))
        impact["prediction_confidence"] = float(preds.get("confidence_score", 0.0))
    except Exception as e:
        # If prediction service fails, continue with heuristic impact only
        logger.warning("Predictive service failed; continuing with heuristic impact", error=str(e))

    logger.info(
        "Impact calculated",
        residents=estimated_residents,
        priority=priority,
        score=priority_score,
    )
    return {**state, "impact": impact, "next": "contractor_agent"}
