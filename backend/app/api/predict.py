"""Predictive Impact Analysis API

POST /predict/impact  — Returns a full impact prediction for a given
incident type and severity.

The route is responsible for fetching historical context from the memory
layer before delegating to the pure predictive_service function. This
prevents any async event-loop issues that would arise from the service
touching the DB session directly.
"""
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.db.models.user import User
from app.schemas.predict import PredictImpactRequest, PredictImpactResponse
from app.services.predictive_service import predict_impact
from app.core.logging import get_logger

logger = get_logger("predict_api")

router = APIRouter(prefix="/predict", tags=["Predictive"])


@router.post(
    "/impact",
    response_model=PredictImpactResponse,
    summary="Predict incident impact using historical memory",
    description=(
        "Given an incident type and severity, returns a data-driven prediction "
        "of affected residents, estimated outage duration, repair costs, and risk "
        "scores — enriched by similar historical incidents from memory."
    ),
)
async def predict_impact_endpoint(
    payload: PredictImpactRequest,
    current_user: User = Depends(get_current_user),
) -> PredictImpactResponse:
    # Step 1: fetch historical context at the API layer (keeps service pure)
    historical_context = []
    try:
        from app.services import memory_service as _mem_svc
        historical_context = await _mem_svc.retrieve_similar_incidents(
            {"incident_type": payload.incident_type}, k=5
        ) or []
    except Exception as mem_err:
        logger.warning(
            "Predict API: memory retrieval failed, falling back to heuristics",
            error=str(mem_err),
        )

    # Step 2: build incident_event dict expected by predictive_service
    incident_event = {
        "type": payload.incident_type,
        "incident_type": payload.incident_type,
        "severity": payload.severity,
    }

    # Step 3: call the pure prediction engine
    prediction = await predict_impact(
        incident_event=incident_event,
        sensor_data={},
        historical_context=historical_context,
    )

    logger.info(
        "Predictive impact API response",
        incident_type=payload.incident_type,
        severity=payload.severity,
        confidence=prediction.get("confidence_score"),
    )

    return PredictImpactResponse(**prediction)
