import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies import get_current_user
from app.db.models.user import User
from app.repositories.incident_repo import IncidentRepository
from app.schemas.incident import (
    SensorDataPayload, IncidentCreate, IncidentUpdate,
    IncidentOut, IncidentListOut,
)
from app.db.models.incident import IncidentType, IncidentSeverity, IncidentStatus

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.post(
    "/sensor-data",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest sensor reading and trigger AI workflow",
)
async def ingest_sensor_data(
    payload: SensorDataPayload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Accepts a raw sensor reading. Runs anomaly detection and, if an incident is
    detected, launches the full multi-agent LangGraph workflow in the background.
    """
    from app.services.workflow_service import WorkflowService
    service = WorkflowService(db)
    incident = await service.process_sensor_data(payload.model_dump())
    if incident:
        return {
            "message": "Incident detected. AI workflow launched.",
            "incident_id": str(incident.id),
            "severity": incident.severity.value,
        }
    return {"message": "Sensor reading processed. No incident detected."}


@router.post(
    "/",
    response_model=IncidentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Manually create an incident",
)
async def create_incident(
    payload: IncidentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = IncidentRepository(db)
    data = payload.model_dump()
    data["detected_at"] = datetime.now(timezone.utc)
    incident = await repo.create(data)
    return incident


@router.get(
    "/",
    response_model=IncidentListOut,
    summary="List incidents with optional filters",
)
async def list_incidents(
    status_filter: Optional[IncidentStatus] = Query(None, alias="status"),
    severity: Optional[IncidentSeverity] = Query(None),
    tower_id: Optional[uuid.UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = IncidentRepository(db)
    items, total = await repo.list_incidents(
        status=status_filter,
        severity=severity,
        tower_id=tower_id,
        page=page,
        page_size=page_size,
    )
    return IncidentListOut(items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/{incident_id}",
    response_model=IncidentOut,
    summary="Get full incident detail with AI decision",
)
async def get_incident(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = IncidentRepository(db)
    incident = await repo.get_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found.")
    return incident


@router.patch(
    "/{incident_id}/status",
    response_model=IncidentOut,
    summary="Update incident status",
)
async def update_incident_status(
    incident_id: uuid.UUID,
    payload: IncidentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = IncidentRepository(db)
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    incident = await repo.update(incident_id, update_data)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found.")
    return incident
