from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.user import User
from backend.services.auth_service import get_current_user
from backend.ai.service import central_ai_service
from backend.ai.schemas import (
    FarmerRecommendationPredictRequest,
    ApproveFarmerRecommendationRequest,
    CorrectFarmerRecommendationRequest,
    AIFarmerRecommendationResponse,
    AIFarmerRecommendationBatchResponse,
)

router = APIRouter(prefix="/api/v1/ai/farmer-recommendation", tags=["Central AI - Farmer Recommendation"])

def require_gp_or_admin(user: User = Depends(get_current_user)) -> User:
    """Enforces that only Gram Panchayat officers or Admins can access Farmer AI recommendations."""
    role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
    if role_str not in ("GRAM_PANCHAYAT", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Only Gram Panchayat officers or Administrators can generate or modify Farmer recommendations."
        )
    return user

@router.post("/predict", response_model=AIFarmerRecommendationBatchResponse)
def predict_farmer_recommendations(
    req: FarmerRecommendationPredictRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_gp_or_admin)
):
    """
    POST /api/v1/ai/farmer-recommendation/predict
    Generates farmer-wise AI crop recommendations from an approved GP allocation.
    Enforces land caps (allocated <= available) and quota conservation.
    """
    return central_ai_service.predict_farmer_recommendations(db=db, req=req, user=current_user)

@router.get("", response_model=List[AIFarmerRecommendationResponse])
def get_farmer_recommendations(
    batch_code: Optional[str] = None,
    status: Optional[str] = None,
    gp_name: Optional[str] = None,
    crop_name: Optional[str] = None,
    farmer_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    GET /api/v1/ai/farmer-recommendation
    Retrieves stored farmer recommendations with strict Gram Panchayat jurisdiction enforcement.
    """
    role_str = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    if role_str not in ("GRAM_PANCHAYAT", "ADMIN", "PANCHAYAT_SAMITI", "FOOD_DEPARTMENT", "FARMER"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: You do not have authorization to view Farmer crop recommendations."
        )
    return central_ai_service.get_farmer_recommendations(
        db=db,
        user=current_user,
        batch_code=batch_code,
        status=status,
        gp_name=gp_name,
        crop_name=crop_name,
        farmer_id=farmer_id,
        limit=limit,
        offset=offset
    )

@router.get("/{id}", response_model=AIFarmerRecommendationResponse)
def get_farmer_recommendation_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    GET /api/v1/ai/farmer-recommendation/{id}
    Retrieves full recommendation details, agronomic suitability metrics, soil report URL, and audit history.
    """
    role_str = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    if role_str not in ("GRAM_PANCHAYAT", "ADMIN", "PANCHAYAT_SAMITI", "FOOD_DEPARTMENT", "FARMER"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: You do not have authorization to view this recommendation."
        )
    return central_ai_service.get_farmer_recommendation_by_id(db=db, rec_id=id, user=current_user)

@router.post("/{id}/approve", response_model=AIFarmerRecommendationResponse)
def approve_farmer_recommendation(
    id: int,
    req: ApproveFarmerRecommendationRequest = ApproveFarmerRecommendationRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_gp_or_admin)
):
    """
    POST /api/v1/ai/farmer-recommendation/{id}/approve
    One-click approval of AI recommended crop allocation for a farmer.
    Preserves original AI values and updates gp_crop_assignments.
    """
    return central_ai_service.approve_farmer_recommendation(db=db, rec_id=id, user=current_user, notes=req.notes)

@router.post("/{id}/correct", response_model=AIFarmerRecommendationResponse)
def correct_farmer_recommendation(
    id: int,
    req: CorrectFarmerRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_gp_or_admin)
):
    """
    POST /api/v1/ai/farmer-recommendation/{id}/correct
    Human review and override of AI recommendation.
    Mandatory operational justification required (min 5 chars).
    Validates farmer land boundaries.
    """
    return central_ai_service.correct_farmer_recommendation(db=db, rec_id=id, req=req, user=current_user)

@router.post("/batch/{batch_code}/approve")
def batch_approve_farmer_recommendations(
    batch_code: str,
    req: ApproveFarmerRecommendationRequest = ApproveFarmerRecommendationRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_gp_or_admin)
):
    """
    POST /api/v1/ai/farmer-recommendation/batch/{batch_code}/approve
    One-click batch approval for all pending farmer recommendations under a GP allocation batch.
    """
    return central_ai_service.batch_approve_farmer_recommendations(db=db, batch_code=batch_code, user=current_user, notes=req.notes)
