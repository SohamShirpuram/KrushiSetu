"""
KrushiSetu Major Warehouse -> Minor Warehouse Dispatch & Truck Tracking Routes
Task 7: Major Warehouse Dispatch, Driver GPS Tracking & Minor Warehouse Receiving
Linked: Batch ID -> Farmer ID -> Crop -> Task 5 Confirmed Grade -> Sent Qty -> Truck -> Driver -> GPS -> Minor WH -> Receiving
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.user import User
from backend.services.auth_service import get_current_user
from backend.ai.service import central_ai_service
from backend.ai.schemas import (
    CreateDispatchPlanRequest,
    UpdateDispatchRequest,
    StartDispatchTransitRequest,
    UpdateGPSLocationRequest,
    ReceiveMinorWarehouseDispatchRequest,
    DispatchRecordResponse,
    DispatchRecordListResponse,
    TruckRegistryResponse,
    CreateTruckRequest,
    DispatchTrackingResponse,
)

router = APIRouter(tags=["Major Warehouse Dispatch & Truck Tracking"])

def require_major_warehouse_or_admin(user: User = Depends(get_current_user)) -> User:
    role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
    if role_str not in ("MAJOR_WAREHOUSE", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Only Major Warehouse staff or Administrators can create or modify dispatches."
        )
    return user

def require_minor_warehouse_or_admin(user: User = Depends(get_current_user)) -> User:
    role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
    if role_str not in ("MINOR_WAREHOUSE", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Only Minor Warehouse staff or Administrators can receive inward dispatches."
        )
    return user

def require_authenticated(user: User = Depends(get_current_user)) -> User:
    return user

# =============================================================================
# 1. TRUCK FLEET REGISTRY
# =============================================================================

@router.get("/api/v1/warehouse/trucks", response_model=List[TruckRegistryResponse])
@router.get("/api/warehouse/trucks", response_model=List[TruckRegistryResponse])
def get_trucks(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """List fleet trucks and drivers with current transit status."""
    return central_ai_service.get_trucks_list(db=db, status=status)

@router.post("/api/v1/warehouse/trucks", response_model=TruckRegistryResponse)
@router.post("/api/warehouse/trucks", response_model=TruckRegistryResponse)
def register_truck(
    req: CreateTruckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_major_warehouse_or_admin)
):
    """Register a new carrier truck and driver to the logistics fleet."""
    return central_ai_service.create_truck(db=db, req=req, user=current_user)

# =============================================================================
# 2. DISPATCH CREATION & MANAGEMENT
# =============================================================================

@router.post("/api/v1/warehouse/dispatch", response_model=DispatchRecordResponse)
@router.post("/api/warehouse/dispatch", response_model=DispatchRecordResponse)
def create_warehouse_dispatch(
    req: CreateDispatchPlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_major_warehouse_or_admin)
):
    """
    POST /api/v1/warehouse/dispatch
    Creates a new dispatch from Major Warehouse to Minor Warehouse.
    - Preserves immutable batch linkage (Batch ID -> Farmer -> Crop -> Grade)
    - Strictly enforces inventory bounds (Sent Qty <= Available Storage Qty)
    - Deducts quantity from Major Warehouse Storage
    - Assigns carrier truck & driver
    """
    return central_ai_service.create_warehouse_dispatch(db=db, req=req, user=current_user)

@router.get("/api/v1/warehouse/dispatches", response_model=DispatchRecordListResponse)
@router.get("/api/warehouse/dispatches", response_model=DispatchRecordListResponse)
def get_warehouse_dispatches(
    batch_id: Optional[str] = None,
    status: Optional[str] = None,
    destination: Optional[str] = None,
    origin: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """List all dispatches with filtering by batch, status, destination, or origin."""
    records = central_ai_service.get_warehouse_dispatches(
        db=db,
        batch_id=batch_id,
        status=status,
        destination=destination,
        origin=origin,
        limit=limit,
        offset=offset
    )
    return {
        "total": len(records),
        "dispatches": records
    }

@router.get("/api/v1/warehouse/dispatch/{dispatch_id}", response_model=DispatchRecordResponse)
@router.get("/api/warehouse/dispatch/{dispatch_id}", response_model=DispatchRecordResponse)
def get_warehouse_dispatch_by_id(
    dispatch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """Retrieve details of a single dispatch record."""
    return central_ai_service.get_warehouse_dispatch_by_id(db=db, dispatch_id_or_pk=dispatch_id)

@router.put("/api/v1/warehouse/dispatch/{dispatch_id}", response_model=DispatchRecordResponse)
@router.put("/api/warehouse/dispatch/{dispatch_id}", response_model=DispatchRecordResponse)
def update_warehouse_dispatch(
    dispatch_id: str,
    req: UpdateDispatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_major_warehouse_or_admin)
):
    """Edit vehicle number, driver details, destination, or schedule before departure."""
    return central_ai_service.update_warehouse_dispatch(db=db, dispatch_id_or_pk=dispatch_id, req=req, user=current_user)

@router.post("/api/v1/warehouse/dispatch/{dispatch_id}/start-transit", response_model=DispatchRecordResponse)
@router.post("/api/warehouse/dispatch/{dispatch_id}/start-transit", response_model=DispatchRecordResponse)
def start_dispatch_transit(
    dispatch_id: str,
    req: Optional[StartDispatchTransitRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_major_warehouse_or_admin)
):
    """
    POST /api/v1/warehouse/dispatch/{dispatch_id}/start-transit
    Transitions dispatch to 'In Transit' and activates live GPS tracking during delivery duty.
    """
    return central_ai_service.start_dispatch_transit(db=db, dispatch_id_or_pk=dispatch_id, req=req, user=current_user)

# =============================================================================
# 3. GPS TRACKING & TELEMETRY
# =============================================================================

@router.post("/api/v1/warehouse/dispatch/{dispatch_id}/gps-location")
@router.post("/api/warehouse/dispatch/{dispatch_id}/gps-location")
def update_dispatch_gps_location(
    dispatch_id: str,
    req: UpdateGPSLocationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """
    POST /api/v1/warehouse/dispatch/{dispatch_id}/gps-location
    Receives live GPS coordinates from mobile device.
    Strict privacy enforcement: GPS tracking is active ONLY during transit duty.
    """
    return central_ai_service.update_dispatch_gps_location(db=db, dispatch_id_or_pk=dispatch_id, req=req, user=current_user)

@router.get("/api/v1/warehouse/dispatch/{dispatch_id}/tracking", response_model=DispatchTrackingResponse)
@router.get("/api/warehouse/dispatch/{dispatch_id}/tracking", response_model=DispatchTrackingResponse)
def get_dispatch_tracking(
    dispatch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated)
):
    """
    GET /api/v1/warehouse/dispatch/{dispatch_id}/tracking
    Returns real-time GPS coordinates, vehicle telemetry, and direct Google Maps deep link.
    """
    return central_ai_service.get_dispatch_tracking(db=db, dispatch_id_or_pk=dispatch_id)

# =============================================================================
# 4. MINOR WAREHOUSE RECEIVING & DISCREPANCY VERIFICATION
# =============================================================================

@router.post("/api/v1/warehouse/dispatch/{dispatch_id}/receive")
@router.post("/api/warehouse/dispatch/{dispatch_id}/receive")
def receive_minor_warehouse_dispatch(
    dispatch_id: str,
    req: ReceiveMinorWarehouseDispatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_minor_warehouse_or_admin)
):
    """
    POST /api/v1/warehouse/dispatch/{dispatch_id}/receive
    Minor Warehouse Receiving & Discrepancy Verification:
    - Calculates difference: sent_quantity_kg - received_quantity_kg
    - If difference != 0: marks status as 'Discrepancy'
    - If difference == 0: marks status as 'Completed'
    - Major Warehouse sent quantity remains untouched
    - Synchronizes with minor_wh_inward_records and minor_wh_stock
    - Stops GPS tracking and releases truck
    """
    return central_ai_service.receive_minor_warehouse_dispatch(db=db, dispatch_id_or_pk=dispatch_id, req=req, user=current_user)

