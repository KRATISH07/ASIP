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

    # Enrich impact with predictive estimates (memory-enhanced + learning-corrected).
    try:
        from app.services.predictive_service import predict_impact
        from app.services.learning_service import compute_correction_factors
        from app.services import memory_service as _mem_svc

        incident_type = (incident_event or {}).get("type")

        # Pre-fetch historical context so predictive_service stays a pure function
        historical_context = []
        try:
            historical_context = await _mem_svc.retrieve_similar_incidents(
                {"incident_type": incident_type}, k=5
            ) or []
        except Exception as mem_err:
            logger.warning("Impact agent: memory retrieval failed", error=str(mem_err))

        # V5: Fetch feedback records for learning correction (read from DB directly,
        # not through memory_service which is protected and Chroma-based)
        correction_factors = None
        try:
            from app.db.session import AsyncSessionFactory
            from app.db.models.incident_memory import IncidentMemory
            from sqlalchemy import select
            import uuid as _uuid

            # Use a single session for both the correction query and the predicted-values write.
            uuid_obj = _uuid.UUID(str(state.get("incident_id"))) if state.get("incident_id") else None
            async with AsyncSessionFactory() as db:
                # 1. Fetch feedback records for learning correction
                stmt = (
                    select(
                        IncidentMemory.predicted_outage_hrs,
                        IncidentMemory.actual_outage_hrs,
                        IncidentMemory.predicted_cost,
                        IncidentMemory.actual_cost,
                    )
                    .where(IncidentMemory.incident_type == incident_type)
                    .where(IncidentMemory.actual_outage_hrs.is_not(None))
                    .order_by(IncidentMemory.created_at.desc())
                    .limit(20)
                )
                result = await db.execute(stmt)
                rows = result.mappings().all()

                feedback_records = [dict(r) for r in rows]
                correction_factors = compute_correction_factors(feedback_records)
                logger.info(
                    "Learning correction factors fetched",
                    incident_type=incident_type,
                    samples=correction_factors["outage_sample_count"],
                    correction_applied=correction_factors["correction_applied"],
                )

                # 2. Write predicted values to incident_memory (will be committed below).
                # Stored here to allow feedback_service to compute error = actual - predicted.
                if uuid_obj:
                    mem_stmt = select(IncidentMemory).where(
                        IncidentMemory.incident_uuid == uuid_obj
                    ).limit(1)
                    mem_result = await db.execute(mem_stmt)
                    _pending_mem_write = (db, mem_result.scalar_one_or_none())
                else:
                    _pending_mem_write = (db, None)

        except Exception as learn_err:
            logger.warning(
                "Learning service unavailable; using uncorrected prediction",
                error=str(learn_err),
            )
            _pending_mem_write = (None, None)

        preds = await predict_impact(
            incident_event or {},
            sensor_data=sensor_data or {},
            historical_context=historical_context,
            correction_factors=correction_factors,
        )

        # Attach full prediction under `impact_prediction` and merge key fields
        impact["impact_prediction"] = preds
        if preds.get("predicted_residents"):
            impact["estimated_residents"] = int(preds.get("predicted_residents"))
        if preds.get("predicted_outage_hrs"):
            impact["predicted_outage_hrs"] = float(preds.get("predicted_outage_hrs"))
        impact["prediction_confidence"] = float(preds.get("confidence_score", 0.0))

        # V5: Write predicted values to incident_memory using the session already opened above.
        db_session, mem_obj = _pending_mem_write if '_pending_mem_write' in dir() else (None, None)
        if db_session and mem_obj:
            try:
                mem_obj.predicted_outage_hrs = preds.get("predicted_outage_hrs")
                mem_obj.predicted_cost = preds.get("estimated_repair_cost")
                await db_session.commit()
                logger.info(
                    "Predicted values written to incident_memory",
                    incident_id=state.get("incident_id"),
                    predicted_outage_hrs=mem_obj.predicted_outage_hrs,
                    predicted_cost=mem_obj.predicted_cost,
                )
            except Exception as write_err:
                logger.warning(
                    "Could not write predicted values to incident_memory",
                    error=str(write_err),
                )

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
