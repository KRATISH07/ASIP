"""
Complaints API — Resident complaint lifecycle endpoints.

POST   /complaints              — create complaint
GET    /complaints              — list all complaints (manager/admin)
GET    /complaints/mine         — list own complaints (resident)
GET    /complaints/stats        — aggregate stats (manager/admin)
GET    /complaints/{id}         — get single complaint
PATCH  /complaints/{id}         — update complaint (manager/admin)
POST   /complaints/{id}/convert — convert to incident (manager/admin)

Access control is enforced via require_roles() at the route level.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user, require_roles
from app.db.models.user import User, UserRole
from app.db.models.complaint import ComplaintCategory, ComplaintStatus
from app.repositories.complaint_repo import ComplaintRepository
from app.schemas.complaint import (
    ComplaintCreate,
    ComplaintUpdate,
    ComplaintOut,
    ComplaintListOut,
    ComplaintStatsOut,
    ComplaintConvertRequest,
    ComplaintConvertResponse,
)
from app.services import complaint_service
from app.core.logging import get_logger

logger = get_logger("complaints_api")

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.post(
    "/",
    response_model=ComplaintOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new resident complaint",
)
async def create_complaint(
    payload: ComplaintCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = require_roles(
        UserRole.resident, UserRole.manager, UserRole.admin
    ),
) -> ComplaintOut:
    # Link resident_id from the user's profile (only for resident-role users)
    resident_id = (
        current_user.resident_id
        if current_user.role == UserRole.resident
        else None
    )
    complaint = await complaint_service.create_complaint(
        payload.model_dump(), db, resident_id=resident_id
    )
    return ComplaintOut.model_validate(complaint)


@router.get(
    "/stats",
    response_model=ComplaintStatsOut,
    summary="Get aggregate complaint statistics",
)
async def get_complaint_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = require_roles(UserRole.manager, UserRole.admin),
) -> ComplaintStatsOut:
    stats = await complaint_service.get_complaint_stats(db)
    return ComplaintStatsOut(**stats)


@router.get(
    "/mine",
    response_model=ComplaintListOut,
    summary="List complaints filed by the currently authenticated resident",
)
async def list_my_complaints(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = require_roles(UserRole.resident),
) -> ComplaintListOut:
    if not current_user.resident_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your account is not linked to a resident profile.",
        )
    repo = ComplaintRepository(db)
    items, total = await repo.list_complaints(
        resident_id=current_user.resident_id, page=page, page_size=page_size
    )
    return ComplaintListOut(items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/",
    response_model=ComplaintListOut,
    summary="List all complaints (manager/admin)",
)
async def list_complaints(
    complaint_status: Optional[ComplaintStatus] = Query(None, alias="status"),
    category: Optional[ComplaintCategory] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = require_roles(UserRole.manager, UserRole.admin),
) -> ComplaintListOut:
    repo = ComplaintRepository(db)
    items, total = await repo.list_complaints(
        status=complaint_status,
        category=category.value if category else None,
        page=page,
        page_size=page_size,
    )
    return ComplaintListOut(items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/{complaint_id}",
    response_model=ComplaintOut,
    summary="Get complaint detail",
)
async def get_complaint(
    complaint_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ComplaintOut:
    repo = ComplaintRepository(db)
    complaint = await repo.get_by_id(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail=f"Complaint {complaint_id} not found.")

    # Residents can only view their own complaints
    if current_user.role == UserRole.resident:
        if complaint.resident_id != current_user.resident_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own complaints.",
            )

    return ComplaintOut.model_validate(complaint)


@router.patch(
    "/{complaint_id}",
    response_model=ComplaintOut,
    summary="Update complaint status or assignment (manager/admin)",
)
async def update_complaint(
    complaint_id: uuid.UUID,
    payload: ComplaintUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = require_roles(UserRole.manager, UserRole.admin),
) -> ComplaintOut:
    repo = ComplaintRepository(db)
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    complaint = await repo.update(complaint_id, update_data)
    if not complaint:
        raise HTTPException(status_code=404, detail=f"Complaint {complaint_id} not found.")
    await db.commit()
    return ComplaintOut.model_validate(complaint)


@router.post(
    "/{complaint_id}/convert",
    response_model=ComplaintConvertResponse,
    summary="Convert complaint to a formal incident (manager/admin)",
    description=(
        "Creates a formal Incident record from the complaint and launches the full "
        "LangGraph AI workflow. The complaint status is updated to "
        "`converted_to_incident` and linked to the created incident.\n\n"
        "**Atomicity:** if incident creation fails, the complaint status is NOT changed."
    ),
)
async def convert_complaint(
    complaint_id: uuid.UUID,
    payload: ComplaintConvertRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = require_roles(UserRole.manager, UserRole.admin),
) -> ComplaintConvertResponse:
    try:
        result = await complaint_service.convert_to_incident(
            complaint_id=complaint_id,
            db=db,
            background_tasks=background_tasks,
            incident_type_override=payload.incident_type,
            severity_override=payload.override_severity,
        )
        return ComplaintConvertResponse(**result)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        logger.error(
            "Complaint conversion failed",
            complaint_id=str(complaint_id),
            error=str(exc),
        )
        raise HTTPException(status_code=500, detail="Failed to convert complaint to incident.")
