"""
KrushiSetu Major Warehouse Storage, Inventory & AI Stock Intelligence Routes
Task 6: Major Warehouse Storage Workflow
Linked: Batch ID -> Farmer ID -> Crop -> Weight/Quantity -> Task 5 AI/Human Grade -> Storage -> Inventory -> Dispatch
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.user import User
from backend.services.auth_service import get_current_user
from backend.ai.service import central_ai_service
from backend.ai.schemas import (
    CreateWarehouseStorageRequest,
    UpdateWarehouseStorageRequest,
    StorageRecordResponse,
    StorageRecordListResponse,
    WarehouseInventorySummary,
    AIStockInsightsResponse,
    AIStockRecommendationResponse,
)

router = APIRouter(tags=["Major Warehouse Storage, Inventory & AI Stock Intelligence"])

def require_warehouse_or_admin(user: User = Depends(get_current_user)) -> User:
    """Enforces that only Major Warehouse personnel or Admins can perform modifications/dispatches."""
    role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
    if role_str not in ("MAJOR_WAREHOUSE", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Only Major Warehouse staff or Administrators can modify storage records or record dispatches."
        )
    return user

# =============================================================================
# 1. MAJOR WAREHOUSE STORAGE RECORDS
# =============================================================================

@router.post("/api/v1/warehouse/storage", response_model=StorageRecordResponse)
def create_warehouse_storage(
    req: CreateWarehouseStorageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_warehouse_or_admin)
):
    """
    POST /api/v1/warehouse/storage
    Creates a certified storage entry for a verified batch.
    Links Batch ID -> Farmer ID -> Crop -> Weight -> Task 5 Grade -> Storage Location.
    Enforces inventory conservation and disallows dispatches exceeding stock.
    """
    return central_ai_service.create_warehouse_storage(db=db, req=req, user=current_user)

@router.get("/api/v1/warehouse/storage", response_model=StorageRecordListResponse)
def get_warehouse_storage_list(
    crop_name: Optional[str] = None,
    crop_category: Optional[str] = None,
    status: Optional[str] = None,
    batch_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    GET /api/v1/warehouse/storage
    Retrieves all storage records with filtering and resolved Task 5 certified quality grade.
    """
    items = central_ai_service.get_warehouse_storage_list(
        db=db,
        crop_name=crop_name,
        crop_category=crop_category,
        status=status,
        batch_id=batch_id,
    )
    return {"items": items, "total": len(items)}

@router.get("/api/v1/warehouse/storage/{storage_id}", response_model=StorageRecordResponse)
def get_warehouse_storage_by_id(
    storage_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    GET /api/v1/warehouse/storage/{storage_id}
    Retrieves a single storage entry by storage ID (e.g. KS-STR-8001) or database PK.
    """
    return central_ai_service.get_warehouse_storage_by_id(db=db, storage_id_or_pk=storage_id)

@router.put("/api/v1/warehouse/storage/{storage_id}", response_model=StorageRecordResponse)
def update_warehouse_storage(
    storage_id: str,
    req: UpdateWarehouseStorageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_warehouse_or_admin)
):
    """
    PUT /api/v1/warehouse/storage/{storage_id}
    Updates an existing storage record (e.g. incremental dispatch pick, reservation, silo location, notes).
    Strictly prevents dispatches exceeding available stock.
    Maintains full audit logging (old value -> new value, user, reason).
    Quality grade manipulation is prohibited.
    """
    return central_ai_service.update_warehouse_storage(
        db=db,
        storage_id_or_pk=storage_id,
        req=req,
        user=current_user
    )

# =============================================================================
# 2. MAJOR WAREHOUSE INVENTORY
# =============================================================================

@router.get("/api/v1/warehouse/inventory", response_model=WarehouseInventorySummary)
def get_warehouse_inventory(
    warehouse_id: Optional[str] = "MWH-PUN-01",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    GET /api/v1/warehouse/inventory
    Aggregates warehouse stock by crop variety:
    - Current stock, reserved stock, dispatched stock, available stock
    - Grade breakdown (A, B, C, REJECTED)
    - Storage silo/bay locations
    - Central AI consumption velocity & buffer coverage days
    """
    return central_ai_service.get_warehouse_inventory(db=db, warehouse_id=warehouse_id)

# =============================================================================
# 3. CENTRAL AI STOCK INTELLIGENCE & RECOMMENDATIONS
# =============================================================================

@router.get("/api/v1/ai/warehouse/stock-insights", response_model=AIStockInsightsResponse)
def get_warehouse_stock_insights(
    warehouse_id: Optional[str] = "MWH-PUN-01",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    GET /api/v1/ai/warehouse/stock-insights
    Central AI Stock Intelligence analytics:
    - Analyzes run-rates, buffer coverage days, and stock level status
    - Explains: 'WHY DID AI GIVE THIS RESULT?' with comprehensive multi-factor breakdown
    - Clearly handles data sparsity: outputs 'Insufficient historical data for reliable AI prediction'
    - Includes prototype model disclaimer
    """
    return central_ai_service.get_warehouse_stock_insights(db=db, warehouse_id=warehouse_id)

@router.get("/api/v1/ai/warehouse/stock-recommendations", response_model=AIStockRecommendationResponse)
def get_warehouse_stock_recommendations(
    warehouse_id: Optional[str] = "MWH-PUN-01",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    GET /api/v1/ai/warehouse/stock-recommendations
    Proactive replenishment and dispatch balancing alerts from Central AI Engine.
    """
    return central_ai_service.get_warehouse_stock_recommendations(db=db, warehouse_id=warehouse_id)
