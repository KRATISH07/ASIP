"""Autonomous Decision Engine API

POST /decision/analyze — Given an incident type and severity, computes and
returns a full autonomous decision: escalation, notification, backup, and
contractor auto-dispatch recommendations.

Memory is fetched at the API layer (same pattern as /predict/impact) so the
decision_service stays a pure function with no hidden async dependencies.
"""
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.db.models.user import User
from app.schemas.decision import DecisionRequest, DecisionResponse
from app.schemas.predict import PredictImpactRequest
from app.services.decision_service import make_decision
from app.services.predictive_service import predict_impact
from app.core.logging import get_logger

logger = get_logger("decision_api")

router = APIRouter(prefix="/decision", tags=["Decision Engine"])


@router.post(
    "/analyze",
    response_model=DecisionResponse,
    summary="Compute autonomous incident decision",
    description=(
        "Given an incident type and severity, runs the full autonomous decision "
        "engine: fetches historical context, generates a predictive impact analysis, "
        "then computes escalation, notification, backup, and auto-dispatch decisions. "
        "Returns a structured decision with risk score and reasoning."
    ),
)
async def analyze_decision(
    payload: DecisionRequest,
    current_user: User = Depends(get_current_user),
) -> DecisionResponse:
    # Step 1: Fetch historical context at API layer (keeps services pure)
    historical_context = []
    try:
        from app.services import memory_service as _mem_svc
        historical_context = await _mem_svc.retrieve_similar_incidents(
            {"incident_type": payload.incident_type}, k=5
        ) or []
    except Exception as mem_err:
        logger.warning(
            "Decision API: memory retrieval failed, using heuristics",
            error=str(mem_err),
        )

    # Step 2: Build incident_event dict
    incident_event = {
        "type": payload.incident_type,
        "incident_type": payload.incident_type,
        "severity": payload.severity,
    }

    # Step 3: Generate impact prediction (needed by decision engine for risk score)
    impact_prediction = {}
    try:
        impact_prediction = await predict_impact(
            incident_event=incident_event,
            sensor_data={},
            historical_context=historical_context,
        )
    except Exception as pred_err:
        logger.warning(
            "Decision API: prediction failed, decision will use defaults",
            error=str(pred_err),
        )

    # Step 4: Run the autonomous decision engine (no contractors at API level —
    # contractor candidates come from the DB which isn't queried here for performance)
    decision = await make_decision(
        incident_event=incident_event,
        impact_prediction=impact_prediction,
        contractor_candidates=[],   # API-level call has no DB; agent workflow has full list
        historical_context=historical_context,
    )

    logger.info(
        "Decision API response",
        incident_type=payload.incident_type,
        severity=payload.severity,
        risk_score=decision.get("estimated_risk_score"),
        escalation=decision.get("requires_immediate_escalation"),
    )

    return DecisionResponse(**decision)
