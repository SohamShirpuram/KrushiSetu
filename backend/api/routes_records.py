from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.user import User
from backend.services.auth_service import get_current_user
from backend.services.audit_service import log_audit_changes, get_record_audit_history
from backend.services.batch_id_generator import generate_batch_id
from backend.ai.engine import ai_engine

# Import all domain models
from backend.models import (
    AuditLog,
    FDCropRequirement,
    FDCrisisRecord,
    FDDemandProjection,
    FDWeatherData,
    FDPSAllocation,
    PanchayatSamiti,
    PSGPRegistry,
    PSSoilSuitability,
    PSGPAllocation,
    GramPanchayat,
    FarmerRegistry,
    FarmerLandRecord,
    SoilTestRecord,
    GPCropAssignment,
    FarmerHarvestRecord,
    FarmerDeliveryRecord,
    FarmerPaymentRecord,
    MajorWarehouseIntake,
    MajorWarehouseDispatch,
    MajorWarehouseStorage,
    MinorWarehouseInward,
    MinorWarehouseStock,
    MinorWarehouseDemand,
    MinorWarehouseDistribution,
    MinorWarehouseRestock,
    BulkBuyerRegistry,
    BulkBuyerEntry,
    AIFarmerRecommendationRecord,
)

router = APIRouter(prefix="/api/records", tags=["Sector Records & Audit Management"])

class GenericEditRequest(BaseModel):
    data: Optional[Dict[str, Any]] = None
    change_reason: Optional[str] = "Operational adjustment"

    class Config:
        extra = "allow"

# ==========================================
# 0. UNIVERSAL AUDIT HISTORY ROUTE
# ==========================================
@router.get("/audit/system/recent")
def get_recent_audit_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves recent cross-sector audit log entries."""
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return {"history": [log.to_dict() for log in logs]}

@router.get("/audit/{table_name}/{record_id}")
def get_audit_history(
    table_name: str,
    record_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves full historical audit trail of all changes made to a record."""
    history = get_record_audit_history(db, table_name, record_id)
    return {"table_name": table_name, "record_id": record_id, "history": history}

