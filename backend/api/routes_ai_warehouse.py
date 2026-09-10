from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.user import User
from backend.services.auth_service import get_current_user
from backend.ai.service import central_ai_service
from backend.ai.schemas import (
    WarehouseGradingAnalyzeRequest,
    ApproveWarehouseGradingRequest,
    CorrectWarehouseGradingRequest,
    AIWarehouseGradingResponse,
    AIWarehouseGradingListResponse,
)

router = APIRouter(prefix="/api/v1/ai/warehouse/grading", tags=["Central AI - Major Warehouse Crop Quality & Grading"])

def require_warehouse_or_admin(user: User = Depends(get_current_user)) -> User:
    """Enforces that only Major Warehouse officers or Admins can approve or correct grading."""
    role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
    if role_str not in ("MAJOR_WAREHOUSE", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Only Major Warehouse inspectors or Administrators can certify crop grading."
        )
    return user

@router.post("/analyze", response_model=AIWarehouseGradingResponse)
def analyze_crop_quality(
    req: WarehouseGradingAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    POST /api/v1/ai/warehouse/grading/analyze
    Analyzes optical frame / uploaded crop sample using Central AI Computer Vision.
    Evaluates 12 visual defect parameters and establishes suggested grade.
    The AI prediction NEVER becomes the final grade automatically.
    """
    return central_ai_service.analyze_crop_quality(db=db, req=req, user=current_user)

@router.get("", response_model=List[AIWarehouseGradingResponse])
def get_warehouse_gradings(
    batch_id: Optional[str] = None,
    status: Optional[str] = None,
    crop_name: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    GET /api/v1/ai/warehouse/grading
    Retrieves stored grading records with full optical parameter breakdown.
    """
    return central_ai_service.get_warehouse_gradings(
        db=db,
        user=current_user,
        batch_id=batch_id,
        status=status,
        crop_name=crop_name,
        limit=limit,
        offset=offset
    )

@router.get("/{id}", response_model=AIWarehouseGradingResponse)
def get_warehouse_grading_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    GET /api/v1/ai/warehouse/grading/{id}
    Retrieves full details of a specific AI crop grading record.
    """
    return central_ai_service.get_warehouse_grading_by_id(db=db, rec_id=id, user=current_user)

@router.post("/{id}/approve", response_model=AIWarehouseGradingResponse)
def approve_warehouse_grading(
    id: int,
    req: ApproveWarehouseGradingRequest = ApproveWarehouseGradingRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_warehouse_or_admin)
):
    """
    POST /api/v1/ai/warehouse/grading/{id}/approve
    One-click zero-typing approval of AI suggested grade & score.
    Preserves original AI predictions immutably and syncs to major_warehouse_intakes.
    """
    return central_ai_service.approve_warehouse_grading(
        db=db,
        rec_id=id,
        user=current_user,
        notes=req.notes
    )

@router.post("/{id}/correct", response_model=AIWarehouseGradingResponse)
def correct_warehouse_grading(
    id: int,
    req: CorrectWarehouseGradingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_warehouse_or_admin)
):
    """
    POST /api/v1/ai/warehouse/grading/{id}/correct
    Human inspector override of AI grading result.
    Enforces mandatory operational justification (min 5 characters).
    Preserves original AI predictions immutably in dual-storage architecture.
    """
    return central_ai_service.correct_warehouse_grading(
        db=db,
        rec_id=id,
        req=req,
        user=current_user
    )

