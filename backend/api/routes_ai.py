from typing import Optional, List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.user import User, UserRole
from backend.services.auth_service import get_current_user
from backend.ai.service import central_ai_service
from backend.ai.schemas import (
    CropRequirementPredictRequest,
    ApprovePredictionRequest,
    CorrectPredictionRequest,
    AIPredictionResponse,
    AIEngineStatsResponse,
)

router = APIRouter(prefix="/api/v1/ai", tags=["Central AI/ML Engine"])

def require_food_dept_or_admin(user: User = Depends(get_current_user)) -> User:
    """Enforces that only Food Department officers or Admins can generate and finalize crop requirements."""
    role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
    if role_str not in ("FOOD_DEPARTMENT", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Only Food Department Directorate or Administrators can manage crop requirement predictions."
        )
    return user

@router.post("/crop-requirement/predict", response_model=AIPredictionResponse)
def predict_crop_requirement(
    req: CropRequirementPredictRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_food_dept_or_admin)
):
    """
    POST /api/v1/ai/crop-requirement/predict
    Generates a new AI crop requirement baseline from real database records
    and stores the prediction immutably in ai_prediction_records.
    """
    return central_ai_service.predict_crop_requirement(db=db, req=req, user=current_user)

@router.get("/predictions", response_model=List[AIPredictionResponse])
def get_predictions(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    GET /api/v1/ai/predictions
    Retrieves stored predictions across all sectors, optionally filtered by review status.
    """
    return central_ai_service.get_predictions(db=db, status=status, limit=limit, offset=offset)

@router.get("/predictions/{id}", response_model=AIPredictionResponse)
def get_prediction_by_id(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    GET /api/v1/ai/predictions/{id}
    Retrieves a single prediction by database integer ID or string prediction_id.
    """
    return central_ai_service.get_prediction_by_id(db=db, pred_id_or_code=id)

@router.post("/predictions/{id}/approve", response_model=AIPredictionResponse)
def approve_prediction(
    id: str,
    req: Optional[ApprovePredictionRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_food_dept_or_admin)
):
    """
    POST /api/v1/ai/predictions/{id}/approve
    Human officer approves the AI recommendation with zero typing.
    Human final values are set equal to AI values, and original AI values remain unchanged.
    """
    notes = req.notes if req else "Approved without changes by Food Directorate"
    return central_ai_service.approve_prediction(db=db, pred_id_or_code=id, user=current_user, notes=notes)

@router.post("/predictions/{id}/correct", response_model=AIPredictionResponse)
def correct_prediction(
    id: str,
    req: CorrectPredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_food_dept_or_admin)
):
    """
    POST /api/v1/ai/predictions/{id}/correct
    Human officer overrides the AI recommendation with adjusted target metrics.
    Enforces mandatory operational justification.
    Never overwrites original AI values; stores human decisions in dedicated columns.
    """
    return central_ai_service.correct_prediction(
        db=db,
        pred_id_or_code=id,
        req=req,
        user=current_user
    )

@router.get("/stats", response_model=AIEngineStatsResponse)
def get_engine_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    GET /api/v1/ai/stats
    Returns real-time engine telemetry, model version, and prediction review statistics.
    """
    return central_ai_service.get_engine_stats(db=db)