# Helper generic handler for standard edits
def handle_record_edit(db: Session, model_cls, table_name: str, record_id: int, req: GenericEditRequest, user: User):
    record = db.query(model_cls).filter(model_cls.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Record {record_id} in {table_name} not found.")
    
    # Support both {data: {...}, change_reason: "..."} and flat {...fields, reason/change_reason: "..."}
    req_dict = req.dict()
    if req.data is not None and isinstance(req.data, dict):
        update_data = req.data
    else:
        update_data = {k: v for k, v in req_dict.items() if k not in ("data", "change_reason", "reason")}
    
    reason = req_dict.get("change_reason") or req_dict.get("reason") or "Operational adjustment"

    log_audit_changes(
        db=db,
        table_name=table_name,
        record_id=record_id,
        old_obj=record,
        new_data=update_data,
        user=user,
        change_reason=reason
    )
    db.commit()
    db.refresh(record)
    return record.to_dict()

# ==========================================
# 1. FOOD DEPARTMENT (AI-FIRST CROP REQUIREMENTS)
# ==========================================
@router.get("/fd/requirements")
def get_fd_requirements(db: Session = Depends(get_db)):
    return [r.to_dict() for r in db.query(FDCropRequirement).order_by(FDCropRequirement.id.desc()).all()]

class GenerateAIRequirementRequest(BaseModel):
    crop_name: Optional[str] = "Sugarcane"
    season: Optional[str] = "Kharif 2026"

@router.post("/fd/generate-ai-recommendation")
def generate_fd_ai_recommendation(
    req: GenerateAIRequirementRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Invokes the ONE CENTRAL AI/ML ENGINE to generate a crop requirement recommendation
    by analyzing cross-sector data (Warehouses, Crisis, Demand Projections, Weather, PS Suitability).
    """
    ai_result = ai_engine.generate_fd_crop_requirement(
        db=db,
        target_crop=req.crop_name,
        season=req.season
    )

    new_req = FDCropRequirement(
        crop_name=ai_result["ai_crop_name"],
        season=ai_result["season"],
        target_quantity_mt=ai_result["ai_recommended_quantity_mt"],
        priority=ai_result["ai_priority"],
        status="AI_GENERATED",
        # Store AI fields immutably
        ai_crop_name=ai_result["ai_crop_name"],
        ai_recommended_quantity_mt=ai_result["ai_recommended_quantity_mt"],
        ai_priority=ai_result["ai_priority"],
        ai_confidence_score=ai_result["ai_confidence_score"],
        ai_rationale=ai_result["ai_rationale"],
        ai_generated_at=ai_result["ai_generated_at"],
        # Initialize human fields
        human_final_quantity_mt=None,
        human_final_priority=None,
        finalized_by=None,
        finalized_at=None,
        notes="Generated by Central AI/ML Engine based on statewide supply chain analysis.",
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)

    return new_req.to_dict()

@router.put("/fd/requirements/{record_id}")
def edit_fd_requirement(
    record_id: int,
    req: GenericEditRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Human Review & Editing of AI Crop Recommendation.
    NEVER overwrites original AI values!
    Updates active values and records changes in AuditLog.
    """
    record = db.query(FDCropRequirement).filter(FDCropRequirement.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Crop Requirement #{record_id} not found.")

    edit_data = req.data.copy()
    
    # Track human edits while preserving original AI recommendation
    if "target_quantity_mt" in edit_data:
        edit_data["human_final_quantity_mt"] = float(edit_data["target_quantity_mt"])
    if "priority" in edit_data:
        edit_data["human_final_priority"] = edit_data["priority"]
    if record.status != "APPROVED":
        edit_data["status"] = "EDITED_BY_HUMAN"

    # Ensure AI recommendation fields cannot be overwritten by manual edits
    for ai_field in ["ai_crop_name", "ai_recommended_quantity_mt", "ai_priority", "ai_rationale", "ai_confidence_score", "ai_generated_at"]:
        edit_data.pop(ai_field, None)

    log_audit_changes(
        db=db,
        table_name="fd_crop_requirements",
        record_id=record_id,
        old_obj=record,
        new_data=edit_data,
        user=user,
        change_reason=req.change_reason or "Food Department human review adjustment"
    )
    db.commit()
    db.refresh(record)
    return record.to_dict()

class ApproveRequirementRequest(BaseModel):
    human_final_quantity_mt: Optional[float] = None
    human_final_priority: Optional[str] = None
    human_review_notes: Optional[str] = "Approved by Food Department Directorate"
    change_reason: Optional[str] = "Final policy approval by Food Directorate"

@router.put("/fd/requirements/{record_id}/approve")
def approve_fd_requirement(
    record_id: int,
    req: ApproveRequirementRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Final approval of the crop requirement by Food Department.
    Stamps finalized_by and finalized_at and transitions status to APPROVED.
    """
    record = db.query(FDCropRequirement).filter(FDCropRequirement.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Crop Requirement #{record_id} not found.")

    final_qty = req.human_final_quantity_mt if req.human_final_quantity_mt is not None else record.target_quantity_mt
    final_priority = req.human_final_priority if req.human_final_priority is not None else record.priority

    new_data = {
        "target_quantity_mt": final_qty,
        "priority": final_priority,
        "human_final_quantity_mt": final_qty,
        "human_final_priority": final_priority,
        "finalized_by": user.username,
        "finalized_at": datetime.utcnow(),
        "human_review_notes": req.human_review_notes,
        "status": "APPROVED",
    }

    log_audit_changes(
        db=db,
        table_name="fd_crop_requirements",
        record_id=record_id,
        old_obj=record,
        new_data=new_data,
        user=user,
        change_reason=req.change_reason or "Food Department final approval"
    )
    db.commit()
    db.refresh(record)
    return record.to_dict()

class AssignToPSRequest(BaseModel):
    panchayat_samiti_name: str
    target_quota_mt: float
    notes: Optional[str] = None

@router.post("/fd/requirements/{record_id}/assign-ps")
def assign_fd_requirement_to_ps(
    record_id: int,
    req: AssignToPSRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Assigns an approved crop requirement to a Panchayat Samiti.
    Creates an FDPSAllocation record in the database.
    """
    record = db.query(FDCropRequirement).filter(FDCropRequirement.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Crop Requirement #{record_id} not found.")

    allocation = FDPSAllocation(
        panchayat_samiti_name=req.panchayat_samiti_name,
        crop_name=record.crop_name,
        target_quota_mt=req.target_quota_mt,
        ai_suggested_quota_mt=record.ai_recommended_quantity_mt,
        human_final_quota_mt=req.target_quota_mt,
        ai_rationale=record.ai_rationale or "Derived from Central AI Food Department recommendation.",
        review_status="CONFIRMED",
        status="ASSIGNED",
    )
    db.add(allocation)
    db.commit()
    db.refresh(allocation)

    return allocation.to_dict()

@router.get("/fd/crisis")
def get_fd_crisis(db: Session = Depends(get_db)):
    return [r.to_dict() for r in db.query(FDCrisisRecord).order_by(FDCrisisRecord.id.desc()).all()]

@router.post("/fd/crisis")
def create_fd_crisis(data: Dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rec = FDCrisisRecord(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()

@router.put("/fd/crisis/{record_id}")
def edit_fd_crisis(record_id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, FDCrisisRecord, "fd_crisis_records", record_id, req, user)

@router.get("/fd/demand")
def get_fd_demand(db: Session = Depends(get_db)):
    return [r.to_dict() for r in db.query(FDDemandProjection).order_by(FDDemandProjection.id.desc()).all()]

@router.post("/fd/demand")
def create_fd_demand(data: Dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rec = FDDemandProjection(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()

@router.put("/fd/demand/{record_id}")
def edit_fd_demand(record_id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, FDDemandProjection, "fd_demand_projections", record_id, req, user)

@router.get("/fd/weather")
def get_fd_weather(db: Session = Depends(get_db)):
    return [r.to_dict() for r in db.query(FDWeatherData).order_by(FDWeatherData.id.desc()).all()]

@router.post("/fd/weather")
def create_fd_weather(data: Dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rec = FDWeatherData(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()

@router.put("/fd/weather/{record_id}")
def edit_fd_weather(record_id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, FDWeatherData, "fd_weather_data", record_id, req, user)

@router.get("/fd/ps-allocations")
def get_fd_ps_allocations(db: Session = Depends(get_db)):
    return [r.to_dict() for r in db.query(FDPSAllocation).order_by(FDPSAllocation.id.desc()).all()]

@router.post("/fd/ps-allocations")
def create_fd_ps_allocation(data: Dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rec = FDPSAllocation(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()

@router.put("/fd/ps-allocations/{record_id}")
def edit_fd_ps_allocation(record_id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, FDPSAllocation, "fd_ps_allocations", record_id, req, user)

# ==========================================
# 2. PANCHAYAT SAMITI
# ==========================================
@router.get("/ps/gps")
def get_ps_gps(db: Session = Depends(get_db)):
    return [r.to_dict() for r in db.query(PSGPRegistry).order_by(PSGPRegistry.id.desc()).all()]

@router.post("/ps/gps")
def create_ps_gp(data: Dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rec = PSGPRegistry(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()

@router.put("/ps/gps/{record_id}")
def edit_ps_gp(record_id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, PSGPRegistry, "ps_gp_registry", record_id, req, user)

@router.get("/ps/soil-suitability")
def get_ps_soil_suitability(db: Session = Depends(get_db)):
    return [r.to_dict() for r in db.query(PSSoilSuitability).order_by(PSSoilSuitability.id.desc()).all()]

@router.post("/ps/soil-suitability")
def create_ps_soil_suitability(data: Dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rec = PSSoilSuitability(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()

@router.put("/ps/soil-suitability/{record_id}")
def edit_ps_soil_suitability(record_id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, PSSoilSuitability, "ps_soil_suitability", record_id, req, user)

@router.get("/ps/gp-allocations")
def get_ps_gp_allocations(db: Session = Depends(get_db)):
    return [r.to_dict() for r in db.query(PSGPAllocation).order_by(PSGPAllocation.id.desc()).all()]

@router.post("/ps/gp-allocations")
def create_ps_gp_allocation(data: Dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rec = PSGPAllocation(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()

@router.put("/ps/gp-allocations/{record_id}")
def edit_ps_gp_allocation(record_id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, PSGPAllocation, "ps_gp_allocations", record_id, req, user)

class GeneratePSAIAllocationRequest(BaseModel):
    panchayat_samiti_name: Optional[str] = "Baramati Block Panchayat Samiti"
    crop_name: Optional[str] = "Wheat (Lokwan)"
    total_quota_mt: Optional[float] = 12000.0
    season: Optional[str] = "Rabi 2026"

@router.post("/ps/generate-ai-allocation")
def generate_ps_ai_allocation(
    req: GeneratePSAIAllocationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Runs Central AI to optimize block quota distribution to Gram Panchayats."""
    ai_recs = ai_engine.generate_ps_gp_allocations(
        db=db,
        ps_name=req.panchayat_samiti_name,
        crop_name=req.crop_name,
        total_quota_mt=req.total_quota_mt,
        season=req.season
    )
    created_records = []
    for r in ai_recs:
        alloc = PSGPAllocation(
            panchayat_samiti_name=r["panchayat_samiti_name"],
            gp_name=r["gp_name"],
            crop_name=r["crop_name"],
            allocated_quantity_mt=r["ai_recommended_quantity_mt"],
            season=r["season"],
            status="AI_GENERATED",
            ai_recommended_quantity_mt=r["ai_recommended_quantity_mt"],
            ai_rationale=r["ai_rationale"],
            ai_confidence_score=r["ai_confidence_score"],
        )
        db.add(alloc)
        created_records.append(alloc)
    db.commit()
    for c in created_records:
        db.refresh(c)
    return [c.to_dict() for c in created_records]

class ApprovePSAllocationRequest(BaseModel):
    human_final_quantity_mt: Optional[float] = None
    change_reason: Optional[str] = "Panchayat Samiti final approval"

@router.put("/ps/gp-allocations/{record_id}/approve")
def approve_ps_gp_allocation(
    record_id: int,
    req: ApprovePSAllocationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    rec = db.query(PSGPAllocation).filter(PSGPAllocation.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="GP Allocation not found")
    
    final_qty = req.human_final_quantity_mt if req.human_final_quantity_mt is not None else rec.allocated_quantity_mt
    new_data = {
        "allocated_quantity_mt": final_qty,
        "human_final_quantity_mt": final_qty,
        "finalized_by": user.username,
        "finalized_at": datetime.utcnow(),
        "status": "APPROVED",
    }
    log_audit_changes(db, "ps_gp_allocations", record_id, rec, new_data, user, req.change_reason)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()

# ==========================================
# 3. GRAM PANCHAYAT
# ==========================================
@router.get("/gp/land-records")
def get_gp_land_records(farmer_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(FarmerLandRecord)
    if farmer_id:
        q = q.filter(FarmerLandRecord.farmer_id == farmer_id)
    return [r.to_dict() for r in q.order_by(FarmerLandRecord.id.desc()).all()]

@router.post("/gp/land-records")
def create_gp_land_record(data: Dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rec = FarmerLandRecord(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()

@router.put("/gp/land-records/{record_id}")
def edit_gp_land_record(record_id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, FarmerLandRecord, "gp_farmer_land_records", record_id, req, user)

@router.get("/gp/soil-tests")
def get_gp_soil_tests(farmer_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(SoilTestRecord)
    if farmer_id:
        q = q.filter(SoilTestRecord.farmer_id == farmer_id)
    return [r.to_dict() for r in q.order_by(SoilTestRecord.id.desc()).all()]

@router.post("/gp/soil-tests")
def create_gp_soil_test(data: Dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rec = SoilTestRecord(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()

@router.put("/gp/soil-tests/{record_id}")
def edit_gp_soil_test(record_id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, SoilTestRecord, "gp_soil_tests", record_id, req, user)

@router.get("/gp/crop-assignments")
def get_gp_crop_assignments(farmer_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(GPCropAssignment)
    if farmer_id:
        q = q.filter(GPCropAssignment.farmer_id == farmer_id)
    return [r.to_dict() for r in q.order_by(GPCropAssignment.id.desc()).all()]

@router.post("/gp/crop-assignments")
def create_gp_crop_assignment(data: Dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rec = GPCropAssignment(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()

@router.put("/gp/crop-assignments/{record_id}")
def edit_gp_crop_assignment(record_id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, GPCropAssignment, "gp_crop_assignments", record_id, req, user)

class GenerateGPAIAssignmentRequest(BaseModel):
    gp_name: Optional[str] = "Shirsuphal Gram Panchayat"
    crop_name: Optional[str] = "Wheat (Lokwan)"
    total_gp_quota_mt: Optional[float] = 120.0
    season: Optional[str] = "Rabi 2026"

@router.post("/gp/generate-ai-assignment")
def generate_gp_ai_assignment(
    req: GenerateGPAIAssignmentRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Runs Central AI to match GP quota to individual farmers based on soil & land records."""
    ai_recs = ai_engine.generate_gp_farmer_allocations(
        db=db,
        gp_name=req.gp_name,
        crop_name=req.crop_name,
        total_gp_quota_mt=req.total_gp_quota_mt,
        season=req.season
    )
    created = []
    for r in ai_recs:
        assign = GPCropAssignment(
            farmer_id=r["farmer_id"],
            farmer_name=r["farmer_name"],
            crop_name=r["crop_name"],
            season=r["season"],
            assigned_acres=r["ai_recommended_acres"],
            required_quantity_quintals=r["ai_recommended_quintals"],
            status="AI_GENERATED",
            ai_recommended_acres=r["ai_recommended_acres"],
            ai_recommended_quintals=r["ai_recommended_quintals"],
            ai_rationale=r["ai_rationale"],
            ai_confidence_score=r["ai_confidence_score"],
        )
        db.add(assign)
        created.append(assign)
    db.commit()
    for c in created:
        db.refresh(c)
    return [c.to_dict() for c in created]

class ApproveGPAssignmentRequest(BaseModel):
    human_final_acres: Optional[float] = None
    human_final_quintals: Optional[float] = None
    change_reason: Optional[str] = "Gram Panchayat committee approval"

@router.put("/gp/crop-assignments/{record_id}/approve")
def approve_gp_crop_assignment(
    record_id: int,
    req: ApproveGPAssignmentRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    rec = db.query(GPCropAssignment).filter(GPCropAssignment.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Crop assignment not found")
    
    final_acres = req.human_final_acres if req.human_final_acres is not None else rec.assigned_acres
    final_qtl = req.human_final_quintals if req.human_final_quintals is not None else rec.required_quantity_quintals
    
    new_data = {
        "assigned_acres": final_acres,
        "required_quantity_quintals": final_qtl,
        "human_final_acres": final_acres,
        "human_final_quintals": final_qtl,
        "finalized_by": user.username,
        "finalized_at": datetime.utcnow(),
        "status": "APPROVED",
    }
    log_audit_changes(db, "gp_crop_assignments", record_id, rec, new_data, user, req.change_reason)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()

# ==========================================
# 4. FARMER
# ==========================================
@router.get("/farmer/harvests")
def get_farmer_harvests(farmer_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(FarmerHarvestRecord)
    if farmer_id:
        q = q.filter(FarmerHarvestRecord.farmer_id == farmer_id)
    return [r.to_dict() for r in q.order_by(FarmerHarvestRecord.id.desc()).all()]

@router.post("/farmer/harvests")
def create_farmer_harvest(data: Dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rec = FarmerHarvestRecord(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()

@router.put("/farmer/harvests/{record_id}")
def edit_farmer_harvest(record_id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, FarmerHarvestRecord, "farmer_harvest_records", record_id, req, user)

@router.get("/farmer/deliveries")
def get_farmer_deliveries(farmer_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(FarmerDeliveryRecord)
    if farmer_id:
        q = q.filter(FarmerDeliveryRecord.farmer_id == farmer_id)
    return [r.to_dict() for r in q.order_by(FarmerDeliveryRecord.id.desc()).all()]

@router.post("/farmer/deliveries")
def create_farmer_delivery(data: Dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rec = FarmerDeliveryRecord(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()

@router.put("/farmer/deliveries/{record_id}")
def edit_farmer_delivery(record_id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, FarmerDeliveryRecord, "farmer_delivery_records", record_id, req, user)

@router.get("/farmer/payments")
def get_farmer_payments(farmer_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(FarmerPaymentRecord)
    if farmer_id:
        q = q.filter(FarmerPaymentRecord.farmer_id == farmer_id)
    return [r.to_dict() for r in q.order_by(FarmerPaymentRecord.id.desc()).all()]

@router.post("/farmer/payments")
def create_farmer_payment(data: Dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rec = FarmerPaymentRecord(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()

@router.put("/farmer/payments/{record_id}")
def edit_farmer_payment(record_id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, FarmerPaymentRecord, "farmer_payment_records", record_id, req, user)

@router.get("/farmer/crop-recommendation")
def get_farmer_ai_recommendation(
    farmer_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    f_id = farmer_id or user.farmer_id or "KS-FMR-1001"
    return ai_engine.generate_farmer_crop_recommendation(db=db, farmer_id=f_id)

@router.get("/farmer/profile-card")
def get_farmer_profile_card(
    farmer_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    f_id = farmer_id or user.farmer_id or "KS-FMR-1001"
    land = db.query(FarmerLandRecord).filter(FarmerLandRecord.farmer_id == f_id).first()
    soil = db.query(SoilTestRecord).filter(SoilTestRecord.farmer_id == f_id).first()
    assigns = db.query(GPCropAssignment).filter(GPCropAssignment.farmer_id == f_id).all()
    deliveries = db.query(FarmerDeliveryRecord).filter(FarmerDeliveryRecord.farmer_id == f_id).all()
    payments = db.query(FarmerPaymentRecord).filter(FarmerPaymentRecord.farmer_id == f_id).all()
    
    return {
        "farmer_id": f_id,
        "full_name": user.full_name if (user.farmer_id == f_id or user.role.value == "FARMER") else (land.farmer_name if land else "Ramesh Narayan Patil"),
        "jurisdiction": user.jurisdiction_or_location if (user.farmer_id == f_id or user.role.value == "FARMER") else (land.village_name if land else "Shirsuphal Village, Baramati"),
        "land_record": land.to_dict() if land else None,
        "soil_test": soil.to_dict() if soil else None,
        "assigned_crops_count": len(assigns),
        "total_deliveries_count": len(deliveries),
        "total_payments_settled": sum(p.total_amount for p in payments),
        "qr_code_payload": f"KRUSHISETU-VERIFIED-FARMER:{f_id}",
    }

@router.get("/farmer/complete-history")
def get_farmer_complete_history(
    farmer_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    f_id = farmer_id or user.farmer_id or "KS-FMR-1001"
    ai_recs = [dict(**r.to_dict(), event_type="AI_CROP_RECOMMENDED") for r in db.query(AIFarmerRecommendationRecord).filter(AIFarmerRecommendationRecord.farmer_id == f_id).all()]
    assigns = [dict(**a.to_dict(), event_type="CROP_ASSIGNED") for a in db.query(GPCropAssignment).filter(GPCropAssignment.farmer_id == f_id).all()]
    harvests = [dict(**h.to_dict(), event_type="HARVEST_LOGGED") for h in db.query(FarmerHarvestRecord).filter(FarmerHarvestRecord.farmer_id == f_id).all()]
    deliveries = [dict(**d.to_dict(), event_type="WAREHOUSE_DELIVERY") for d in db.query(FarmerDeliveryRecord).filter(FarmerDeliveryRecord.farmer_id == f_id).all()]
    intakes = [dict(**i.to_dict(), event_type="QUALITY_GRADED") for i in db.query(MajorWarehouseIntake).filter(MajorWarehouseIntake.farmer_id == f_id).all()]
    payments = [dict(**p.to_dict(), event_type="PAYMENT_SETTLED") for p in db.query(FarmerPaymentRecord).filter(FarmerPaymentRecord.farmer_id == f_id).all()]
    
    events = ai_recs + assigns + harvests + deliveries + intakes + payments
    events.sort(key=lambda x: str(x.get("created_at") or ""), reverse=True)
    return {"farmer_id": f_id, "events": events}

# ==========================================
# 5. MAJOR WAREHOUSE (DUAL GRADING & INTAKE)
# ==========================================
@router.get("/major-wh/intakes")
def get_major_wh_intakes(batch_id: Optional[str] = None, farmer_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(MajorWarehouseIntake)
    if batch_id:
        q = q.filter(MajorWarehouseIntake.batch_id == batch_id)
    if farmer_id:
        q = q.filter(MajorWarehouseIntake.farmer_id == farmer_id)
    return [r.to_dict() for r in q.order_by(MajorWarehouseIntake.id.desc()).all()]

@router.post("/major-wh/intakes")
def create_major_wh_intake(data: Dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Auto-assign unique Batch ID if not provided
    if not data.get("batch_id"):
        data["batch_id"] = generate_batch_id(db)

    # If net weight not computed, compute from gross - tare
    if not data.get("net_weight_kg") and data.get("gross_weight_kg") and data.get("tare_weight_kg"):
        data["net_weight_kg"] = float(data["gross_weight_kg"]) - float(data["tare_weight_kg"])

    # Initial AI Prediction Placeholder (e.g. Score=86, Grade=A)
    if "ai_predicted_score" not in data:
        data["ai_predicted_score"] = 86.0
    if "ai_predicted_grade" not in data:
        data["ai_predicted_grade"] = "A"

    rec = MajorWarehouseIntake(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()

@router.put("/major-wh/intakes/{record_id}")
def edit_major_wh_intake(record_id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, MajorWarehouseIntake, "major_warehouse_intakes", record_id, req, user)

class DualGradingReviewRequest(BaseModel):
    human_final_score: float
    human_final_grade: str # "A", "B", "C", "REJECTED"
    grading_notes: Optional[str] = None
    change_reason: Optional[str] = "Human inspector quality review"

@router.put("/major-wh/intakes/{record_id}/grade")
def review_and_confirm_grade(
    record_id: int,
    req: DualGradingReviewRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Core Requirement:
    AI will only PREDICT the quality/grade.
    Human warehouse staff can review AI prediction, edit score, change grade, and confirm final grade.
    Example: AI (Score: 86, Grade: A) -> Human changes to (Score: 78, Grade: B) -> Final is (Score: 78, Grade: B).
    BOTH the AI prediction and human final results are stored.
    """
    intake = db.query(MajorWarehouseIntake).filter(MajorWarehouseIntake.id == record_id).first()
    if not intake:
        raise HTTPException(status_code=404, detail="Intake record not found.")

    new_data = {
        "human_final_score": req.human_final_score,
        "human_final_grade": req.human_final_grade,
        "grading_notes": req.grading_notes or intake.grading_notes,
        "review_status": "CONFIRMED",
        "reviewed_by": user.username,
        "reviewed_at": datetime.utcnow(),
    }

    log_audit_changes(
        db=db,
        table_name="major_warehouse_intakes",
        record_id=record_id,
        old_obj=intake,
        new_data=new_data,
        user=user,
        change_reason=req.change_reason or "Human quality grading confirmation"
    )

    db.commit()
    db.refresh(intake)
    return intake.to_dict()

@router.get("/major-wh/dispatches")
def get_major_wh_dispatches(db: Session = Depends(get_db)):
    return [r.to_dict() for r in db.query(MajorWarehouseDispatch).order_by(MajorWarehouseDispatch.id.desc()).all()]

@router.post("/major-wh/dispatches")
def create_major_wh_dispatch(data: Dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not data.get("dispatch_id"):
        data["dispatch_id"] = f"KS-DSP-{datetime.utcnow().strftime('%M%S')}"
    rec = MajorWarehouseDispatch(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()

@router.put("/major-wh/dispatches/{record_id}")
def edit_major_wh_dispatch(record_id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, MajorWarehouseDispatch, "major_warehouse_dispatches", record_id, req, user)

class GenerateAIGradeRequest(BaseModel):
    batch_id: str
    crop_name: str
    moisture_pct: Optional[float] = 11.4
    foreign_matter_pct: Optional[float] = 1.2
    broken_grains_pct: Optional[float] = 1.8

@router.post("/major-wh/generate-ai-grade")
def generate_major_wh_ai_grade(
    req: GenerateAIGradeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Runs Central AI computer vision & sensory grain quality grading."""
    res = ai_engine.generate_major_wh_quality_grade(
        db=db,
        batch_id=req.batch_id,
        crop_name=req.crop_name,
        sample_metrics={
            "moisture_pct": req.moisture_pct,
            "foreign_matter_pct": req.foreign_matter_pct,
            "broken_grains_pct": req.broken_grains_pct,
        }
    )
    # Update intake record if batch exists
    intake = db.query(MajorWarehouseIntake).filter(MajorWarehouseIntake.batch_id == req.batch_id).first()
    if intake:
        intake.ai_predicted_score = res["ai_predicted_score"]
        intake.ai_predicted_grade = res["ai_predicted_grade"]
        intake.review_status = "AI_GENERATED"
        db.commit()
        db.refresh(intake)
        return intake.to_dict()
    return res

# ==========================================
# 6. MINOR WAREHOUSE
# ==========================================
@router.get("/minor-wh/inward")
def get_minor_wh_inward(db: Session = Depends(get_db)):
    return [r.to_dict() for r in db.query(MinorWarehouseInward).order_by(MinorWarehouseInward.id.desc()).all()]

@router.post("/minor-wh/inward")
def create_minor_wh_inward(data: Dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rec = MinorWarehouseInward(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()

@router.put("/minor-wh/inward/{record_id}")
def edit_minor_wh_inward(record_id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, MinorWarehouseInward, "minor_wh_inward_records", record_id, req, user)

@router.get("/minor-wh/stock")
def get_minor_wh_stock(db: Session = Depends(get_db)):
    return [r.to_dict() for r in db.query(MinorWarehouseStock).order_by(MinorWarehouseStock.id.desc()).all()]

@router.post("/minor-wh/stock")
def create_minor_wh_stock(data: Dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rec = MinorWarehouseStock(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()

@router.put("/minor-wh/stock/{record_id}")
def edit_minor_wh_stock(record_id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, MinorWarehouseStock, "minor_wh_stock", record_id, req, user)

@router.get("/minor-wh/demand")
def get_minor_wh_demand(db: Session = Depends(get_db)):
    return [r.to_dict() for r in db.query(MinorWarehouseDemand).order_by(MinorWarehouseDemand.id.desc()).all()]

@router.post("/minor-wh/demand")
def create_minor_wh_demand(data: Dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rec = MinorWarehouseDemand(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()

@router.put("/minor-wh/demand/{record_id}")
def edit_minor_wh_demand(record_id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, MinorWarehouseDemand, "minor_wh_regional_demand", record_id, req, user)

@router.get("/minor-wh/distributions")
def get_minor_wh_distributions(db: Session = Depends(get_db)):
    return [r.to_dict() for r in db.query(MinorWarehouseDistribution).order_by(MinorWarehouseDistribution.id.desc()).all()]

@router.post("/minor-wh/distributions")
def create_minor_wh_distribution(data: Dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rec = MinorWarehouseDistribution(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()

@router.put("/minor-wh/distributions/{record_id}")
def edit_minor_wh_distribution(record_id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, MinorWarehouseDistribution, "minor_wh_distributions", record_id, req, user)

@router.get("/minor-wh/restock")
def get_minor_wh_restock(db: Session = Depends(get_db)):
    return [r.to_dict() for r in db.query(MinorWarehouseRestock).order_by(MinorWarehouseRestock.id.desc()).all()]

@router.post("/minor-wh/restock")
def create_minor_wh_restock(data: Dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rec = MinorWarehouseRestock(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()

@router.put("/minor-wh/restock/{record_id}")
def edit_minor_wh_restock(record_id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, MinorWarehouseRestock, "minor_wh_restock_requests", record_id, req, user)

# ==========================================
# 7. BULK BUYER
# ==========================================
@router.get("/buyer/registry")
def get_buyer_registry(buyer_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(BulkBuyerRegistry)
    if buyer_id:
        q = q.filter(BulkBuyerRegistry.buyer_id == buyer_id)
    return [r.to_dict() for r in q.order_by(BulkBuyerRegistry.id.desc()).all()]

@router.post("/buyer/registry")
def create_buyer_registry(data: Dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rec = BulkBuyerRegistry(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()

@router.put("/buyer/registry/{record_id}")
def edit_buyer_registry(record_id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, BulkBuyerRegistry, "bulk_buyer_registry", record_id, req, user)

@router.get("/buyer/entries")
def get_buyer_entries(buyer_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(BulkBuyerEntry)
    if buyer_id:
        q = q.filter(BulkBuyerEntry.buyer_id == buyer_id)
    return [r.to_dict() for r in q.order_by(BulkBuyerEntry.id.desc()).all()]

@router.post("/buyer/entries")
def create_buyer_entry(data: Dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rec = BulkBuyerEntry(**data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec.to_dict()

@router.put("/buyer/entries/{record_id}")
def edit_buyer_entry(record_id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, BulkBuyerEntry, "bulk_buyer_entries", record_id, req, user)

class CreateBuyerIdRequest(BaseModel):
    company_name: str
    business_type: str
    gst_number: Optional[str] = None
    contact_person: str
    contact_phone: str
    official_email: str

@router.post("/buyer/create-id")
def create_buyer_id(
    req: CreateBuyerIdRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    count = db.query(BulkBuyerRegistry).count() + 1
    new_buyer_id = f"KS-BYR-{5000 + count}"
    
    registry = BulkBuyerRegistry(
        buyer_id=new_buyer_id,
        company_name=req.company_name,
        business_type=req.business_type,
        gst_number=req.gst_number,
        contact_person=req.contact_person,
        contact_phone=req.contact_phone,
        official_email=req.official_email,
        status="VERIFIED_BUYER",
    )
    db.add(registry)
    if user.role.value == "BULK_BUYER" and not user.buyer_id:
        user.buyer_id = new_buyer_id
    db.commit()
    db.refresh(registry)
    return registry.to_dict()

# ==========================================
# 8. MINOR WAREHOUSE AI RECOMMENDATIONS
# ==========================================
@router.get("/minor-wh/ai-recommendations")
def get_minor_wh_ai_recommendations(
    location: Optional[str] = "Baramati APMC Godown No. 3",
    crop_name: Optional[str] = "Wheat (Lokwan)",
    db: Session = Depends(get_db)
):
    return ai_engine.generate_minor_wh_stock_recommendations(
        db=db,
        warehouse_location=location,
        crop_name=crop_name
    )

# ==========================================
# 9. TRUCK GPS TRACKING (MAJOR WH, MINOR WH, FOOD DEPT)
# ==========================================
@router.get("/tracking/trucks")
def get_live_truck_tracking(db: Session = Depends(get_db)):
    """Returns active dispatch truck shipments with live GPS and Google Maps link."""
    dispatches = db.query(MajorWarehouseDispatch).order_by(MajorWarehouseDispatch.id.desc()).all()
    results = []
    for d in dispatches:
        item = d.to_dict()
        lat = d.latitude or 18.3512
        lng = d.longitude or 74.1205
        item["google_maps_url"] = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
        results.append(item)
    return results

class UpdateTruckGPSRequest(BaseModel):
    current_location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

@router.put("/tracking/trucks/{dispatch_id}/update-gps")
def update_truck_gps(
    dispatch_id: str,
    req: UpdateTruckGPSRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    disp = db.query(MajorWarehouseDispatch).filter(MajorWarehouseDispatch.dispatch_id == dispatch_id).first()
    if not disp:
        raise HTTPException(status_code=404, detail="Dispatch truck not found")
    disp.current_location = req.current_location
    disp.last_gps_update = datetime.utcnow()
    if req.latitude: disp.latitude = req.latitude
    if req.longitude: disp.longitude = req.longitude
    db.commit()
    db.refresh(disp)
    return disp.to_dict()

@router.put("/tracking/trucks/{dispatch_id}/complete")
def complete_truck_delivery(
    dispatch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    disp = db.query(MajorWarehouseDispatch).filter(MajorWarehouseDispatch.dispatch_id == dispatch_id).first()
    if not disp:
        raise HTTPException(status_code=404, detail="Dispatch truck not found")
    disp.delivery_status = "COMPLETED"
    disp.status = "RECEIVED_AT_DESTINATION"
    disp.current_location = f"Delivered to {disp.destination_minor_warehouse}"
    disp.last_gps_update = datetime.utcnow()
    db.commit()
    db.refresh(disp)
    return disp.to_dict()

# ==========================================
# 10. CENTRAL AI DATA FEEDBACK LOOP & FD INSIGHTS
# ==========================================
@router.get("/ai/feedback-loop")
def get_ai_feedback_loop(db: Session = Depends(get_db)):
    return ai_engine.get_feedback_loop_analytics(db=db)

@router.get("/fd/ai-data-insights")
def get_fd_ai_data_insights(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return ai_engine.get_fd_ai_data_insights(db=db)

# ==========================================
# 11. PANCHAYAT SAMITI — GP REGISTRY (JURISDICTION ENFORCED)
# ==========================================
class RegisterGPRequest(BaseModel):
    gp_name: str
    gp_code: Optional[str] = None
    district: Optional[str] = "Pune"
    panchayat_samiti_name: Optional[str] = None
    village_location: Optional[str] = None
    total_area_hectares: float
    cultivable_area_hectares: float
    active_farmers_count: Optional[int] = 0
    sarpanch_name: Optional[str] = None
    office_phone: Optional[str] = None

@router.get("/ps/gps")
def list_ps_gps(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(PSGPRegistry)
    role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_str == "PANCHAYAT_SAMITI":
        ps_name = "Baramati Block Panchayat Samiti"
        if current_user.jurisdiction_or_location and "Baramati" in current_user.jurisdiction_or_location:
            ps_name = "Baramati Block Panchayat Samiti"
        query = query.filter(PSGPRegistry.panchayat_samiti_name == ps_name)
    records = query.order_by(PSGPRegistry.id.desc()).all()
    return [r.to_dict() for r in records]

@router.post("/ps/gps")
def register_gp(req: RegisterGPRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    target_ps = req.panchayat_samiti_name or "Baramati Block Panchayat Samiti"
    if role_str == "PANCHAYAT_SAMITI":
        target_ps = "Baramati Block Panchayat Samiti"

    cnt = db.query(PSGPRegistry).count() + 1
    code = req.gp_code or f"GP-BMT-{cnt + 10:02d}"

    new_gp = PSGPRegistry(
        gp_code=code,
        gp_name=req.gp_name,
        panchayat_samiti_name=target_ps,
        district=req.district or "Pune",
        village_location=req.village_location or req.gp_name,
        total_area_hectares=req.total_area_hectares,
        cultivable_area_hectares=req.cultivable_area_hectares,
        active_farmers_count=req.active_farmers_count or 0,
        sarpanch_name=req.sarpanch_name or "Appointed Sarpanch",
        office_phone=req.office_phone or "+91 2112 255100",
    )
    db.add(new_gp)
    db.commit()
    db.refresh(new_gp)

    db.add(AuditLog(
        table_name="ps_gp_registry",
        record_id=str(new_gp.id),
        field_name="gp_code",
        old_value="",
        new_value=code,
        edited_by=current_user.username,
        edited_by_role=role_str,
        change_reason=f"Panchayat Samiti official registration of new Gram Panchayat {new_gp.gp_name}",
    ))
    db.commit()
    return new_gp.to_dict()

@router.put("/ps/gps/{id}")
def edit_ps_gp(id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, PSGPRegistry, "ps_gp_registry", id, req, user)

# ==========================================
# 12. GRAM PANCHAYAT — FARMER REGISTRY & SOIL REPORT
# ==========================================
class RegisterFarmerRequest(BaseModel):
    farmer_name: str
    contact_phone: Optional[str] = None
    aadhaar_masked: Optional[str] = "XXXX-XXXX-8921"
    gp_name: Optional[str] = None
    village_name: Optional[str] = None
    total_land_acres: float
    survey_number: str
    soil_type: Optional[str] = "Medium Deep Black Cotton Soil"
    irrigation_source: Optional[str] = "CANAL"
    ph_level: Optional[float] = 7.3
    nitrogen_kg_ha: Optional[float] = 260.0
    phosphorus_kg_ha: Optional[float] = 38.0
    potassium_kg_ha: Optional[float] = 290.0
    organic_carbon_pct: Optional[float] = 0.68
    soil_test_doc_url: Optional[str] = "/uploads/soil_reports/soil_health_card_KS-FMR-1001.svg"

@router.get("/gp/farmers")
def list_gp_farmers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(FarmerRegistry)
    role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_str == "GRAM_PANCHAYAT":
        gp_name = "Shirsuphal Gram Panchayat"
        if current_user.jurisdiction_or_location and "Shirsuphal" in current_user.jurisdiction_or_location:
            gp_name = "Shirsuphal Gram Panchayat"
        query = query.filter(FarmerRegistry.gp_name == gp_name)
    records = query.order_by(FarmerRegistry.id.desc()).all()
    return [r.to_dict() for r in records]

@router.post("/gp/farmers")
def register_farmer(req: RegisterFarmerRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    target_gp = req.gp_name or "Shirsuphal Gram Panchayat"
    if role_str == "GRAM_PANCHAYAT":
        target_gp = "Shirsuphal Gram Panchayat"

    count = db.query(FarmerRegistry).count() + 1
    new_farmer_id = f"KS-FMR-{1000 + count}"

    # 1. Farmer Master Record
    new_farmer = FarmerRegistry(
        farmer_id=new_farmer_id,
        farmer_name=req.farmer_name,
        contact_phone=req.contact_phone or "+91 98220 12345",
        aadhaar_masked=req.aadhaar_masked or "XXXX-XXXX-8921",
        gp_name=target_gp,
        panchayat_samiti_name="Baramati Block Panchayat Samiti",
        district="Pune",
        village_name=req.village_name or "Shirsuphal",
        total_land_acres=req.total_land_acres,
        bank_account_masked="SBIN000XXXX4412",
        soil_health_card_no=f"SHC-MH-BMT-{new_farmer_id[-4:]}",
    )
    db.add(new_farmer)

    # 2. Land Record
    land = FarmerLandRecord(
        farmer_id=new_farmer_id,
        farmer_name=req.farmer_name,
        survey_number=req.survey_number,
        village_name=req.village_name or "Shirsuphal",
        land_area_acres=req.total_land_acres,
        soil_type=req.soil_type or "Medium Deep Black Cotton Soil",
        irrigation_source=req.irrigation_source or "CANAL",
    )
    db.add(land)

    # 3. Soil Test Record
    doc_path = req.soil_test_doc_url or "/uploads/soil_reports/soil_health_card_KS-FMR-1001.svg"
    soil = SoilTestRecord(
        farmer_id=new_farmer_id,
        survey_number=req.survey_number,
        sample_date=datetime.utcnow().strftime("%Y-%m-%d"),
        ph_level=req.ph_level or 7.3,
        nitrogen_kg_ha=req.nitrogen_kg_ha or 260.0,
        phosphorus_kg_ha=req.phosphorus_kg_ha or 38.0,
        potassium_kg_ha=req.potassium_kg_ha or 290.0,
        organic_carbon_pct=req.organic_carbon_pct or 0.68,
        soil_test_doc_url=doc_path,
        testing_lab="Baramati Agricultural Research Center",
    )
    db.add(soil)
    db.commit()
    db.refresh(new_farmer)

    db.add(AuditLog(
        table_name="gp_farmer_registry",
        record_id=str(new_farmer.id),
        field_name="farmer_id",
        old_value="",
        new_value=new_farmer_id,
        edited_by=current_user.username,
        edited_by_role=role_str,
        change_reason=f"Gram Panchayat registration of farmer {new_farmer.farmer_name} with certified soil report",
    ))
    db.commit()
    return new_farmer.to_dict()

@router.put("/gp/farmers/{id}")
def edit_gp_farmer(id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, FarmerRegistry, "gp_farmer_registry", id, req, user)

class UploadSoilDocRequest(BaseModel):
    farmer_id: str
    file_name: Optional[str] = "soil_health_card.jpg"
    doc_url: Optional[str] = None

@router.post("/gp/upload-soil-report")
def upload_soil_report(req: UploadSoilDocRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc_url = req.doc_url or "/uploads/soil_reports/soil_health_card_KS-FMR-1001.svg"
    soil_rec = db.query(SoilTestRecord).filter(SoilTestRecord.farmer_id == req.farmer_id).first()
    if soil_rec:
        soil_rec.soil_test_doc_url = doc_url
        db.commit()
    return {"status": "SUCCESS", "document_url": doc_url, "farmer_id": req.farmer_id}

# ==========================================
# 13. MAJOR WAREHOUSE — CAMERA AI GRADING & STORAGE
# ==========================================
class CameraGradingRequest(BaseModel):
    batch_id: Optional[str] = None
    crop_name: Optional[str] = "Wheat (Lokwan)"
    sample_metrics: Optional[Dict[str, float]] = None
    image_base64: Optional[str] = None

@router.post("/major-wh/camera-ai-grading")
def run_camera_ai_grading(req: CameraGradingRequest, db: Session = Depends(get_db)):
    batch = req.batch_id or f"KS-BATCH-{1000 + db.query(MajorWarehouseIntake).count() + 1}"
    return ai_engine.generate_major_wh_quality_grade(
        db=db,
        batch_id=batch,
        crop_name=req.crop_name or "Wheat (Lokwan)",
        sample_metrics=req.sample_metrics
    )

@router.get("/major-wh/storage")
def list_major_wh_storage(db: Session = Depends(get_db)):
    records = db.query(MajorWarehouseStorage).order_by(MajorWarehouseStorage.id.desc()).all()
    return [r.to_dict() for r in records]

class CreateStorageRequest(BaseModel):
    batch_id: str
    crop_name: str
    quantity_kg: float
    current_stock_kg: float
    storage_location: str
    movement_type: Optional[str] = "INTAKE_STORAGE"
    status: Optional[str] = "STORED"
    storage_date: Optional[str] = None

@router.post("/major-wh/storage")
def create_major_wh_storage(req: CreateStorageRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cnt = db.query(MajorWarehouseStorage).count() + 1
    new_storage = MajorWarehouseStorage(
        storage_id=f"KS-STR-{8000 + cnt}",
        batch_id=req.batch_id,
        crop_name=req.crop_name,
        quantity_kg=req.quantity_kg,
        current_stock_kg=req.current_stock_kg,
        storage_location=req.storage_location,
        movement_type=req.movement_type or "INTAKE_STORAGE",
        status=req.status or "STORED",
        storage_date=req.storage_date or datetime.utcnow().strftime("%Y-%m-%d"),
    )
    db.add(new_storage)
    db.commit()
    db.refresh(new_storage)
    return new_storage.to_dict()

@router.put("/major-wh/storage/{id}")
def edit_major_wh_storage(id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return handle_record_edit(db, MajorWarehouseStorage, "major_warehouse_storage", id, req, user)

# ==========================================
# 14. MINOR WAREHOUSE — SENT VS RECEIVED ENTRIES
# ==========================================
@router.get("/minor-wh/sent-received")
def list_minor_wh_sent_received(db: Session = Depends(get_db)):
    records = db.query(MinorWarehouseInward).order_by(MinorWarehouseInward.id.desc()).all()
    return [r.to_dict() for r in records]

@router.put("/minor-wh/sent-received/{id}")
def edit_minor_wh_sent_received(id: int, req: GenericEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    res = handle_record_edit(db, MinorWarehouseInward, "minor_wh_inward_records", id, req, user)
    rec = db.query(MinorWarehouseInward).filter(MinorWarehouseInward.id == id).first()
    if rec:
        sent = rec.sent_quantity_kg if rec.sent_quantity_kg is not None else rec.received_quantity_kg
        rec.sent_quantity_kg = sent
        rec.difference_kg = round(sent - rec.received_quantity_kg, 2)
        db.commit()
        db.refresh(rec)
        return rec.to_dict()
    return res

# ==========================================
# 15. BULK BUYER — AUTO-RETRIEVAL & SINGLE-ID ORDERING
# ==========================================
@router.get("/buyer/verify/{buyer_id}")
def verify_bulk_buyer(buyer_id: str, db: Session = Depends(get_db)):
    buyer = db.query(BulkBuyerRegistry).filter(BulkBuyerRegistry.buyer_id == buyer_id).first()
    if not buyer:
        raise HTTPException(status_code=404, detail=f"Bulk Buyer ID '{buyer_id}' not found in registry.")
    return {
        "status": "VERIFIED",
        "verified": True,
        "buyer": buyer.to_dict(),
    }

class BuyerOrderRequest(BaseModel):
    buyer_id: str
    crop_name: str
    required_quantity_mt: float
    target_grade: Optional[str] = "A"
    max_price_offer_per_quintal: float
    delivery_hub: Optional[str] = "Pune Central Logistics Hub"
    required_by_date: str
    notes: Optional[str] = "Direct procurement order"

@router.post("/buyer/place-order")
def place_buyer_order(req: BuyerOrderRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    buyer = db.query(BulkBuyerRegistry).filter(BulkBuyerRegistry.buyer_id == req.buyer_id).first()
    if not buyer:
        raise HTTPException(status_code=404, detail=f"Invalid Bulk Buyer ID: '{req.buyer_id}'. Please register first.")

    entry = BulkBuyerEntry(
        buyer_id=req.buyer_id,
        crop_name=req.crop_name,
        required_quantity_mt=req.required_quantity_mt,
        target_grade=req.target_grade or "A",
        max_price_offer_per_quintal=req.max_price_offer_per_quintal,
        delivery_hub=req.delivery_hub or "Pune Central Logistics Hub",
        required_by_date=req.required_by_date,
        status="ENTRY_RECORDED",
        notes=f"Order from {buyer.company_name} ({buyer.business_type}). {req.notes or ''}",
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    entry_dict = entry.to_dict()
    return {
        "status": "SUCCESS",
        **entry_dict,
        "order": entry_dict,
        "buyer": buyer.to_dict()
    }

