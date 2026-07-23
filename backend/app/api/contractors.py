import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies import get_current_user, require_manager_or_above, require_roles
from app.repositories.contractor_repo import ContractorRepository
from app.schemas.contractor import ContractorCreate, ContractorOut
from app.db.models.user import User, UserRole
from typing import Any
from app.services import contractor_service
from app.schemas.contractor import ContractorOut

router = APIRouter(prefix="/contractors", tags=["Contractors"])


@router.get("/", response_model=List[ContractorOut], summary="List all active contractors")
async def list_contractors(
    specialization: Optional[str] = Query(None, description="Filter by specialization e.g. water"),
    db: AsyncSession = Depends(get_db),
    current_user: User = require_roles(UserRole.manager, UserRole.admin, UserRole.contractor),
):
    repo = ContractorRepository(db)
    contractors = await repo.list_active(specialization=specialization)
    return contractors


@router.get("/rankings", summary="Get ranked contractors for an incident")
async def get_rankings(
    incident_type: Optional[str] = Query(None, description="Incident type (used to match specializations)"),
    k: int = Query(5, description="Number of top contractors to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = require_roles(UserRole.manager, UserRole.admin),
):
    ranked = await contractor_service.rank_contractors(db, incident_type=incident_type, k=k)
    return ranked


@router.get("/{contractor_id}", response_model=ContractorOut, summary="Get contractor detail")
async def get_contractor(
    contractor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = require_roles(UserRole.manager, UserRole.admin, UserRole.contractor),
):
    repo = ContractorRepository(db)
    contractor = await repo.get_by_id(contractor_id)
    if not contractor:
        raise HTTPException(status_code=404, detail=f"Contractor {contractor_id} not found.")
    return contractor


@router.post(
    "/",
    response_model=ContractorOut,
    status_code=201,
    summary="Add a new contractor (Admin/Manager only)",
)
async def create_contractor(
    payload: ContractorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    repo = ContractorRepository(db)
    contractor = await repo.create(payload.model_dump())
    return contractor



@router.put("/{contractor_id}", response_model=ContractorOut, summary="Update contractor (Manager/Admin)")
async def update_contractor(
    contractor_id: uuid.UUID,
    payload: ContractorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    repo = ContractorRepository(db)
    contractor = await repo.get_by_id(contractor_id)
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")
    for k, v in payload.model_dump().items():
        setattr(contractor, k, v)
    await db.flush()
    await db.refresh(contractor)
    return contractor


@router.delete("/{contractor_id}", status_code=200, summary="Deactivate a contractor (Admin/Manager only)")
async def delete_contractor(
    contractor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_above),
):
    repo = ContractorRepository(db)
    contractor = await repo.get_by_id(contractor_id)
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")
    contractor.is_active = False
    await db.commit()
    return {"message": "Contractor deactivated successfully"}
