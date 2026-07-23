"""
Complaint Service — Resident complaint lifecycle management.

Responsibilities:
- Create complaints (with optional resident linking)
- Convert complaints to formal Incidents + launch LangGraph workflow
- Aggregate complaint statistics

Architecture:
    Complaint is created in the tenant DB schema.
    Conversion creates an Incident and queues the standard AI workflow.
    The complaint's linked_incident_id and status are updated atomically with
    the incident creation — if either fails the transaction rolls back.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.complaint_repo import ComplaintRepository
from app.repositories.incident_repo import IncidentRepository
from app.db.models.complaint import (
    Complaint, ComplaintStatus, CATEGORY_TO_INCIDENT_TYPE
)
from app.db.models.incident import IncidentType, IncidentSeverity, IncidentStatus
from app.core.logging import get_logger

logger = get_logger("complaint_service")

# Priority → IncidentSeverity mapping
_PRIORITY_TO_SEVERITY = {
    "low":    IncidentSeverity.low,
    "medium": IncidentSeverity.medium,
    "high":   IncidentSeverity.high,
    "urgent": IncidentSeverity.critical,
}


async def create_complaint(
    data: dict,
    db: AsyncSession,
    resident_id: Optional[uuid.UUID] = None,
) -> Complaint:
    """
    Insert a new complaint record.

    Parameters
    ----------
    data : dict
        Validated complaint fields (title, description, category, priority).
    db : AsyncSession
    resident_id : UUID | None
        Set from the authenticated user's resident_id link. None for manager-created complaints.
    """
    repo = ComplaintRepository(db)
    if resident_id:
        data["resident_id"] = resident_id
    data.setdefault("status", ComplaintStatus.submitted)
    complaint = await repo.create(data)
    await db.commit()
    logger.info(
        "Complaint created",
        complaint_id=str(complaint.id),
        category=data.get("category"),
        priority=data.get("priority"),
    )
    return complaint


async def convert_to_incident(
    complaint_id: uuid.UUID,
    db: AsyncSession,
    background_tasks: BackgroundTasks,
    incident_type_override: Optional[str] = None,
    severity_override: Optional[str] = None,
) -> dict:
    """
    Convert a complaint to a formal Incident and launch the LangGraph workflow.

    The operation is atomic:
      1. Fetch complaint (raises ValueError if not found or already converted)
      2. Determine incident_type from category mapping (or override)
      3. Create Incident record
      4. Update complaint: status = converted_to_incident, linked_incident_id
      5. Commit transaction
      6. Queue background workflow task

    If steps 1–5 fail, the transaction rolls back. The complaint status is
    NOT changed unless the incident record is successfully created.

    Parameters
    ----------
    complaint_id : UUID
    db : AsyncSession
    background_tasks : BackgroundTasks  FastAPI background task queue
    incident_type_override : str | None  Override category-mapped incident type
    severity_override : str | None       Override priority-mapped severity

    Returns
    -------
    dict: { complaint_id, incident_id, workflow_queued }
    """
    complaint_repo = ComplaintRepository(db)
    incident_repo = IncidentRepository(db)

    complaint = await complaint_repo.get_by_id(complaint_id)
    if not complaint:
        raise ValueError(f"Complaint {complaint_id} not found.")
    if complaint.status == ComplaintStatus.converted_to_incident:
        raise ValueError(f"Complaint {complaint_id} has already been converted to an incident.")

    # Resolve incident type
    raw_type = incident_type_override or CATEGORY_TO_INCIDENT_TYPE.get(
        complaint.category.value, "abnormal_infrastructure"
    )
    try:
        incident_type = IncidentType(raw_type)
    except ValueError:
        incident_type = IncidentType.abnormal_infrastructure

    # Resolve severity
    raw_severity = severity_override or complaint.priority.value
    severity = _PRIORITY_TO_SEVERITY.get(raw_severity, IncidentSeverity.medium)

    # Create the incident
    incident_data = {
        "type": incident_type,
        "severity": severity,
        "confidence": 0.7,
        "status": IncidentStatus.detected,
        "description": f"[Complaint] {complaint.title}: {complaint.description}",
        "detected_at": datetime.now(timezone.utc),
        "sensor_data": {
            "source": "complaint",
            "complaint_id": str(complaint_id),
            "category": complaint.category.value,
        },
    }
    incident = await incident_repo.create(incident_data)

    # Update complaint atomically
    await complaint_repo.update(complaint_id, {
        "status": ComplaintStatus.converted_to_incident,
        "linked_incident_id": incident.id,
    })

    await db.commit()

    # Queue the AI workflow as background task
    sensor_payload = {
        "tower_id": str(uuid.uuid4()),  # no tower context for complaints
        "sensor_type": "manual_complaint",
        "value": 1.0,
        "unit": "report",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": {"complaint_id": str(complaint_id)},
    }
    background_tasks.add_task(
        _run_complaint_workflow,
        sensor_payload,
        str(incident.id),
    )

    logger.info(
        "Complaint converted to incident",
        complaint_id=str(complaint_id),
        incident_id=str(incident.id),
        incident_type=incident_type.value,
        severity=severity.value,
    )
    return {
        "complaint_id": complaint_id,
        "incident_id": str(incident.id),
        "workflow_queued": True,
    }


async def _run_complaint_workflow(sensor_payload: dict, incident_id: str) -> None:
    """Background task: runs the AI workflow for a complaint-derived incident."""
    from app.db.session import AsyncSessionFactory
    from app.services.workflow_service import WorkflowService

    logger.info("Starting complaint-derived incident workflow", incident_id=incident_id)
    try:
        async with AsyncSessionFactory() as db:
            service = WorkflowService(db)
            await service.process_sensor_data(sensor_payload, incident_id=incident_id)
            logger.info("Complaint workflow completed", incident_id=incident_id)
    except Exception as exc:
        logger.error(
            "Complaint workflow failed",
            incident_id=incident_id,
            error=str(exc),
        )


async def get_complaint_stats(db: AsyncSession) -> dict:
    """Return aggregate complaint counts and average resolution time."""
    repo = ComplaintRepository(db)
    return await repo.get_stats()
