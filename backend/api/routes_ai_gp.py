from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.user import User
from backend.services.auth_service import get_current_user
from backend.ai.service import central_ai_service
from backend.ai.schemas import (
    GPAllocationPredictRequest,
    ApproveGPAllocationRequest,
    CorrectGPAllocationRequest,
    AIGPAllocationResponse,
    AIGPAllocationBatchResponse,
)

router = APIRouter(prefix="/api/v1/ai/gp-allocation", tags=["Central AI - GP Allocation"])

def require_ps_or_admin(user: User = Depends(get_current_user)) -> User:
    """Enforces that only Panchayat Samiti officers, Food Dept, or Admins can access GP AI allocations."""
    role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
    if role_str not in ("PANCHAYAT_SAMITI", "ADMIN", "FOOD_DEPARTMENT"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Only Panchayat Samiti officers or Administrators can manage GP allocations."
        )
    return user

def require_ps_officer_or_admin(user: User = Depends(get_current_user)) -> User:
    """Enforces that only Panchayat Samiti officers or Admins can approve or modify GP AI allocations."""
    role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
    if role_str not in ("PANCHAYAT_SAMITI", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Only Panchayat Samiti officers or Administrators can approve or correct GP allocations."
        )
    return user

@router.post("/predict", response_model=AIGPAllocationBatchResponse)
def predict_gp_allocation(
    req: GPAllocationPredictRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_ps_or_admin)
):
    """
    POST /api/v1/ai/gp-allocation/predict
    Generates Gram Panchayat-wise AI crop allocations from an approved Food Department requirement.
    Enforces quota conservation: sum(allocations) == total_quota_mt.
    """
    return central_ai_service.predict_gp_allocation(db=db, req=req, user=current_user)

@router.get("", response_model=List[AIGPAllocationResponse])
def get_gp_allocations(
    batch_code: Optional[str] = None,
    status: Optional[str] = None,
    crop_name: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    GET /api/v1/ai/gp-allocation
    Retrieves stored GP allocations with strict Panchayat Samiti jurisdiction enforcement.
    """
    role_str = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    if role_str not in ("PANCHAYAT_SAMITI", "ADMIN", "FOOD_DEPARTMENT", "GRAM_PANCHAYAT"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: You do not have authorization to view Panchayat Samiti crop allocations."
        )
    return central_ai_service.get_gp_allocations(
        db=db,
        user=current_user,
        batch_code=batch_code,
        status=status,
        crop_name=crop_name,
        limit=limit,
        offset=offset
    )

@router.get("/{id}", response_model=AIGPAllocationResponse)
def get_gp_allocation_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    GET /api/v1/ai/gp-allocation/{id}
    Retrieves full allocation details, suitability metrics, and audit history.
    """
    role_str = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    if role_str not in ("PANCHAYAT_SAMITI", "ADMIN", "FOOD_DEPARTMENT", "GRAM_PANCHAYAT"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: You do not have authorization to view this allocation."
        )
    return central_ai_service.get_gp_allocation_by_id(db=db, alloc_id=id, user=current_user)

@router.post("/{id}/approve", response_model=AIGPAllocationResponse)
def approve_gp_allocation(
    id: int,
    req: ApproveGPAllocationRequest = ApproveGPAllocationRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_ps_officer_or_admin)
):
    """
    POST /api/v1/ai/gp-allocation/{id}/approve
    One-click approval of AI recommended allocation for a Gram Panchayat.
    Copies AI values to human final columns and preserves original AI values.
    """
    return central_ai_service.approve_gp_allocation(db=db, alloc_id=id, user=current_user, notes=req.notes)

@router.post("/{id}/correct", response_model=AIGPAllocationResponse)
def correct_gp_allocation(
    id: int,
    req: CorrectGPAllocationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_ps_officer_or_admin)
):
    """
    POST /api/v1/ai/gp-allocation/{id}/correct
    Human review and override of AI recommendation.
    Mandatory operational justification required.
    Validates total quota conservation.
    Original AI recommendation is never overwritten.
    """
    return central_ai_service.correct_gp_allocation(db=db, alloc_id=id, req=req, user=current_user)

@router.post("/batch/{batch_code}/approve")
def batch_approve_gp_allocations(
    batch_code: str,
    req: ApproveGPAllocationRequest = ApproveGPAllocationRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_ps_officer_or_admin)
):
    """
    POST /api/v1/ai/gp-allocation/batch/{batch_code}/approve
    One-click batch approval for all pending Gram Panchayat allocations under a requirement run.
    """
    return central_ai_service.batch_approve_gp_allocations(db=db, batch_code=batch_code, user=current_user, notes=req.notes)

