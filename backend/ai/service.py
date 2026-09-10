from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from backend.models.ai_prediction import AIPredictionRecord
from backend.models.ai_gp_allocation import AIGPAllocationRecord
from backend.models.ai_farmer_recommendation import AIFarmerRecommendationRecord
from backend.models.ai_major_warehouse_grading import AIMajorWarehouseGradingRecord
from backend.models.records_fd import FDCropRequirement
from backend.models.records_ps import PSGPAllocation, PSGPRegistry
from backend.models.records_gp import GPCropAssignment
from backend.models.records_warehouse import MajorWarehouseIntake, MajorWarehouseStorage, MajorWarehouseDispatch, TruckRegistry
from backend.models.records_minor_warehouse import MinorWarehouseInward, MinorWarehouseStock
from backend.models.audit import AuditLog
from backend.models.user import User
from backend.ai.data_preparation import CentralAIDataPreparationPipeline
from backend.ai.predictions.predictor import CropRequirementPredictor
from backend.ai.models.ps_gp_allocation_model import PSToGPAllocationModel
from backend.ai.models.farmer_recommendation_model import GPToFarmerRecommendationModel
from backend.ai.models.warehouse_grading_model import CropQualityVisionModel
from backend.ai.models.warehouse_stock_model import MajorWarehouseStockIntelligenceModel
from backend.ai.schemas import (
    CropRequirementPredictRequest,
    CorrectPredictionRequest,
    GPAllocationPredictRequest,
    CorrectGPAllocationRequest,
    FarmerRecommendationPredictRequest,
    CorrectFarmerRecommendationRequest,
    WarehouseGradingAnalyzeRequest,
    ApproveWarehouseGradingRequest,
    CorrectWarehouseGradingRequest,
    CreateWarehouseStorageRequest,
    UpdateWarehouseStorageRequest,
    CreateDispatchPlanRequest,
    UpdateDispatchRequest,
    StartDispatchTransitRequest,
    UpdateGPSLocationRequest,
    ReceiveMinorWarehouseDispatchRequest,
    CreateTruckRequest,
)

class CentralAIService:
    """
    CENTRAL AI/ML ENGINE SERVICE:
    Unified orchestration layer governing all KrushiSetu AI predictions,
    data preparation, inference pipelines, dual-storage persistence,
    and human review governance.
    """

    def __init__(self):
        self.predictor = CropRequirementPredictor()
        self.gp_allocation_model = PSToGPAllocationModel()
        self.farmer_rec_model = GPToFarmerRecommendationModel()
        self.vision_model = CropQualityVisionModel()
        self.stock_model = MajorWarehouseStockIntelligenceModel()
        self.data_prep = CentralAIDataPreparationPipeline()


    def predict_crop_requirement(
        self,
        db: Session,
        req: CropRequirementPredictRequest,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        1. Ingests real authorized system data across 12 database tables.
        2. Executes explainable multi-factor prediction.
        3. Persists original AI prediction immutably to ai_prediction_records.
        4. Logs audit entry and returns standardized response.
        """
        target_crop = req.crop_name or "Sugarcane"
        target_season = req.season or "Kharif 2026"
        target_region = req.region or "Baramati Block Panchayat Samiti"

        # 1. Prepare real features from database
        features = CentralAIDataPreparationPipeline.prepare_crop_requirement_features(
            db=db,
            crop_name=target_crop,
            season=target_season,
            region=target_region
        )

        # 2. Count existing predictions for unique ID sequencing
        db_count = db.query(func.count(AIPredictionRecord.id)).scalar() or 0

        # 3. Generate prediction
        pred_dict = self.predictor.generate_prediction(features, db_prediction_count=db_count)

        # 4. Save to Database (AIPredictionRecord)
        rec = AIPredictionRecord(
            prediction_id=pred_dict["prediction_id"],
            module_name=pred_dict["module_name"],
            model_name=pred_dict["model_name"],
            model_version=pred_dict["model_version"],
            input_data_reference=pred_dict["input_data_reference"],
            ai_recommended_crop=pred_dict["ai_recommended_crop"],
            ai_recommended_quantity=pred_dict["ai_recommended_quantity"],
            ai_priority=pred_dict["ai_priority"],
            ai_reasoning=pred_dict["ai_reasoning"],
            ai_factors=pred_dict["ai_factors"],
            ai_confidence=pred_dict["ai_confidence"],
            suitable_region=pred_dict["suitable_region"],
            review_status="PENDING_REVIEW",
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)

        # 5. Log Audit Trail
        user_name = user.username if user else "central_ai_engine"
        role_str = user.role.value if (user and hasattr(user.role, 'value')) else (str(user.role) if user else "AI_ENGINE")

        audit_entry = AuditLog(
            table_name="ai_prediction_records",
            record_id=str(rec.id),
            field_name="ai_recommendation_generated",
            old_value="",
            new_value=f"{rec.ai_recommended_quantity:,.0f} MT {rec.ai_recommended_crop} ({rec.ai_priority})",
            edited_by=user_name,
            edited_by_role=role_str,
            change_reason="Autonomous Central AI crop requirement baseline generated from authorized system data.",
        )
        db.add(audit_entry)
        db.commit()

        return rec.to_dict()

    def get_predictions(
        self,
        db: Session,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Retrieves list of stored AI predictions."""
        query = db.query(AIPredictionRecord)
        if status:
            query = query.filter(AIPredictionRecord.review_status == status.upper())
        records = query.order_by(AIPredictionRecord.id.desc()).offset(offset).limit(limit).all()
        return [r.to_dict() for r in records]

    def get_prediction_by_id(self, db: Session, pred_id_or_code: Any) -> Dict[str, Any]:
        """Retrieves single prediction by integer ID or string prediction_id."""
        query = db.query(AIPredictionRecord)
        if str(pred_id_or_code).isdigit():
            rec = query.filter(AIPredictionRecord.id == int(pred_id_or_code)).first()
        else:
            rec = query.filter(AIPredictionRecord.prediction_id == str(pred_id_or_code)).first()

        if not rec:
            raise HTTPException(status_code=404, detail=f"AI Prediction '{pred_id_or_code}' not found.")
        return rec.to_dict()

    def approve_prediction(
        self,
        db: Session,
        pred_id_or_code: Any,
        user: User,
        notes: Optional[str] = "Approved without changes by Food Directorate"
    ) -> Dict[str, Any]:
        """
        HUMAN APPROVAL FLOW:
        Officer reviews the AI recommendation and approves it with zero typing.
        Human final values are set equal to the AI recommendation.
        Original AI values remain permanently intact.
        """
        query = db.query(AIPredictionRecord)
        if str(pred_id_or_code).isdigit():
            rec = query.filter(AIPredictionRecord.id == int(pred_id_or_code)).first()
        else:
            rec = query.filter(AIPredictionRecord.prediction_id == str(pred_id_or_code)).first()

        if not rec:
            raise HTTPException(status_code=404, detail=f"AI Prediction '{pred_id_or_code}' not found.")

        # Update Human Review fields
        old_status = rec.review_status
        rec.review_status = "APPROVED"
        rec.human_final_crop = rec.ai_recommended_crop
        rec.human_final_quantity = rec.ai_recommended_quantity
        rec.human_final_priority = rec.ai_priority
        rec.reviewed_by = user.username
        rec.reviewed_at = datetime.utcnow()
        rec.correction_reason = notes or "Approved as recommended by AI"

        db.commit()
        db.refresh(rec)

        # Audit Log
        role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
        db.add(AuditLog(
            table_name="ai_prediction_records",
            record_id=str(rec.id),
            field_name="review_status",
            old_value=old_status,
            new_value="APPROVED",
            edited_by=user.username,
            edited_by_role=role_str,
            change_reason=rec.correction_reason,
        ))
        db.commit()

        # Seamlessly synchronize with Food Department operational requirements table
        self._sync_to_fd_requirements(db, rec, user, is_approved=True)

        return rec.to_dict()

    def correct_prediction(
        self,
        db: Session,
        pred_id_or_code: Any,
        req: CorrectPredictionRequest,
        user: User
    ) -> Dict[str, Any]:
        """
        HUMAN CORRECTION FLOW:
        Officer overrides the AI recommendation with custom target metrics.
        MANDATORY RULE:
        1. Never overwrites original AI values (stored in ai_recommended_*).
        2. Stores human values in separate dedicated columns (human_final_*).
        3. Enforces mandatory justification for the correction.
        4. Writes comprehensive immutable audit log.
        """
        if not req.correction_reason or len(req.correction_reason.strip()) < 3:
            raise HTTPException(
                status_code=400,
                detail="A valid operational justification (correction reason) is mandatory to override AI recommendation."
            )

        query = db.query(AIPredictionRecord)
        if str(pred_id_or_code).isdigit():
            rec = query.filter(AIPredictionRecord.id == int(pred_id_or_code)).first()
        else:
            rec = query.filter(AIPredictionRecord.prediction_id == str(pred_id_or_code)).first()

        if not rec:
            raise HTTPException(status_code=404, detail=f"AI Prediction '{pred_id_or_code}' not found.")

        # Capture old values for audit
        old_val_summary = (
            f"AI Rec: {rec.ai_recommended_quantity:,.0f} MT {rec.ai_recommended_crop} ({rec.ai_priority})"
        )

        # Apply Human Final Decisions into separate columns
        rec.review_status = "CORRECTED"
        rec.human_final_crop = req.human_final_crop or rec.ai_recommended_crop
        rec.human_final_quantity = req.human_final_quantity_mt
        rec.human_final_priority = req.human_final_priority or rec.ai_priority
        rec.reviewed_by = user.username
        rec.reviewed_at = datetime.utcnow()
        rec.correction_reason = req.correction_reason.strip()

        db.commit()
        db.refresh(rec)

        new_val_summary = (
            f"Human Final: {rec.human_final_quantity:,.0f} MT {rec.human_final_crop} ({rec.human_final_priority})"
        )

        # Audit Log recording AI vs Human difference
        role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
        db.add(AuditLog(
            table_name="ai_prediction_records",
            record_id=str(rec.id),
            field_name="human_correction_applied",
            old_value=old_val_summary,
            new_value=new_val_summary,
            edited_by=user.username,
            edited_by_role=role_str,
            change_reason=rec.correction_reason,
        ))
        db.commit()

        # Synchronize with Food Department operational table
        self._sync_to_fd_requirements(db, rec, user, is_approved=False)

        return rec.to_dict()

    def get_engine_stats(self, db: Session) -> Dict[str, Any]:
        """Returns Central AI Engine telemetry and review status breakdown."""
        total = db.query(func.count(AIPredictionRecord.id)).scalar() or 0
        pending = db.query(func.count(AIPredictionRecord.id)).filter(AIPredictionRecord.review_status == "PENDING_REVIEW").scalar() or 0
        approved = db.query(func.count(AIPredictionRecord.id)).filter(AIPredictionRecord.review_status == "APPROVED").scalar() or 0
        corrected = db.query(func.count(AIPredictionRecord.id)).filter(AIPredictionRecord.review_status == "CORRECTED").scalar() or 0

        return {
            "engine_status": "ONLINE",
            "model_version": "v1.0.0-prototype",
            "total_predictions": total,
            "pending_reviews": pending,
            "approved_predictions": approved,
            "human_corrections": corrected,
            "active_modules": ["crop_requirement_recommendation"],
        }

    def _sync_to_fd_requirements(self, db: Session, rec: AIPredictionRecord, user: User, is_approved: bool):
        """Synchronizes approved or corrected prediction into the operational fd_crop_requirements table."""
        final_qty = rec.human_final_quantity or rec.ai_recommended_quantity
        final_crop = rec.human_final_crop or rec.ai_recommended_crop
        final_priority = rec.human_final_priority or rec.ai_priority
        status_str = "APPROVED" if is_approved else "EDITED_BY_HUMAN"

        existing = db.query(FDCropRequirement).filter(
            FDCropRequirement.crop_name == final_crop
        ).order_by(FDCropRequirement.id.desc()).first()

        if existing:
            existing.target_quantity_mt = final_qty
            existing.human_final_quantity_mt = final_qty
            existing.ai_recommended_quantity_mt = rec.ai_recommended_quantity
            existing.priority = final_priority
            existing.status = status_str
            existing.finalized_by = user.username
            existing.notes = f"Central AI Recommendation #{rec.prediction_id}: {rec.correction_reason or 'Approved without adjustment'}"
        else:
            new_req = FDCropRequirement(
                crop_name=final_crop,
                season="Kharif 2026",
                target_quantity_mt=final_qty,
                ai_recommended_quantity_mt=rec.ai_recommended_quantity,
                human_final_quantity_mt=final_qty,
                priority=final_priority,
                status=status_str,
                finalized_by=user.username,
                notes=f"Central AI Recommendation #{rec.prediction_id}: {rec.correction_reason or 'Approved without adjustment'}",
            )
            db.add(new_req)

        db.commit()

    # =========================================================================
    # TASK 3: PANCHAYAT SAMITI -> GRAM PANCHAYAT AI CROP ALLOCATION METHODS
    # =========================================================================

    def predict_gp_allocation(
        self,
        db: Session,
        req: GPAllocationPredictRequest,
        user: User
    ) -> Dict[str, Any]:
        """
        Runs Central AI PSToGPAllocationModel across candidate Gram Panchayats.
        Strictly enforces Panchayat Samiti jurisdiction and quota conservation.
        """
        # 1. Determine and enforce Panchayat Samiti Jurisdiction
        role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
        ps_name = req.panchayat_samiti_name or "Baramati Block Panchayat Samiti"
        
        if role_str == "PANCHAYAT_SAMITI":
            user_loc = user.jurisdiction_or_location or "Baramati"
            # If user has a specific jurisdiction, reject requests targeting other blocks
            if "baramati" in user_loc.lower():
                if req.panchayat_samiti_name and "baramati" not in req.panchayat_samiti_name.lower():
                    raise HTTPException(
                        status_code=403,
                        detail=f"Access Denied: You are assigned to '{user_loc}' and cannot generate allocations for '{req.panchayat_samiti_name}'."
                    )
                ps_name = "Baramati Block Panchayat Samiti"
            elif user.jurisdiction_or_location:
                if req.panchayat_samiti_name and req.panchayat_samiti_name.lower() != user.jurisdiction_or_location.lower():
                    raise HTTPException(
                        status_code=403,
                        detail=f"Access Denied: You are assigned to '{user.jurisdiction_or_location}' and cannot generate allocations for '{req.panchayat_samiti_name}'."
                    )
                ps_name = user.jurisdiction_or_location

        # 2. Extract real multi-sector features from database
        features = self.data_prep.prepare_ps_gp_allocation_features(
            db=db,
            panchayat_samiti_name=ps_name,
            crop_name=req.crop_name,
            season=req.season,
            total_quota_mt=req.total_quota_mt,
        )

        # 3. Run Central AI allocation inference
        ai_allocations = self.gp_allocation_model.predict(features)
        if not ai_allocations:
            raise HTTPException(
                status_code=400,
                detail=f"No Gram Panchayats found under jurisdiction '{ps_name}' or invalid quota ({req.total_quota_mt} MT)."
            )

        # 4. Generate batch code for this allocation run
        batch_count = db.query(func.count(func.distinct(AIGPAllocationRecord.batch_code))).scalar() or 0
        batch_code = f"BATCH-GPA-2026-{batch_count + 1:03d}"

        # 5. Persist each GP allocation into ai_gp_allocation_records
        saved_records = []
        global_count = db.query(func.count(AIGPAllocationRecord.id)).scalar() or 0

        for idx, alloc in enumerate(ai_allocations):
            global_count += 1
            alloc_code = f"GPA-2026-{global_count:04d}"

            record = AIGPAllocationRecord(
                allocation_code=alloc_code,
                batch_code=batch_code,
                fd_requirement_id=req.fd_requirement_id,
                panchayat_samiti_name=ps_name,
                gp_code=alloc["gp_code"],
                gp_name=alloc["gp_name"],
                crop_name=req.crop_name,
                season=req.season,
                target_year=req.target_year or 2026,
                agricultural_area_ha=alloc.get("agricultural_area_ha"),
                active_farmers_count=alloc.get("active_farmers_count", 0),
                ai_recommended_quantity_mt=alloc["ai_recommended_quantity_mt"],
                ai_priority=alloc.get("ai_priority", req.priority or "HIGH"),
                ai_suitability=alloc.get("ai_suitability", "HIGH_SUITABILITY"),
                ai_reasoning=alloc.get("ai_reasoning"),
                ai_confidence_score=alloc.get("ai_confidence_score", 0.94),
                model_name=self.gp_allocation_model.model_name,
                model_version=self.gp_allocation_model.model_version,
                ai_factors=alloc.get("ai_factors", {}),
                review_status="PENDING_REVIEW",
            )
            db.add(record)
            saved_records.append(record)

        db.commit()
        for r in saved_records:
            db.refresh(r)

        # 6. Audit Trail Logging
        db.add(AuditLog(
            table_name="ai_gp_allocation_records",
            record_id=batch_code,
            field_name="central_ai_gp_allocation_generated",
            old_value="",
            new_value=f"Batch {batch_code}: {req.total_quota_mt:,.1f} MT {req.crop_name} across {len(saved_records)} Gram Panchayats",
            edited_by=user.username,
            edited_by_role=role_str,
            change_reason=f"Central AI GP-wise allocation baseline computed under {ps_name}."
        ))
        db.commit()

        total_allocated = sum(r.ai_recommended_quantity_mt for r in saved_records)
        remaining = round(req.total_quota_mt - total_allocated, 1)

        return {
            "batch_code": batch_code,
            "crop_name": req.crop_name,
            "season": req.season,
            "panchayat_samiti_name": ps_name,
            "total_quota_mt": req.total_quota_mt,
            "total_ai_allocated_mt": round(total_allocated, 1),
            "remaining_quota_mt": remaining,
            "gp_count": len(saved_records),
            "allocations": [r.to_dict() for r in saved_records],
        }

    def get_gp_allocations(
        self,
        db: Session,
        user: User,
        batch_code: Optional[str] = None,
        status: Optional[str] = None,
        crop_name: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Retrieves Gram Panchayat allocations with strict jurisdiction enforcement."""
        query = db.query(AIGPAllocationRecord)
        role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)

        # Jurisdiction Enforcement: PS officers only see their jurisdiction
        if role_str == "PANCHAYAT_SAMITI":
            ps_term = "Baramati"
            if user.jurisdiction_or_location and "Baramati" in user.jurisdiction_or_location:
                ps_term = "Baramati"
            elif user.jurisdiction_or_location:
                ps_term = user.jurisdiction_or_location.split()[0]
            query = query.filter(AIGPAllocationRecord.panchayat_samiti_name.ilike(f"%{ps_term}%"))

        if batch_code:
            query = query.filter(AIGPAllocationRecord.batch_code == batch_code)
        if status:
            query = query.filter(AIGPAllocationRecord.review_status == status.upper())
        if crop_name:
            clean = crop_name.split()[0]
            query = query.filter(AIGPAllocationRecord.crop_name.ilike(f"%{clean}%"))

        records = query.order_by(AIGPAllocationRecord.id.desc()).offset(offset).limit(limit).all()
        return [r.to_dict() for r in records]

    def get_gp_allocation_by_id(self, db: Session, alloc_id: int, user: User) -> Dict[str, Any]:
        """Retrieves single GP allocation with jurisdiction verification."""
        rec = db.query(AIGPAllocationRecord).filter(AIGPAllocationRecord.id == alloc_id).first()
        if not rec:
            raise HTTPException(status_code=404, detail=f"GP Allocation #{alloc_id} not found.")

        role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
        if role_str == "PANCHAYAT_SAMITI":
            if user.jurisdiction_or_location and "Baramati" in user.jurisdiction_or_location:
                if "Baramati" not in rec.panchayat_samiti_name:
                    raise HTTPException(status_code=403, detail="Access denied: Record outside your Panchayat Samiti jurisdiction.")

        return rec.to_dict()

    def approve_gp_allocation(
        self,
        db: Session,
        alloc_id: int,
        user: User,
        notes: Optional[str] = "Approved without modification by Panchayat Samiti"
    ) -> Dict[str, Any]:
        """
        PANCHAYAT SAMITI HUMAN APPROVAL FLOW:
        1. Copies AI recommendation to verified human final columns.
        2. Preserves original AI recommendation intact.
        3. Sets review_status = 'APPROVED'.
        4. Writes immutable audit log.
        5. Synchronizes with operational ps_gp_allocations table.
        """
        rec = db.query(AIGPAllocationRecord).filter(AIGPAllocationRecord.id == alloc_id).first()
        if not rec:
            raise HTTPException(status_code=404, detail=f"GP Allocation #{alloc_id} not found.")

        # Jurisdiction Enforcement
        role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
        if role_str == "PANCHAYAT_SAMITI":
            if user.jurisdiction_or_location and "Baramati" in user.jurisdiction_or_location:
                if "Baramati" not in rec.panchayat_samiti_name:
                    raise HTTPException(status_code=403, detail="Access denied: Cannot approve allocations outside your jurisdiction.")

        old_status = rec.review_status
        rec.review_status = "APPROVED"
        rec.human_final_quantity_mt = rec.ai_recommended_quantity_mt
        rec.human_final_priority = rec.ai_priority
        rec.reviewed_by = user.username
        rec.reviewed_at = datetime.utcnow()
        rec.human_review_notes = notes or "Approved as recommended by AI"

        db.commit()
        db.refresh(rec)

        # Audit Log
        db.add(AuditLog(
            table_name="ai_gp_allocation_records",
            record_id=str(rec.id),
            field_name="review_status",
            old_value=old_status,
            new_value="APPROVED",
            edited_by=user.username,
            edited_by_role=role_str,
            change_reason=f"Approved {rec.gp_name} allocation of {rec.human_final_quantity_mt:,.1f} MT {rec.crop_name} without modification."
        ))
        db.commit()

        # Synchronize with downstream ps_gp_allocations
        self._sync_to_ps_gp_allocations(db, rec, user, is_approved=True)

        return rec.to_dict()

    def correct_gp_allocation(
        self,
        db: Session,
        alloc_id: int,
        req: CorrectGPAllocationRequest,
        user: User
    ) -> Dict[str, Any]:
        """
        PANCHAYAT SAMITI HUMAN CORRECTION FLOW:
        1. Validates mandatory correction reason (>= 5 chars).
        2. Validates positive allocation.
        3. Enforces total requirement quota conservation (cannot exceed approved requirement).
        4. Preserves ai_recommended_quantity_mt intact.
        5. Saves human values into human_final_* columns.
        6. Writes immutable audit log.
        7. Synchronizes with operational ps_gp_allocations table.
        """
        if not req.correction_reason or len(req.correction_reason.strip()) < 5:
            raise HTTPException(
                status_code=422,
                detail="A mandatory operational justification of at least 5 characters is required to correct an AI allocation."
            )

        if req.human_final_quantity_mt <= 0:
            raise HTTPException(
                status_code=422,
                detail="Human final quantity must be greater than 0 MT."
            )

        rec = db.query(AIGPAllocationRecord).filter(AIGPAllocationRecord.id == alloc_id).first()
        if not rec:
            raise HTTPException(status_code=404, detail=f"GP Allocation #{alloc_id} not found.")

        # Jurisdiction Enforcement
        role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
        if role_str == "PANCHAYAT_SAMITI":
            if user.jurisdiction_or_location and "Baramati" in user.jurisdiction_or_location:
                if "Baramati" not in rec.panchayat_samiti_name:
                    raise HTTPException(status_code=403, detail="Access denied: Cannot modify allocations outside your jurisdiction.")

        # Total Quota Constraint Validation across batch
        other_records = db.query(AIGPAllocationRecord).filter(
            AIGPAllocationRecord.batch_code == rec.batch_code,
            AIGPAllocationRecord.id != rec.id,
        ).all()
        
        # Calculate new total if this modification is applied
        current_other_sum = sum(
            (o.human_final_quantity_mt if o.human_final_quantity_mt is not None else o.ai_recommended_quantity_mt)
            for o in other_records
        )
        total_after_edit = current_other_sum + req.human_final_quantity_mt
        batch_original_total = sum(o.ai_recommended_quantity_mt for o in other_records) + rec.ai_recommended_quantity_mt

        # Allow minor flexibility (+5%) or strict check
        if total_after_edit > (batch_original_total * 1.10):
            raise HTTPException(
                status_code=400,
                detail=f"Allocation exceeds approved quota limit. Batch requirement is {batch_original_total:,.1f} MT, but proposed total is {total_after_edit:,.1f} MT."
            )

        old_val_summary = f"AI Rec: {rec.ai_recommended_quantity_mt:,.1f} MT ({rec.ai_priority})"
        new_val_summary = f"Human Final: {req.human_final_quantity_mt:,.1f} MT ({req.human_final_priority or rec.ai_priority})"

        # Dual-Storage Override
        rec.review_status = "CORRECTED"
        rec.human_final_quantity_mt = req.human_final_quantity_mt
        rec.human_final_priority = req.human_final_priority or rec.ai_priority
        rec.reviewed_by = user.username
        rec.reviewed_at = datetime.utcnow()
        rec.correction_reason = req.correction_reason.strip()
        rec.human_review_notes = req.notes

        db.commit()
        db.refresh(rec)

        # Audit Log
        db.add(AuditLog(
            table_name="ai_gp_allocation_records",
            record_id=str(rec.id),
            field_name="human_correction_applied",
            old_value=old_val_summary,
            new_value=new_val_summary,
            edited_by=user.username,
            edited_by_role=role_str,
            change_reason=rec.correction_reason,
        ))
        db.commit()

        # Synchronize with downstream ps_gp_allocations
        self._sync_to_ps_gp_allocations(db, rec, user, is_approved=False)

        return rec.to_dict()

    def batch_approve_gp_allocations(
        self,
        db: Session,
        batch_code: str,
        user: User,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """One-click batch approval of all pending GP allocations for a batch."""
        records = db.query(AIGPAllocationRecord).filter(
            AIGPAllocationRecord.batch_code == batch_code,
            AIGPAllocationRecord.review_status == "PENDING_REVIEW",
        ).all()

        if not records:
            return {"message": "No pending allocations found for this batch.", "approved_count": 0}

        role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
        now = datetime.utcnow()
        approved_count = 0

        for rec in records:
            # Check jurisdiction
            if role_str == "PANCHAYAT_SAMITI":
                if user.jurisdiction_or_location and "Baramati" in user.jurisdiction_or_location:
                    if "Baramati" not in rec.panchayat_samiti_name:
                        continue

            rec.review_status = "APPROVED"
            rec.human_final_quantity_mt = rec.ai_recommended_quantity_mt
            rec.human_final_priority = rec.ai_priority
            rec.reviewed_by = user.username
            rec.reviewed_at = now
            rec.human_review_notes = notes or "Batch approved by Panchayat Samiti BDO"

            self._sync_to_ps_gp_allocations(db, rec, user, is_approved=True)
            approved_count += 1

        db.commit()

        db.add(AuditLog(
            table_name="ai_gp_allocation_records",
            record_id=batch_code,
            field_name="batch_approved",
            old_value="PENDING_REVIEW",
            new_value=f"APPROVED ({approved_count} GPs)",
            edited_by=user.username,
            edited_by_role=role_str,
            change_reason=f"Batch approval signed off for {batch_code} ({approved_count} Gram Panchayats)."
        ))
        db.commit()

        return {
            "batch_code": batch_code,
            "approved_count": approved_count,
            "message": f"Successfully approved {approved_count} Gram Panchayat allocations.",
        }

    def _sync_to_ps_gp_allocations(self, db: Session, rec: AIGPAllocationRecord, user: User, is_approved: bool):
        """Synchronizes approved or corrected GP allocation to operational ps_gp_allocations table."""
        final_qty = rec.human_final_quantity_mt or rec.ai_recommended_quantity_mt
        final_status = "APPROVED" if is_approved else "EDITED_BY_HUMAN"

        existing = db.query(PSGPAllocation).filter(
            PSGPAllocation.gp_name == rec.gp_name,
            PSGPAllocation.crop_name == rec.crop_name,
            PSGPAllocation.season == rec.season,
        ).first()

        if existing:
            existing.allocated_quantity_mt = final_qty
            existing.human_final_quantity_mt = final_qty
            existing.ai_recommended_quantity_mt = rec.ai_recommended_quantity_mt
            existing.status = final_status
            existing.finalized_by = user.username
            existing.finalized_at = datetime.utcnow()
            existing.human_notes = rec.correction_reason or rec.human_review_notes
        else:
            new_alloc = PSGPAllocation(
                panchayat_samiti_name=rec.panchayat_samiti_name,
                gp_name=rec.gp_name,
                crop_name=rec.crop_name,
                allocated_quantity_mt=final_qty,
                season=rec.season,
                status=final_status,
                ai_recommended_quantity_mt=rec.ai_recommended_quantity_mt,
                human_final_quantity_mt=final_qty,
                ai_rationale=rec.ai_reasoning,
                ai_confidence_score=rec.ai_confidence_score,
                finalized_by=user.username,
                finalized_at=datetime.utcnow(),
                human_notes=rec.correction_reason or rec.human_review_notes,
            )
            db.add(new_alloc)
        db.commit()

    # =========================================================================
    # TASK 4: GRAM PANCHAYAT -> FARMER-WISE AI CROP RECOMMENDATION WORKFLOW
    # =========================================================================

    def predict_farmer_recommendations(
        self,
        db: Session,
        req: FarmerRecommendationPredictRequest,
        user: User
    ) -> Dict[str, Any]:
        """
        Runs Central AI GPToFarmerRecommendationModel across registered farmers in target GP.
        Strictly enforces Gram Panchayat jurisdiction and land/quota bounds.
        """
        role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
        gp_name = req.gp_name or "Shirsuphal Gram Panchayat"

        # ABAC Jurisdiction Enforcement
        if role_str == "GRAM_PANCHAYAT":
            user_loc = user.jurisdiction_or_location or "Shirsuphal"
            if "shirsuphal" in user_loc.lower():
                if req.gp_name and "shirsuphal" not in req.gp_name.lower():
                    raise HTTPException(
                        status_code=403,
                        detail=f"Access Denied: You are assigned to '{user_loc}' and cannot generate recommendations for '{req.gp_name}'."
                    )
                gp_name = "Shirsuphal Gram Panchayat"
            elif user.jurisdiction_or_location:
                if req.gp_name and req.gp_name.lower() != user.jurisdiction_or_location.lower():
                    raise HTTPException(
                        status_code=403,
                        detail=f"Access Denied: You are assigned to '{user.jurisdiction_or_location}' and cannot generate recommendations for '{req.gp_name}'."
                    )
                gp_name = user.jurisdiction_or_location

        # 2. Extract real multi-factor features from database
        features = self.data_prep.prepare_gp_farmer_recommendation_features(
            db=db,
            gp_name=gp_name,
            crop_name=req.crop_name,
            season=req.season,
            target_year=req.target_year or 2026,
            gp_target_quota_mt=req.gp_target_quota_mt,
            gp_allocation_id=req.gp_allocation_id,
            panchayat_samiti_name=req.panchayat_samiti_name,
            priority=req.priority or "HIGH",
        )

        # 3. Run Central AI inference
        ai_recommendations = self.farmer_rec_model.predict(features)
        if not ai_recommendations:
            raise HTTPException(
                status_code=400,
                detail=f"No eligible farmers or available agricultural land found under Gram Panchayat '{gp_name}'."
            )

        # 4. Generate batch code
        batch_count = db.query(func.count(func.distinct(AIFarmerRecommendationRecord.batch_code))).scalar() or 0
        batch_code = f"BATCH-FRA-2026-{batch_count + 1:03d}"

        # 5. Persist each farmer recommendation
        saved_records = []
        global_count = db.query(func.count(AIFarmerRecommendationRecord.id)).scalar() or 0

        for idx, rec in enumerate(ai_recommendations):
            global_count += 1
            rec_code = f"REC-FMR-2026-{global_count:04d}"

            record = AIFarmerRecommendationRecord(
                recommendation_code=rec_code,
                batch_code=batch_code,
                gp_allocation_id=features.get("gp_allocation_id"),
                panchayat_samiti_name=rec["panchayat_samiti_name"],
                gp_code=rec["gp_code"],
                gp_name=rec["gp_name"],
                farmer_id=rec["farmer_id"],
                farmer_name=rec["farmer_name"],
                survey_number=rec.get("survey_number"),
                village_name=rec.get("village_name"),
                crop_name=rec["crop_name"],
                season=rec["season"],
                target_year=rec["target_year"],
                farmer_total_land_acres=rec["farmer_total_land_acres"],
                farmer_available_land_acres=rec["farmer_available_land_acres"],
                ai_recommended_area_acres=rec["ai_recommended_area_acres"],
                ai_recommended_quantity_quintals=rec["ai_recommended_quantity_quintals"],
                ai_suitability=rec["ai_suitability"],
                ai_priority=rec["ai_priority"],
                ai_reasoning=rec["ai_reasoning"],
                ai_confidence_score=rec["ai_confidence_score"],
                model_name=self.farmer_rec_model.model_name,
                model_version=self.farmer_rec_model.model_version,
                ai_factors=rec.get("ai_factors", {}),
                review_status="PENDING_REVIEW",
            )
            db.add(record)
            saved_records.append(record)

        db.commit()
        for r in saved_records:
            db.refresh(r)

        # 6. Audit Logging
        total_acres = sum(r.ai_recommended_area_acres for r in saved_records)
        total_qtl = sum(r.ai_recommended_quantity_quintals for r in saved_records)
        total_mt = round(total_qtl / 10.0, 2)
        total_avail_acres = sum(r.farmer_available_land_acres for r in saved_records)
        remaining_land = max(0.0, round(total_avail_acres - total_acres, 1))
        gp_quota_mt = features.get("gp_target_quota_mt", 2500.0)
        remaining_quota = max(0.0, round(gp_quota_mt - total_mt, 1))

        db.add(AuditLog(
            table_name="ai_farmer_recommendation_records",
            record_id=batch_code,
            field_name="central_ai_farmer_recommendations_generated",
            old_value="",
            new_value=f"Batch {batch_code}: {len(saved_records)} farmers, {total_acres:.1f} Acres ({total_qtl:.1f} Qtl / {total_mt} MT) {req.crop_name}",
            edited_by=user.username,
            edited_by_role=role_str,
            change_reason=f"Central AI GP-to-Farmer recommendation baseline computed under {gp_name}."
        ))
        db.commit()

        return {
            "batch_code": batch_code,
            "crop_name": req.crop_name,
            "season": req.season,
            "gp_name": gp_name,
            "gp_approved_quota_mt": gp_quota_mt,
            "total_ai_allocated_acres": round(total_acres, 1),
            "total_ai_allocated_quintals": round(total_qtl, 1),
            "total_ai_allocated_mt": total_mt,
            "remaining_quota_mt": remaining_quota,
            "total_available_land_acres": round(total_avail_acres, 1),
            "remaining_land_acres": remaining_land,
            "farmer_count": len(saved_records),
            "recommendations": [r.to_dict() for r in saved_records],
        }

    def get_farmer_recommendations(
        self,
        db: Session,
        user: User,
        batch_code: Optional[str] = None,
        status: Optional[str] = None,
        gp_name: Optional[str] = None,
        crop_name: Optional[str] = None,
        farmer_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Retrieves farmer crop recommendations with strict GP jurisdiction enforcement."""
        query = db.query(AIFarmerRecommendationRecord)
        role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)

        if role_str == "GRAM_PANCHAYAT":
            clean_loc = "Shirsuphal"
            if user.jurisdiction_or_location and "Shirsuphal" in user.jurisdiction_or_location:
                clean_loc = "Shirsuphal"
            elif user.jurisdiction_or_location:
                clean_loc = user.jurisdiction_or_location.split()[0]
            query = query.filter(AIFarmerRecommendationRecord.gp_name.ilike(f"%{clean_loc}%"))
        elif role_str == "FARMER" and user.farmer_id:
            query = query.filter(AIFarmerRecommendationRecord.farmer_id == user.farmer_id)

        if gp_name:
            clean_gp = gp_name.split()[0]
            query = query.filter(AIFarmerRecommendationRecord.gp_name.ilike(f"%{clean_gp}%"))
        if batch_code:
            query = query.filter(AIFarmerRecommendationRecord.batch_code == batch_code)
        if status:
            query = query.filter(AIFarmerRecommendationRecord.review_status == status.upper())
        if crop_name:
            clean = crop_name.split()[0]
            query = query.filter(AIFarmerRecommendationRecord.crop_name.ilike(f"%{clean}%"))
        if farmer_id:
            query = query.filter(AIFarmerRecommendationRecord.farmer_id == farmer_id)

        records = query.order_by(AIFarmerRecommendationRecord.id.desc()).offset(offset).limit(limit).all()
        return [r.to_dict() for r in records]

    def get_farmer_recommendation_by_id(
        self,
        db: Session,
        rec_id: int,
        user: User
    ) -> Dict[str, Any]:
        """Retrieves full farmer recommendation including soil metrics and document reference."""
        rec = db.query(AIFarmerRecommendationRecord).filter(AIFarmerRecommendationRecord.id == rec_id).first()
        if not rec:
            raise HTTPException(status_code=404, detail=f"Farmer recommendation #{rec_id} not found.")

        role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
        if role_str == "GRAM_PANCHAYAT":
            if user.jurisdiction_or_location and "Shirsuphal" in user.jurisdiction_or_location:
                if "Shirsuphal" not in rec.gp_name:
                    raise HTTPException(status_code=403, detail="Access denied: Record outside your Gram Panchayat jurisdiction.")
        elif role_str == "FARMER":
            if user.farmer_id and rec.farmer_id != user.farmer_id:
                raise HTTPException(status_code=403, detail="Access denied: Cannot view recommendations for other farmers.")

        return rec.to_dict()

    def approve_farmer_recommendation(
        self,
        db: Session,
        rec_id: int,
        user: User,
        notes: Optional[str] = "Approved without modification by Gram Panchayat"
    ) -> Dict[str, Any]:
        """
        GRAM PANCHAYAT HUMAN APPROVAL FLOW:
        1. Copies AI recommendation to verified human final columns.
        2. Preserves original AI recommendation intact (Dual Storage).
        3. Sets review_status = 'APPROVED'.
        4. Writes immutable audit log.
        5. Synchronizes with downstream gp_crop_assignments table.
        """
        rec = db.query(AIFarmerRecommendationRecord).filter(AIFarmerRecommendationRecord.id == rec_id).first()
        if not rec:
            raise HTTPException(status_code=404, detail=f"Farmer recommendation #{rec_id} not found.")

        role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
        if role_str == "GRAM_PANCHAYAT":
            if user.jurisdiction_or_location and "Shirsuphal" in user.jurisdiction_or_location:
                if "Shirsuphal" not in rec.gp_name:
                    raise HTTPException(status_code=403, detail="Access denied: Cannot approve recommendations outside your Gram Panchayat.")

        rec.review_status = "APPROVED"
        rec.human_final_crop = rec.crop_name
        rec.human_final_area_acres = rec.ai_recommended_area_acres
        rec.human_final_quantity_quintals = rec.ai_recommended_quantity_quintals
        rec.human_final_priority = rec.ai_priority
        rec.reviewed_by = user.username
        rec.reviewed_at = datetime.utcnow()
        rec.human_review_notes = notes or "Approved as recommended by AI"

        db.commit()
        db.refresh(rec)

        db.add(AuditLog(
            table_name="ai_farmer_recommendation_records",
            record_id=str(rec.id),
            field_name="review_status",
            old_value="PENDING_REVIEW",
            new_value=f"APPROVED ({rec.human_final_area_acres} Acres / {rec.human_final_quantity_quintals} Qtl)",
            edited_by=user.username,
            edited_by_role=role_str,
            change_reason=rec.human_review_notes,
        ))
        db.commit()

        self._sync_to_gp_crop_assignments(db, rec, user, is_approved=True)
        return rec.to_dict()

    def correct_farmer_recommendation(
        self,
        db: Session,
        rec_id: int,
        req: CorrectFarmerRecommendationRequest,
        user: User
    ) -> Dict[str, Any]:
        """
        GRAM PANCHAYAT HUMAN CORRECTION FLOW:
        1. Validates mandatory operational justification (>= 5 chars).
        2. Validates human_final_area_acres <= farmer_total_land_acres.
        3. Updates human_final_* columns while permanently preserving ai_recommended_*.
        4. Sets review_status = 'CORRECTED'.
        5. Logs audit change.
        6. Synchronizes to gp_crop_assignments.
        """
        reason = (req.correction_reason or req.justification or "").strip()
        if not reason or len(reason) < 5:
            raise HTTPException(
                status_code=422,
                detail="A mandatory operational justification of at least 5 characters is required to correct an AI recommendation."
            )

        if req.human_final_area_acres <= 0:
            raise HTTPException(
                status_code=422,
                detail="Human final parcel area must be greater than 0 Acres."
            )

        rec = db.query(AIFarmerRecommendationRecord).filter(AIFarmerRecommendationRecord.id == rec_id).first()
        if not rec:
            raise HTTPException(status_code=404, detail=f"Farmer recommendation #{rec_id} not found.")

        role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
        if role_str == "GRAM_PANCHAYAT":
            if user.jurisdiction_or_location and "Shirsuphal" in user.jurisdiction_or_location:
                if "Shirsuphal" not in rec.gp_name:
                    raise HTTPException(status_code=403, detail="Access denied: Cannot modify recommendations outside your Gram Panchayat.")

        # Land Constraint Validation
        if req.human_final_area_acres > rec.farmer_total_land_acres:
            raise HTTPException(
                status_code=400,
                detail=f"Allocation area ({req.human_final_area_acres} Acres) exceeds farmer's registered land ({rec.farmer_total_land_acres} Acres)."
            )

        yield_benchmark = rec.ai_recommended_quantity_quintals / (rec.ai_recommended_area_acres or 1.0)
        yield_qtl = req.human_final_quantity_quintals or round(req.human_final_area_acres * yield_benchmark, 1)

        old_val_summary = f"AI Rec: {rec.ai_recommended_area_acres} Acres ({rec.ai_recommended_quantity_quintals} Qtl)"
        new_val_summary = f"Human Final: {req.human_final_area_acres} Acres ({yield_qtl} Qtl)"

        rec.review_status = "CORRECTED"
        rec.human_final_crop = req.human_final_crop or rec.crop_name
        rec.human_final_area_acres = req.human_final_area_acres
        rec.human_final_quantity_quintals = yield_qtl
        rec.human_final_priority = req.human_final_priority or rec.ai_priority
        rec.reviewed_by = user.username
        rec.reviewed_at = datetime.utcnow()
        rec.correction_reason = reason
        rec.human_review_notes = req.notes

        db.commit()
        db.refresh(rec)

        db.add(AuditLog(
            table_name="ai_farmer_recommendation_records",
            record_id=str(rec.id),
            field_name="human_correction_applied",
            old_value=old_val_summary,
            new_value=new_val_summary,
            edited_by=user.username,
            edited_by_role=role_str,
            change_reason=rec.correction_reason,
        ))
        db.commit()

        self._sync_to_gp_crop_assignments(db, rec, user, is_approved=False)
        return rec.to_dict()

    def batch_approve_farmer_recommendations(
        self,
        db: Session,
        batch_code: str,
        user: User,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """One-click batch approval for all pending recommendations in a batch."""
        records = db.query(AIFarmerRecommendationRecord).filter(
            AIFarmerRecommendationRecord.batch_code == batch_code,
            AIFarmerRecommendationRecord.review_status == "PENDING_REVIEW"
        ).all()

        role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
        now = datetime.utcnow()
        approved_count = 0

        for rec in records:
            if role_str == "GRAM_PANCHAYAT":
                if user.jurisdiction_or_location and "Shirsuphal" in user.jurisdiction_or_location:
                    if "Shirsuphal" not in rec.gp_name:
                        continue

            rec.review_status = "APPROVED"
            rec.human_final_crop = rec.crop_name
            rec.human_final_area_acres = rec.ai_recommended_area_acres
            rec.human_final_quantity_quintals = rec.ai_recommended_quantity_quintals
            rec.human_final_priority = rec.ai_priority
            rec.reviewed_by = user.username
            rec.reviewed_at = now
            rec.human_review_notes = notes or "Batch approved by Gram Panchayat Sarpanch"

            self._sync_to_gp_crop_assignments(db, rec, user, is_approved=True)
            approved_count += 1

        db.commit()

        db.add(AuditLog(
            table_name="ai_farmer_recommendation_records",
            record_id=batch_code,
            field_name="batch_approved",
            old_value="PENDING_REVIEW",
            new_value=f"APPROVED ({approved_count} Farmers)",
            edited_by=user.username,
            edited_by_role=role_str,
            change_reason=f"Batch approval signed off for {batch_code} ({approved_count} farmers)."
        ))
        db.commit()

        return {
            "batch_code": batch_code,
            "approved_count": approved_count,
            "message": f"Successfully approved {approved_count} farmer recommendations.",
        }

    def _sync_to_gp_crop_assignments(self, db: Session, rec: AIFarmerRecommendationRecord, user: User, is_approved: bool):
        """Synchronizes approved or corrected farmer recommendation to operational gp_crop_assignments table."""
        final_acres = rec.human_final_area_acres or rec.ai_recommended_area_acres
        final_qtl = rec.human_final_quantity_quintals or rec.ai_recommended_quantity_quintals
        final_status = "APPROVED" if is_approved else "EDITED_BY_HUMAN"

        existing = db.query(GPCropAssignment).filter(
            GPCropAssignment.farmer_id == rec.farmer_id,
            GPCropAssignment.crop_name == rec.crop_name,
            GPCropAssignment.season == rec.season,
        ).order_by(GPCropAssignment.id.desc()).first()

        if existing:
            existing.assigned_acres = final_acres
            existing.required_quantity_quintals = final_qtl
            existing.human_final_acres = final_acres
            existing.human_final_quintals = final_qtl
            existing.status = final_status
            existing.finalized_by = user.username
            existing.finalized_at = datetime.utcnow()
            existing.ai_rationale = rec.ai_reasoning
            existing.ai_confidence_score = rec.ai_confidence_score
        else:
            new_assign = GPCropAssignment(
                farmer_id=rec.farmer_id,
                farmer_name=rec.farmer_name,
                crop_name=rec.human_final_crop or rec.crop_name,
                season=rec.season,
                assigned_acres=final_acres,
                required_quantity_quintals=final_qtl,
                status=final_status,
                ai_recommended_acres=rec.ai_recommended_area_acres,
                ai_recommended_quintals=rec.ai_recommended_quantity_quintals,
                human_final_acres=final_acres,
                human_final_quintals=final_qtl,
                finalized_by=user.username,
                finalized_at=datetime.utcnow(),
                ai_rationale=rec.ai_reasoning,
                ai_confidence_score=rec.ai_confidence_score,
            )
            db.add(new_assign)
        db.commit()

    # =========================================================================
    # TASK 5: MAJOR WAREHOUSE AI CROP QUALITY & GRADING (COMPUTER VISION)
    # =========================================================================

    def analyze_crop_quality(
        self,
        db: Session,
        req: WarehouseGradingAnalyzeRequest,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Ingests real batch intake data, processes camera frame / sample image,
        executes Central AI computer vision analysis across 12 visual parameters,
        and saves an immutable AI prediction record in ai_warehouse_grading_records.
        The AI prediction NEVER becomes the final grade automatically.
        """
        # 1. Prepare features from database & request
        features = self.data_prep.prepare_warehouse_grading_features(
            db=db,
            batch_id=req.batch_id,
            crop_name=req.crop_name,
            farmer_id=req.farmer_id,
            farmer_name=req.farmer_name,
            warehouse_id=req.warehouse_id,
            net_weight_kg=req.net_weight_kg,
            image_data=req.image_data,
            manual_moisture_pct=req.manual_moisture_pct,
            manual_foreign_matter_pct=req.manual_foreign_matter_pct,
            manual_broken_grain_pct=req.manual_broken_grain_pct,
            manual_damaged_grain_pct=req.manual_damaged_grain_pct,
            has_cuts=req.has_cuts,
            has_cracks=req.has_cracks,
            has_spots=req.has_spots,
            has_bruises=req.has_bruises,
            has_pest_damage=req.has_pest_damage,
        )

        # 2. Run Central AI Vision Model
        ai_res = self.vision_model.analyze_crop_quality(features)

        # 3. Generate unique grading code
        count = db.query(func.count(AIMajorWarehouseGradingRecord.id)).scalar() or 0
        clean_batch = features["batch_id"].replace(" ", "").upper()
        grading_code = f"GRD-{clean_batch[-4:]}-{count + 1:04d}"

        # 4. Save to ai_warehouse_grading_records
        record = AIMajorWarehouseGradingRecord(
            grading_code=grading_code,
            batch_id=features["batch_id"],
            intake_id=features.get("intake_id"),
            farmer_id=features["farmer_id"],
            farmer_name=features["farmer_name"],
            crop_name=features["crop_name"],
            warehouse_id=features.get("warehouse_id", "MWH-PUN-01"),
            warehouse_name="Pune Central Silo Complex",
            net_weight_kg=features.get("net_weight_kg"),
            image_url=features["image_url"],
            ai_score=ai_res["ai_score"],
            ai_grade=ai_res["ai_grade"],
            ai_confidence=ai_res["ai_confidence"],
            ai_quality_factors=ai_res["ai_quality_factors"],
            ai_warnings=ai_res["ai_warnings"],
            ai_reasoning=ai_res["ai_reasoning"],
            model_name=ai_res["model_name"],
            model_version=ai_res["model_version"],
            prototype_disclaimer=ai_res["prototype_disclaimer"],
            review_status="PENDING_REVIEW",
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        # 5. Audit Log
        username = user.username if user else "central_ai_vision_engine"
        role_str = user.role.value if (user and hasattr(user.role, 'value')) else (str(user.role) if user else "AI_VISION_ENGINE")
        db.add(AuditLog(
            table_name="ai_warehouse_grading_records",
            record_id=str(record.id),
            field_name="ai_grading_generated",
            old_value="",
            new_value=f"Score: {record.ai_score}, Grade: {record.ai_grade}",
            edited_by=username,
            edited_by_role=role_str,
            change_reason=f"Central AI Computer Vision analyzed grain sample for batch {record.batch_id}."
        ))
        db.commit()

        return record.to_dict()

    def get_warehouse_gradings(
        self,
        db: Session,
        user: User,
        batch_id: Optional[str] = None,
        status: Optional[str] = None,
        crop_name: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        query = db.query(AIMajorWarehouseGradingRecord)
        if batch_id:
            query = query.filter(AIMajorWarehouseGradingRecord.batch_id == batch_id.strip())
        if status:
            query = query.filter(AIMajorWarehouseGradingRecord.review_status == status.strip().upper())
        if crop_name:
            query = query.filter(AIMajorWarehouseGradingRecord.crop_name.ilike(f"%{crop_name.strip()}%"))
        
        records = query.order_by(AIMajorWarehouseGradingRecord.id.desc()).offset(offset).limit(limit).all()
        return [r.to_dict() for r in records]

    def get_warehouse_grading_by_id(self, db: Session, rec_id: int, user: User) -> Dict[str, Any]:
        record = db.query(AIMajorWarehouseGradingRecord).filter(AIMajorWarehouseGradingRecord.id == rec_id).first()
        if not record:
            raise HTTPException(status_code=404, detail=f"Grading record #{rec_id} not found.")
        return record.to_dict()

    def approve_warehouse_grading(
        self,
        db: Session,
        rec_id: int,
        user: User,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        One-click Zero-Typing approval of AI Quality Score and Suggested Grade.
        Sets review_status='APPROVED', preserves original AI fields, and syncs to major_warehouse_intakes.
        """
        record = db.query(AIMajorWarehouseGradingRecord).filter(AIMajorWarehouseGradingRecord.id == rec_id).first()
        if not record:
            raise HTTPException(status_code=404, detail=f"Grading record #{rec_id} not found.")

        old_status = record.review_status
        record.review_status = "APPROVED"
        record.reviewed_by = user.username
        record.reviewed_at = datetime.utcnow()
        record.human_notes = notes or "Approved without modification by Major Warehouse inspector."
        
        # Dual-storage guarantee: Human final values match AI values on approval
        record.human_final_score = record.ai_score
        record.human_final_grade = record.ai_grade

        # Synchronize with operational MajorWarehouseIntake
        self._sync_to_major_wh_intake(db, record, user, is_approved=True)

        role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
        db.add(AuditLog(
            table_name="ai_warehouse_grading_records",
            record_id=str(record.id),
            field_name="review_status",
            old_value=old_status,
            new_value="APPROVED",
            edited_by=user.username,
            edited_by_role=role_str,
            change_reason=f"Inspector approved AI grading for batch {record.batch_id} without modifications (Final Grade: {record.ai_grade}, Score: {record.ai_score})."
        ))
        db.commit()
        db.refresh(record)
        return record.to_dict()

    def correct_warehouse_grading(
        self,
        db: Session,
        rec_id: int,
        req: CorrectWarehouseGradingRequest,
        user: User
    ) -> Dict[str, Any]:
        """
        Human Inspector Review & Correction:
        Requires mandatory justification (>= 5 characters).
        Validates grade and score bounds.
        Never overwrites original AI predictions (ai_score, ai_grade).
        """
        record = db.query(AIMajorWarehouseGradingRecord).filter(AIMajorWarehouseGradingRecord.id == rec_id).first()
        if not record:
            raise HTTPException(status_code=404, detail=f"Grading record #{rec_id} not found.")

        reason = (req.correction_reason or "").strip()
        if len(reason) < 5:
            raise HTTPException(
                status_code=422,
                detail="A mandatory operational justification of at least 5 characters is required to modify AI grading results."
            )

        clean_grade = req.human_final_grade.strip().upper()
        if clean_grade not in ("A", "B", "C", "REJECTED"):
            raise HTTPException(
                status_code=422,
                detail=f"Invalid grade '{req.human_final_grade}'. Must be 'A', 'B', 'C', or 'REJECTED'."
            )

        if not (0.0 <= req.human_final_score <= 100.0):
            raise HTTPException(
                status_code=422,
                detail="Quality score must be between 0 and 100."
            )

        old_val = f"AI Score: {record.ai_score}, AI Grade: {record.ai_grade}"
        new_val = f"Human Score: {req.human_final_score}, Human Grade: {clean_grade}"

        record.review_status = "CORRECTED"
        record.human_final_score = req.human_final_score
        record.human_final_grade = clean_grade
        record.correction_reason = reason
        record.reviewed_by = user.username
        record.reviewed_at = datetime.utcnow()
        record.human_notes = req.notes or f"Corrected by inspector {user.username}."

        # Synchronize with operational MajorWarehouseIntake
        self._sync_to_major_wh_intake(db, record, user, is_approved=False)

        role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
        db.add(AuditLog(
            table_name="ai_warehouse_grading_records",
            record_id=str(record.id),
            field_name="human_grade_override",
            old_value=old_val,
            new_value=new_val,
            edited_by=user.username,
            edited_by_role=role_str,
            change_reason=reason
        ))
        db.commit()
        db.refresh(record)
        return record.to_dict()

    def _sync_to_major_wh_intake(
        self,
        db: Session,
        rec: AIMajorWarehouseGradingRecord,
        user: User,
        is_approved: bool
    ):
        """
        Synchronizes verified AI or human grading result to major_warehouse_intakes table.
        Preserves original AI prediction and records human review decision.
        """
        intake = db.query(MajorWarehouseIntake).filter(
            MajorWarehouseIntake.batch_id == rec.batch_id
        ).first()

        if intake:
            intake.ai_predicted_score = rec.ai_score
            intake.ai_predicted_grade = rec.ai_grade
            intake.human_final_score = rec.human_final_score or rec.ai_score
            intake.human_final_grade = rec.human_final_grade or rec.ai_grade
            intake.review_status = "CONFIRMED"
            intake.reviewed_by = user.username
            intake.reviewed_at = datetime.utcnow()
            if rec.image_url:
                intake.crop_image_url = rec.image_url
            intake.grading_notes = (
                rec.correction_reason if not is_approved else (rec.human_notes or "Approved AI grade")
            )
            db.commit()

    # =========================================================================
    # TASK 6: MAJOR WAREHOUSE STORAGE, INVENTORY & AI STOCK INTELLIGENCE
    # =========================================================================

    def _resolve_batch_quality(self, db: Session, batch_id: str) -> Dict[str, Any]:
        """
        Resolves official certified quality grade and score for a batch.
        Prioritizes Task 5 AIMajorWarehouseGradingRecord, falling back to MajorWarehouseIntake.
        Grade can NEVER be manually edited or overwritten by storage/inventory actions.
        """
        grading_rec = db.query(AIMajorWarehouseGradingRecord).filter(
            AIMajorWarehouseGradingRecord.batch_id == batch_id
        ).order_by(AIMajorWarehouseGradingRecord.id.desc()).first()

        if grading_rec:
            return {
                "grade": grading_rec.effective_final_grade,
                "score": grading_rec.effective_final_score,
                "is_human_reviewed": grading_rec.review_status in ("APPROVED", "CORRECTED"),
                "review_status": grading_rec.review_status,
            }

        intake = db.query(MajorWarehouseIntake).filter(
            MajorWarehouseIntake.batch_id == batch_id
        ).first()

        if intake:
            grade = intake.human_final_grade or intake.ai_predicted_grade or "A"
            score = intake.human_final_score or intake.ai_predicted_score or 90.0
            return {
                "grade": grade,
                "score": score,
                "is_human_reviewed": intake.review_status == "CONFIRMED",
                "review_status": intake.review_status or "PENDING",
            }

        return {
            "grade": "A",
            "score": 88.0,
            "is_human_reviewed": False,
            "review_status": "UNGRADED",
        }

    def _enrich_storage_record(self, db: Session, rec: MajorWarehouseStorage) -> Dict[str, Any]:
        """Converts MajorWarehouseStorage model to dict and enriches with certified Task 5 quality grade."""
        d = rec.to_dict()
        quality_info = self._resolve_batch_quality(db, rec.batch_id)
        d["quality_grade"] = quality_info["grade"]
        d["quality_score"] = quality_info["score"]
        d["quality_review_status"] = quality_info["review_status"]
        d["storage_section"] = rec.storage_location
        d["storage_status"] = rec.status
        return d

    def create_warehouse_storage(
        self,
        db: Session,
        req: CreateWarehouseStorageRequest,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Creates a new storage entry for a verified batch.
        Validates batch linkage (Batch ID -> Farmer ID -> Crop -> AI/Human Grade).
        Enforces mathematical inventory bounds:
          current_stock = quantity_kg - dispatched_quantity_kg
          available_stock = current_stock - reserved_quantity_kg
        """
        # Validate batch exists in system
        intake = db.query(MajorWarehouseIntake).filter(
            MajorWarehouseIntake.batch_id == req.batch_id
        ).first()

        grading_rec = db.query(AIMajorWarehouseGradingRecord).filter(
            AIMajorWarehouseGradingRecord.batch_id == req.batch_id
        ).first()

        if not intake and not grading_rec:
            raise HTTPException(
                status_code=404,
                detail=f"Batch ID '{req.batch_id}' not found in Major Warehouse intake or grading records. Every storage batch must originate from verified crop arrival."
            )

        # Resolve farmer details if not provided
        farmer_id = req.farmer_id or (intake.farmer_id if intake else (grading_rec.farmer_id if grading_rec else "UNKNOWN"))
        farmer_name = req.farmer_name or (intake.farmer_name if intake else (grading_rec.farmer_name if grading_rec else "Farmer"))
        crop_name = req.crop_name or (intake.crop_name if intake else (grading_rec.crop_name if grading_rec else "Wheat"))

        # Generate unique storage ID if not supplied
        storage_id = req.storage_id
        if not storage_id:
            count = db.query(func.count(MajorWarehouseStorage.id)).scalar() or 0
            storage_id = f"KS-STR-{8001 + count}"

        # Ensure storage_id uniqueness
        if db.query(MajorWarehouseStorage).filter(MajorWarehouseStorage.storage_id == storage_id).first():
            raise HTTPException(
                status_code=400,
                detail=f"Storage record ID '{storage_id}' already exists in database."
            )

        # Validate quantities
        if req.quantity_kg <= 0:
            raise HTTPException(status_code=422, detail="Storage quantity must be strictly greater than 0 kg.")

        dispatched = round(float(req.dispatched_quantity_kg or 0.0), 2)
        reserved = round(float(req.reserved_quantity_kg or 0.0), 2)

        if dispatched > req.quantity_kg:
            raise HTTPException(
                status_code=400,
                detail=f"Dispatched quantity ({dispatched} kg) cannot exceed total received quantity ({req.quantity_kg} kg)."
            )

        current_stock = max(0.0, round(float(req.quantity_kg) - dispatched, 2))

        if reserved > current_stock:
            raise HTTPException(
                status_code=400,
                detail=f"Reserved quantity ({reserved} kg) cannot exceed current stock ({current_stock} kg)."
            )

        # Auto-compute status
        if current_stock == 0:
            computed_status = "Completed"
        elif dispatched > 0:
            computed_status = "Partially Dispatched"
        elif reserved > 0:
            computed_status = "Reserved"
        else:
            computed_status = req.storage_status or "Stored"

        storage_rec = MajorWarehouseStorage(
            storage_id=storage_id,
            batch_id=req.batch_id,
            warehouse_id=req.warehouse_id or "MWH-PUN-01",
            warehouse_name=req.warehouse_name or "Pune Central Major Warehouse",
            farmer_id=farmer_id,
            farmer_name=farmer_name,
            crop_name=crop_name,
            crop_category=req.crop_category or "Grains",
            quantity_kg=req.quantity_kg,
            current_stock_kg=current_stock,
            reserved_quantity_kg=reserved,
            dispatched_quantity_kg=dispatched,
            storage_location=req.storage_section or "SILO-A-01",
            storage_type=req.storage_type or "Silo Storage",
            expiry_date=req.expiry_date or "",
            temperature_celsius=req.temperature_celsius,
            humidity_percentage=req.humidity_percentage,
            movement_type=req.movement_type or "INTAKE_STORAGE",
            status=computed_status,
            storage_date=req.storage_date or datetime.utcnow().strftime("%Y-%m-%d"),
            notes=req.notes or f"Stored into {req.storage_section or 'SILO-A-01'} from batch {req.batch_id}",
        )

        db.add(storage_rec)

        # Audit log
        username = user.username if user else "Warehouse Intake Officer"
        role_str = (user.role.value if hasattr(user.role, 'value') else str(user.role)) if user else "MAJOR_WAREHOUSE_MANAGER"
        db.add(AuditLog(
            table_name="major_warehouse_storage",
            record_id=storage_id,
            field_name="create_storage_entry",
            old_value="NONE",
            new_value=f"Batch {req.batch_id}: {req.quantity_kg}kg of {crop_name} stored in {req.storage_section or 'SILO-A-01'}",
            edited_by=username,
            edited_by_role=role_str,
            change_reason="Initial verified batch storage intake"
        ))
        db.commit()
        db.refresh(storage_rec)

        return self._enrich_storage_record(db, storage_rec)

    def get_warehouse_storage_list(
        self,
        db: Session,
        crop_name: Optional[str] = None,
        crop_category: Optional[str] = None,
        status: Optional[str] = None,
        batch_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves list of storage entries with filtering and resolved Task 5 certified quality grade."""
        q = db.query(MajorWarehouseStorage)
        if crop_name:
            q = q.filter(MajorWarehouseStorage.crop_name.ilike(f"%{crop_name}%"))
        if crop_category:
            q = q.filter(MajorWarehouseStorage.crop_category.ilike(f"%{crop_category}%"))
        if status:
            q = q.filter(MajorWarehouseStorage.status == status)
        if batch_id:
            q = q.filter(MajorWarehouseStorage.batch_id == batch_id)

        records = q.order_by(MajorWarehouseStorage.id.desc()).all()
        return [self._enrich_storage_record(db, r) for r in records]

    def get_warehouse_storage_by_id(self, db: Session, storage_id_or_pk: str) -> Dict[str, Any]:
        """Retrieves single storage entry by storage_id (e.g. KS-STR-8001) or primary key id."""
        record = None
        if str(storage_id_or_pk).isdigit():
            record = db.query(MajorWarehouseStorage).filter(MajorWarehouseStorage.id == int(storage_id_or_pk)).first()
        if not record:
            record = db.query(MajorWarehouseStorage).filter(MajorWarehouseStorage.storage_id == storage_id_or_pk).first()

        if not record:
            raise HTTPException(status_code=404, detail=f"Storage record '{storage_id_or_pk}' not found.")

        return self._enrich_storage_record(db, record)

    def update_warehouse_storage(
        self,
        db: Session,
        storage_id_or_pk: str,
        req: UpdateWarehouseStorageRequest,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Updates an existing storage record (e.g. dispatch pick, reservation, transfer, notes).
        Maintains mathematical inventory conservation:
          Current Stock = Received - Dispatched
          Available = Current Stock - Reserved
        Logs changes to audit_logs.
        Grade manipulation is strictly prohibited.
        """
        record = None
        if str(storage_id_or_pk).isdigit():
            record = db.query(MajorWarehouseStorage).filter(MajorWarehouseStorage.id == int(storage_id_or_pk)).first()
        if not record:
            record = db.query(MajorWarehouseStorage).filter(MajorWarehouseStorage.storage_id == storage_id_or_pk).first()

        if not record:
            raise HTTPException(status_code=404, detail=f"Storage record '{storage_id_or_pk}' not found.")

        old_state = (
            f"Stock: {record.current_stock_kg}kg, Dispatched: {record.dispatched_quantity_kg}kg, "
            f"Reserved: {record.reserved_quantity_kg}kg, Location: {record.storage_location}, Status: {record.status}"
        )

        # Dispatch handling
        if req.dispatch_increment_kg is not None:
            if req.dispatch_increment_kg <= 0:
                raise HTTPException(status_code=422, detail="Dispatch increment must be greater than 0 kg.")
            if req.dispatch_increment_kg > record.available_quantity_kg:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot dispatch {req.dispatch_increment_kg} kg. Only {record.available_quantity_kg} kg available for dispatch (Current Stock: {record.current_stock_kg} kg, Reserved: {record.reserved_quantity_kg} kg)."
                )
            record.dispatched_quantity_kg = round(float(record.dispatched_quantity_kg or 0.0) + float(req.dispatch_increment_kg), 2)
        elif req.dispatched_quantity_kg is not None:
            if req.dispatched_quantity_kg > record.quantity_kg:
                raise HTTPException(
                    status_code=400,
                    detail=f"Total dispatched quantity ({req.dispatched_quantity_kg} kg) cannot exceed initial received quantity ({record.quantity_kg} kg)."
                )
            record.dispatched_quantity_kg = round(float(req.dispatched_quantity_kg), 2)

        # Recompute current stock
        record.current_stock_kg = max(0.0, round(float(record.quantity_kg) - float(record.dispatched_quantity_kg or 0.0), 2))

        # Reservation handling
        if req.reserved_quantity_kg is not None:
            if req.reserved_quantity_kg > record.current_stock_kg:
                raise HTTPException(
                    status_code=400,
                    detail=f"Reserved quantity ({req.reserved_quantity_kg} kg) cannot exceed current available stock ({record.current_stock_kg} kg)."
                )
            record.reserved_quantity_kg = round(float(req.reserved_quantity_kg), 2)

        # Status determination
        if record.current_stock_kg == 0:
            record.status = "Completed"
        elif (record.dispatched_quantity_kg or 0.0) > 0:
            record.status = "Partially Dispatched"
        elif (record.reserved_quantity_kg or 0.0) > 0:
            record.status = "Reserved"
        elif req.storage_status:
            record.status = req.storage_status

        # Metadata updates
        if req.storage_section:
            record.storage_location = req.storage_section
        if req.storage_type:
            record.storage_type = req.storage_type
        if req.temperature_celsius is not None:
            record.temperature_celsius = req.temperature_celsius
        if req.humidity_percentage is not None:
            record.humidity_percentage = req.humidity_percentage
        if req.movement_type:
            record.movement_type = req.movement_type
        if req.notes is not None:
            record.notes = req.notes

        record.updated_at = datetime.utcnow()

        new_state = (
            f"Stock: {record.current_stock_kg}kg, Dispatched: {record.dispatched_quantity_kg}kg, "
            f"Reserved: {record.reserved_quantity_kg}kg, Location: {record.storage_location}, Status: {record.status}"
        )

        username = user.username if user else (req.edited_by or "Warehouse Supervisor")
        role_str = (user.role.value if hasattr(user.role, 'value') else str(user.role)) if user else "MAJOR_WAREHOUSE_MANAGER"
        reason = req.edit_reason or "Operational inventory stock update or dispatch movement"

        db.add(AuditLog(
            table_name="major_warehouse_storage",
            record_id=record.storage_id,
            field_name="inventory_update",
            old_value=old_state,
            new_value=new_state,
            edited_by=username,
            edited_by_role=role_str,
            change_reason=reason
        ))
        db.commit()
        db.refresh(record)

        return self._enrich_storage_record(db, record)

    def get_warehouse_inventory(self, db: Session, warehouse_id: Optional[str] = "MWH-PUN-01") -> Dict[str, Any]:
        """
        Calculates aggregate warehouse inventory grouped by crop.
        Summarizes:
        - Total received, dispatched, reserved, current stock, available stock
        - Batch count & IDs
        - Quality grade breakdown (from Task 5)
        - Silo / storage bay locations
        - Central AI run rate & buffer coverage days
        """
        records = db.query(MajorWarehouseStorage).all()
        dispatches = db.query(MajorWarehouseDispatch).all()

        crops_map: Dict[str, Dict[str, Any]] = {}

        for rec in records:
            crop = rec.crop_name
            if crop not in crops_map:
                crops_map[crop] = {
                    "crop_name": crop,
                    "crop_category": rec.crop_category or "Grains",
                    "total_received_kg": 0.0,
                    "total_dispatched_kg": 0.0,
                    "total_reserved_kg": 0.0,
                    "current_stock_kg": 0.0,
                    "available_stock_kg": 0.0,
                    "batches_count": 0,
                    "batch_ids": [],
                    "grades_breakdown": {"A": 0.0, "B": 0.0, "C": 0.0, "REJECTED": 0.0},
                    "storage_sections": set(),
                }

            cm = crops_map[crop]
            cm["total_received_kg"] = round(cm["total_received_kg"] + float(rec.quantity_kg), 2)
            cm["total_dispatched_kg"] = round(cm["total_dispatched_kg"] + float(rec.dispatched_quantity_kg or 0.0), 2)
            cm["total_reserved_kg"] = round(cm["total_reserved_kg"] + float(rec.reserved_quantity_kg or 0.0), 2)
            cm["current_stock_kg"] = round(cm["current_stock_kg"] + float(rec.current_stock_kg), 2)
            cm["available_stock_kg"] = round(cm["available_stock_kg"] + float(rec.available_quantity_kg), 2)
            cm["batches_count"] += 1
            if rec.batch_id not in cm["batch_ids"]:
                cm["batch_ids"].append(rec.batch_id)
            if rec.storage_location:
                cm["storage_sections"].add(rec.storage_location)

            # Grade resolution
            q_info = self._resolve_batch_quality(db, rec.batch_id)
            grade = q_info["grade"]
            if grade not in cm["grades_breakdown"]:
                cm["grades_breakdown"][grade] = 0.0
            cm["grades_breakdown"][grade] = round(cm["grades_breakdown"][grade] + float(rec.current_stock_kg), 2)

        items: List[Dict[str, Any]] = []
        categories_summary: Dict[str, float] = {}

        for crop, data in crops_map.items():
            data["storage_sections"] = sorted(list(data["storage_sections"]))
            cat = data["crop_category"]
            categories_summary[cat] = round(categories_summary.get(cat, 0.0) + data["current_stock_kg"], 2)

            # AI Stock analysis for this crop
            crop_dispatches = [d.to_dict() for d in dispatches if d.crop_name == crop]
            ai_features = {
                "crop_name": crop,
                "current_stock_kg": data["current_stock_kg"],
                "reserved_stock_kg": data["total_reserved_kg"],
                "recent_dispatches": crop_dispatches,
                "incoming_batches": [],
                "avg_storage_days": 18.0,
                "demand_projection_mt": 0.0,
            }
            ai_res = self.stock_model.analyze_stock(ai_features)
            data["status"] = ai_res.get("stock_level_status", "OPTIMAL")
            
            # Extract daily velocity
            factors = ai_res.get("ai_factors", {})
            data["ai_run_rate_kg_day"] = factors.get("daily_consumption_velocity")
            data["ai_buffer_coverage_days"] = factors.get("buffer_coverage_days")
            items.append(data)

        items.sort(key=lambda x: x["current_stock_kg"], reverse=True)

        total_inv = round(sum(i["current_stock_kg"] for i in items), 2)
        total_res = round(sum(i["total_reserved_kg"] for i in items), 2)
        total_disp = round(sum(i["total_dispatched_kg"] for i in items), 2)
        total_avail = round(sum(i["available_stock_kg"] for i in items), 2)

        return {
            "warehouse_id": warehouse_id or "MWH-PUN-01",
            "warehouse_name": "Pune Central Major Warehouse",
            "total_inventory_kg": total_inv,
            "total_reserved_kg": total_res,
            "total_dispatched_kg": total_disp,
            "total_available_kg": total_avail,
            "crop_count": len(items),
            "items": items,
            "categories_summary": categories_summary,
        }

    def get_warehouse_stock_insights(
        self,
        db: Session,
        warehouse_id: Optional[str] = "MWH-PUN-01"
    ) -> Dict[str, Any]:
        """
        Executes Central AI Stock Intelligence analysis.
        Calculates:
        - Overall stock status (LOW_STOCK, OPTIMAL, HIGH_STOCK, INSUFFICIENT_DATA)
        - Run rate and buffer coverage days
        - Transparent "WHY DID AI GIVE THIS RESULT?" factors breakdown
        - Prototype disclaimer and data sparsity notice if history is sparse
        """
        inventory = self.get_warehouse_inventory(db, warehouse_id)
        dispatches = db.query(MajorWarehouseDispatch).all()
        dispatch_dicts = [d.to_dict() for d in dispatches]

        is_sparse = len(inventory["items"]) == 0 and len(dispatch_dicts) == 0
        sparse_notice = (
            "Insufficient historical data for reliable AI prediction."
            if is_sparse or len(dispatch_dicts) < 2
            else None
        )

        crop_insights = []
        for item in inventory["items"]:
            crop_dispatches = [d for d in dispatch_dicts if d.get("crop_name") == item["crop_name"]]
            analysis = self.stock_model.analyze_stock({
                "crop_name": item["crop_name"],
                "current_stock_kg": item["current_stock_kg"],
                "reserved_stock_kg": item["total_reserved_kg"],
                "recent_dispatches": crop_dispatches,
                "avg_storage_days": 15.0,
                "demand_projection_mt": 0.0,
            })
            crop_insights.append(analysis)

        # Capacity utilization (e.g. Pune Central Major Warehouse has ~25,000 MT capacity = 25,000,000 kg)
        max_capacity_kg = 25000000.0
        utilization_pct = round((inventory["total_inventory_kg"] / max_capacity_kg) * 100, 2)

        # Overall status
        if any(ci.get("stock_level_status") == "LOW_STOCK" for ci in crop_insights):
            overall_status = "LOW_STOCK"
        elif any(ci.get("stock_level_status") == "HIGH_STOCK" for ci in crop_insights):
            overall_status = "HIGH_STOCK"
        elif not crop_insights:
            overall_status = "INSUFFICIENT_DATA"
        else:
            overall_status = "OPTIMAL"

        return {
            "model_name": self.stock_model.model_name,
            "model_version": self.stock_model.model_version,
            "disclaimer": self.stock_model.prototype_disclaimer,
            "status": "SUCCESS",
            "is_sparse_data": is_sparse or (len(dispatch_dicts) < 2),
            "sparse_data_notice": sparse_notice,
            "overall_stock_status": overall_status,
            "storage_utilization_pct": utilization_pct,
            "crop_insights": crop_insights,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def get_warehouse_stock_recommendations(
        self,
        db: Session,
        warehouse_id: Optional[str] = "MWH-PUN-01"
    ) -> Dict[str, Any]:
        """
        Central AI Proactive Recommendations and Stock Alerts.
        Suggests replenishment or dispatch balance based on velocity and buffer coverage.
        """
        insights = self.get_warehouse_stock_insights(db, warehouse_id)
        recommendations = []
        alerts = []

        if insights.get("sparse_data_notice"):
            alerts.append(f"AI Notice: {insights['sparse_data_notice']}")

        for ci in insights.get("crop_insights", []):
            crop = ci["crop_name"]
            status = ci["stock_level_status"]
            if status == "LOW_STOCK":
                alerts.append(f"CRITICAL: {crop} stock buffer is critically low! ({ci.get('warning')})")
                recommendations.append({
                    "crop_name": crop,
                    "priority": "HIGH",
                    "action_type": "REPLENISH",
                    "action": f"Request {ci.get('expected_requirement_mt', 50)} MT allocation replenish from GP clusters for {crop}.",
                    "rationale": ci.get("why_explanation"),
                })
            elif status == "HIGH_STOCK":
                alerts.append(f"ADVISORY: {crop} inventory exceeds 90-day buffer. High storage dwell time.")
                recommendations.append({
                    "crop_name": crop,
                    "priority": "MEDIUM",
                    "action_type": "EXPEDITE_DISPATCH",
                    "action": f"Prioritize dispatch transfers of {crop} to sub-district APMC godowns or processing mills.",
                    "rationale": ci.get("why_explanation"),
                })
            else:
                recommendations.append({
                    "crop_name": crop,
                    "priority": "LOW",
                    "action_type": "MAINTAIN",
                    "action": f"Maintain standard storage aeration and climate monitoring for {crop}.",
                    "rationale": ci.get("why_explanation"),
                })

        return {
            "model_name": self.stock_model.model_name,
            "model_version": self.stock_model.model_version,
            "recommendations": recommendations,
            "alerts": alerts,
            "generated_at": datetime.utcnow().isoformat(),
        }

    # =========================================================================
    # TASK 7: MAJOR WAREHOUSE -> MINOR WAREHOUSE DISPATCH & TRUCK TRACKING
    # =========================================================================

    def get_trucks_list(self, db: Session, status: Optional[str] = None) -> List[Dict[str, Any]]:
        query = db.query(TruckRegistry)
        if status:
            query = query.filter(TruckRegistry.current_status == status)
        trucks = query.order_by(TruckRegistry.truck_id.asc()).all()
        return [t.to_dict() for t in trucks]

    def create_truck(self, db: Session, req: CreateTruckRequest, user: Optional[User] = None) -> Dict[str, Any]:
        truck_id = req.truck_id
        if not truck_id:
            count = db.query(TruckRegistry).count()
            truck_id = f"TRK-{count + 1:03d}"

        existing = db.query(TruckRegistry).filter(
            or_(TruckRegistry.truck_id == truck_id, TruckRegistry.vehicle_number == req.vehicle_number)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Truck ID '{truck_id}' or Vehicle Number '{req.vehicle_number}' already registered.")

        truck = TruckRegistry(
            truck_id=truck_id,
            vehicle_number=req.vehicle_number,
            vehicle_type=req.vehicle_type or "16-Wheeler Heavy Grain Carrier",
            capacity_mt=req.capacity_mt or 25.0,
            driver_name=req.driver_name,
            driver_phone=req.driver_phone or "",
            driver_id=req.driver_id or f"DRV-{truck_id.split('-')[-1]}",
            current_status=req.current_status or "AVAILABLE",
            origin_base=req.origin_base or "Pune Central Major Silo Hub",
            last_location=req.last_location or "Pune Hub Logistics Yard",
            last_latitude=req.last_latitude or 18.5204,
            last_longitude=req.last_longitude or 73.8567,
            last_gps_update=datetime.utcnow()
        )
        db.add(truck)
        db.commit()
        db.refresh(truck)
        return truck.to_dict()

    def create_warehouse_dispatch(
        self,
        db: Session,
        req: CreateDispatchPlanRequest,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Create a Major Warehouse -> Minor Warehouse dispatch record.
        - Verifies immutable batch linkage (Batch ID -> Farmer -> Crop -> Grade)
        - Strictly enforces inventory conservation (Sent Qty <= Available Storage Qty)
        - Deducts stock from storage
        - Assigns truck & driver
        """
        # 1. Lookup storage record for batch
        storage = db.query(MajorWarehouseStorage).filter(
            MajorWarehouseStorage.batch_id == req.batch_id
        ).order_by(MajorWarehouseStorage.id.desc()).first()

        if not storage:
            # Fallback lookup in Intake
            intake = db.query(MajorWarehouseIntake).filter(
                MajorWarehouseIntake.batch_id == req.batch_id
            ).first()
            if not intake:
                raise HTTPException(status_code=404, detail=f"Batch '{req.batch_id}' not found in storage or intake.")
            # Auto-create storage record if missing
            storage = MajorWarehouseStorage(
                storage_id=f"STR-{req.batch_id}",
                batch_id=req.batch_id,
                warehouse_id="MWH-PUN-01",
                warehouse_name="Pune Central Major Warehouse",
                farmer_id=intake.farmer_id,
                farmer_name=intake.farmer_name,
                crop_name=intake.crop_name,
                crop_category="Grains",
                quantity_kg=intake.net_weight_kg,
                current_stock_kg=intake.net_weight_kg,
                storage_location=intake.storage_silo_bay or "Silo Bay A-1",
                storage_date=datetime.utcnow().strftime("%Y-%m-%d"),
                status="Stored"
            )
            db.add(storage)
            db.commit()
            db.refresh(storage)

        # 2. Strict Inventory Conservation Check
        available_qty = storage.available_quantity_kg
        if req.dispatch_quantity_kg <= 0:
            raise HTTPException(status_code=400, detail="Dispatch quantity must be strictly greater than 0 kg.")
        if req.dispatch_quantity_kg > available_qty:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot dispatch {req.dispatch_quantity_kg} kg. Only {available_qty} kg available in storage for batch {req.batch_id}."
            )

        # 3. Resolve certified quality grade from intake / grading record
        intake_rec = db.query(MajorWarehouseIntake).filter(MajorWarehouseIntake.batch_id == req.batch_id).first()
        final_grade = req.final_grade
        if not final_grade and intake_rec:
            final_grade = intake_rec.human_final_grade or intake_rec.ai_predicted_grade or "A"
        if not final_grade:
            final_grade = "A"

        # 4. Generate dispatch_id
        count = db.query(MajorWarehouseDispatch).count()
        dispatch_id = f"DSP-{datetime.utcnow().strftime('%Y%m%d')}-{count + 101:04d}"

        # 5. Resolve truck and driver
        truck_record = None
        truck_id = req.truck_id
        truck_number = req.truck_number
        driver_id = req.driver_id
        driver_name = req.driver_name
        driver_phone = req.driver_phone

        if truck_id:
            truck_record = db.query(TruckRegistry).filter(TruckRegistry.truck_id == truck_id).first()
        elif truck_number:
            truck_record = db.query(TruckRegistry).filter(TruckRegistry.vehicle_number == truck_number).first()

        if truck_record:
            truck_id = truck_record.truck_id
            truck_number = truck_record.vehicle_number
            if not driver_name:
                driver_name = truck_record.driver_name
            if not driver_phone:
                driver_phone = truck_record.driver_phone
            if not driver_id:
                driver_id = truck_record.driver_id
            truck_record.current_status = "ASSIGNED"
            truck_record.current_dispatch_id = dispatch_id
            truck_record.destination = req.destination_minor_warehouse or "Baramati APMC Transit Godown"

        # 6. Deduct stock from storage
        storage.dispatched_quantity_kg = round(float(storage.dispatched_quantity_kg or 0.0) + float(req.dispatch_quantity_kg), 2)
        storage.current_stock_kg = max(0.0, round(float(storage.quantity_kg or 0.0) - float(storage.dispatched_quantity_kg), 2))
        if storage.current_stock_kg <= 0:
            storage.status = "Completed"
        else:
            storage.status = "Partially Dispatched"
        storage.movement_type = "DISPATCH_PICK"

        # 7. Create Dispatch Record
        dispatch = MajorWarehouseDispatch(
            dispatch_id=dispatch_id,
            batch_id=req.batch_id,
            crop_name=storage.crop_name or req.crop_name or "Wheat",
            final_grade=final_grade,
            dispatch_quantity_kg=req.dispatch_quantity_kg,
            origin_warehouse=req.origin_warehouse or "Pune Central Silo Hub",
            origin_warehouse_id=req.origin_warehouse_id or "MWH-PUN-01",
            destination_minor_warehouse=req.destination_minor_warehouse or "Baramati APMC Transit Godown",
            destination_minor_warehouse_id=req.destination_minor_warehouse_id or "MIN-BMT-01",
            truck_id=truck_id or "TRK-001",
            truck_number=truck_number or "MH-12-Q-4521",
            driver_id=driver_id or "DRV-001",
            driver_name=driver_name or "Ramesh Patil",
            driver_phone=driver_phone or "+91 98220 11223",
            dispatch_date=req.dispatch_date or datetime.utcnow().strftime("%Y-%m-%d"),
            departure_time=req.departure_time or "10:30 AM",
            expected_arrival=req.expected_arrival or "02:30 PM",
            status="Pending Departure",
            delivery_status="PENDING",
            current_location=req.origin_warehouse or "Pune Central Silo Hub",
            latitude=18.5204,
            longitude=73.8567,
            last_gps_update=datetime.utcnow(),
            is_gps_active=False,
            notes=req.notes or f"Dispatch from {storage.storage_location} to {req.destination_minor_warehouse}"
        )
        db.add(dispatch)
        db.commit()
        db.refresh(dispatch)

        # Audit Log
        uname = user.username if user else "warehouse_admin"
        role_str = (user.role.value if hasattr(user.role, 'value') else str(user.role)) if user else "MAJOR_WAREHOUSE_MANAGER"
        db.add(AuditLog(
            table_name="major_warehouse_dispatches",
            record_id=str(dispatch.id),
            field_name="dispatch_created",
            old_value=None,
            new_value=f"Created {dispatch_id} for {req.dispatch_quantity_kg}kg {dispatch.crop_name} (Grade {final_grade})",
            edited_by=uname,
            edited_by_role=role_str,
            change_reason=f"Dispatched from storage {storage.storage_id}"
        ))
        db.commit()

        return dispatch.to_dict()

    def get_warehouse_dispatches(
        self,
        db: Session,
        batch_id: Optional[str] = None,
        status: Optional[str] = None,
        destination: Optional[str] = None,
        origin: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        query = db.query(MajorWarehouseDispatch)
        if batch_id:
            query = query.filter(MajorWarehouseDispatch.batch_id == batch_id)
        if status:
            query = query.filter(
                or_(
                    MajorWarehouseDispatch.status == status,
                    MajorWarehouseDispatch.delivery_status == status
                )
            )
        if destination:
            query = query.filter(MajorWarehouseDispatch.destination_minor_warehouse.ilike(f"%{destination}%"))
        if origin:
            query = query.filter(MajorWarehouseDispatch.origin_warehouse.ilike(f"%{origin}%"))
        records = query.order_by(MajorWarehouseDispatch.id.desc()).offset(offset).limit(limit).all()
        return [r.to_dict() for r in records]

    def get_warehouse_dispatch_by_id(self, db: Session, dispatch_id_or_pk: Any) -> Dict[str, Any]:
        query = db.query(MajorWarehouseDispatch)
        if str(dispatch_id_or_pk).isdigit():
            rec = query.filter(MajorWarehouseDispatch.id == int(dispatch_id_or_pk)).first()
        else:
            rec = query.filter(MajorWarehouseDispatch.dispatch_id == str(dispatch_id_or_pk)).first()
        if not rec:
            raise HTTPException(status_code=404, detail=f"Dispatch '{dispatch_id_or_pk}' not found.")
        return rec.to_dict()

    def update_warehouse_dispatch(
        self,
        db: Session,
        dispatch_id_or_pk: Any,
        req: UpdateDispatchRequest,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        query = db.query(MajorWarehouseDispatch)
        if str(dispatch_id_or_pk).isdigit():
            rec = query.filter(MajorWarehouseDispatch.id == int(dispatch_id_or_pk)).first()
        else:
            rec = query.filter(MajorWarehouseDispatch.dispatch_id == str(dispatch_id_or_pk)).first()
        if not rec:
            raise HTTPException(status_code=404, detail=f"Dispatch '{dispatch_id_or_pk}' not found.")

        # Update allowed editable fields
        if req.truck_number is not None:
            rec.truck_number = req.truck_number
        if req.driver_name is not None:
            rec.driver_name = req.driver_name
        if req.driver_phone is not None:
            rec.driver_phone = req.driver_phone
        if req.destination_minor_warehouse is not None:
            rec.destination_minor_warehouse = req.destination_minor_warehouse
        if req.expected_arrival is not None:
            rec.expected_arrival = req.expected_arrival
        if req.departure_time is not None:
            rec.departure_time = req.departure_time
        if req.notes is not None:
            rec.notes = req.notes
        if req.status is not None:
            rec.status = req.status
            rec.delivery_status = req.status

        db.commit()
        db.refresh(rec)
        return rec.to_dict()

    def start_dispatch_transit(
        self,
        db: Session,
        dispatch_id_or_pk: Any,
        req: Optional[StartDispatchTransitRequest] = None,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Transition dispatch to 'In Transit'.
        Activates GPS tracking on driver duty.
        """
        query = db.query(MajorWarehouseDispatch)
        if str(dispatch_id_or_pk).isdigit():
            rec = query.filter(MajorWarehouseDispatch.id == int(dispatch_id_or_pk)).first()
        else:
            rec = query.filter(MajorWarehouseDispatch.dispatch_id == str(dispatch_id_or_pk)).first()
        if not rec:
            raise HTTPException(status_code=404, detail=f"Dispatch '{dispatch_id_or_pk}' not found.")

        rec.status = "In Transit"
        rec.delivery_status = "IN_TRANSIT"
        rec.is_gps_active = True
        rec.departure_time = (req.departure_time if req and req.departure_time else datetime.utcnow().strftime("%I:%M %p"))
        rec.last_gps_update = datetime.utcnow()

        if req and req.notes:
            rec.notes = f"{rec.notes or ''} | {req.notes}".strip(" |")

        # Sync Truck status
        if rec.truck_id or rec.truck_number:
            truck = db.query(TruckRegistry).filter(
                or_(TruckRegistry.truck_id == rec.truck_id, TruckRegistry.vehicle_number == rec.truck_number)
            ).first()
            if truck:
                truck.current_status = "IN_TRANSIT"
                truck.current_dispatch_id = rec.dispatch_id
                truck.destination = rec.destination_minor_warehouse
                truck.last_gps_update = datetime.utcnow()

        db.commit()
        db.refresh(rec)

        uname = user.username if user else "warehouse_officer"
        role_str = (user.role.value if hasattr(user.role, 'value') else str(user.role)) if user else "MAJOR_WAREHOUSE_MANAGER"
        db.add(AuditLog(
            table_name="major_warehouse_dispatches",
            record_id=str(rec.id),
            field_name="status",
            old_value="Pending Departure",
            new_value="In Transit",
            edited_by=uname,
            edited_by_role=role_str,
            change_reason="Started vehicle delivery transit with GPS tracking enabled"
        ))
        db.commit()
        return rec.to_dict()

    def update_dispatch_gps_location(
        self,
        db: Session,
        dispatch_id_or_pk: Any,
        req: UpdateGPSLocationRequest,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Updates live GPS coordinates sent from the driver's device.
        Strict privacy enforcement: GPS tracking is active ONLY during transit duty.
        """
        query = db.query(MajorWarehouseDispatch)
        if str(dispatch_id_or_pk).isdigit():
            rec = query.filter(MajorWarehouseDispatch.id == int(dispatch_id_or_pk)).first()
        else:
            rec = query.filter(MajorWarehouseDispatch.dispatch_id == str(dispatch_id_or_pk)).first()
        if not rec:
            raise HTTPException(status_code=404, detail=f"Dispatch '{dispatch_id_or_pk}' not found.")

        if not rec.is_gps_active or rec.status in ("Completed", "Received", "Cancelled"):
            raise HTTPException(
                status_code=400,
                detail="GPS tracking is inactive. Driver is not currently on active delivery duty."
            )

        rec.latitude = req.latitude
        rec.longitude = req.longitude
        if req.location_name:
            rec.current_location = req.location_name
        rec.last_gps_update = datetime.utcnow()

        # Sync with Truck Registry
        truck = db.query(TruckRegistry).filter(
            or_(TruckRegistry.truck_id == rec.truck_id, TruckRegistry.vehicle_number == rec.truck_number)
        ).first()
        if truck:
            truck.last_latitude = req.latitude
            truck.last_longitude = req.longitude
            if req.location_name:
                truck.last_location = req.location_name
            truck.last_gps_update = datetime.utcnow()

        db.commit()
        db.refresh(rec)

        return {
            "dispatch_id": rec.dispatch_id,
            "truck_number": rec.truck_number,
            "latitude": rec.latitude,
            "longitude": rec.longitude,
            "current_location": rec.current_location,
            "last_gps_update": rec.last_gps_update.strftime("%Y-%m-%d %H:%M:%S"),
            "google_maps_url": rec.google_maps_url,
            "is_gps_active": rec.is_gps_active,
            "status": rec.status
        }

    def receive_minor_warehouse_dispatch(
        self,
        db: Session,
        dispatch_id_or_pk: Any,
        req: ReceiveMinorWarehouseDispatchRequest,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Minor Warehouse receiving flow:
        - Calculates difference = sent_quantity_kg - received_quantity_kg
        - If difference != 0: status becomes 'Discrepancy' (or 'WEIGHT_MISMATCH')
        - If difference == 0: status becomes 'Completed' / 'VERIFIED_IN_STOCK'
        - Major Warehouse sent record quantity is preserved untouched
        - Syncs to MinorWarehouseInward and MinorWarehouseStock
        - Deactivates GPS tracking and frees truck
        """
        query = db.query(MajorWarehouseDispatch)
        if str(dispatch_id_or_pk).isdigit():
            rec = query.filter(MajorWarehouseDispatch.id == int(dispatch_id_or_pk)).first()
        else:
            rec = query.filter(MajorWarehouseDispatch.dispatch_id == str(dispatch_id_or_pk)).first()
        if not rec:
            raise HTTPException(status_code=404, detail=f"Dispatch '{dispatch_id_or_pk}' not found.")

        sent_qty = float(rec.dispatch_quantity_kg)
        received_qty = float(req.received_quantity_kg)
        if received_qty < 0:
            raise HTTPException(status_code=400, detail="Received quantity cannot be negative.")

        difference_kg = round(sent_qty - received_qty, 2)
        has_discrepancy = abs(difference_kg) > 0.001

        # Update Dispatch Record
        old_status = rec.status
        if has_discrepancy:
            rec.status = "Discrepancy"
            rec.delivery_status = "DISCREPANCY"
            verification_status = "WEIGHT_MISMATCH"
        else:
            rec.status = "Completed"
            rec.delivery_status = "DELIVERED"
            verification_status = "VERIFIED_IN_STOCK"

        rec.actual_arrival = req.arrival_time or datetime.utcnow().strftime("%I:%M %p")
        rec.is_gps_active = False # Stop tracking on duty complete
        rec.current_location = f"{rec.destination_minor_warehouse} (Delivered)"

        # 1. Sync to MinorWarehouseInward
        inward_rec = db.query(MinorWarehouseInward).filter(
            MinorWarehouseInward.dispatch_id == rec.dispatch_id
        ).first()

        discrepancy_note = req.discrepancy_reason or ("Exact Match verified" if not has_discrepancy else f"Weight mismatch of {difference_kg} kg observed at intake.")

        if not inward_rec:
            inward_rec = MinorWarehouseInward(
                dispatch_id=rec.dispatch_id,
                batch_id=rec.batch_id,
                crop_name=rec.crop_name,
                source_major_wh=rec.origin_warehouse,
                truck_number=rec.truck_number,
                driver_name=rec.driver_name,
                sent_quantity_kg=sent_qty,
                received_quantity_kg=received_qty,
                difference_kg=difference_kg,
                dispatch_time=rec.departure_time or "10:30 AM",
                arrival_time=rec.actual_arrival,
                discrepancy_reason=discrepancy_note,
                intake_date=datetime.utcnow().strftime("%Y-%m-%d"),
                verification_status=verification_status
            )
            db.add(inward_rec)
        else:
            inward_rec.received_quantity_kg = received_qty
            inward_rec.difference_kg = difference_kg
            inward_rec.arrival_time = rec.actual_arrival
            inward_rec.discrepancy_reason = discrepancy_note
            inward_rec.verification_status = verification_status

        # 2. Sync to MinorWarehouseStock
        stock_rec = db.query(MinorWarehouseStock).filter(
            MinorWarehouseStock.crop_name == rec.crop_name,
            MinorWarehouseStock.batch_id == rec.batch_id
        ).first()

        if not stock_rec:
            stock_rec = MinorWarehouseStock(
                crop_name=rec.crop_name,
                batch_id=rec.batch_id,
                current_stock_kg=received_qty,
                warehouse_location=rec.destination_minor_warehouse or "Baramati APMC Godown No. 3",
                last_replenished=datetime.utcnow().strftime("%Y-%m-%d")
            )
            db.add(stock_rec)
        else:
            stock_rec.current_stock_kg = round(float(stock_rec.current_stock_kg or 0.0) + received_qty, 2)
            stock_rec.last_replenished = datetime.utcnow().strftime("%Y-%m-%d")

        # 3. Release Truck to AVAILABLE
        truck = db.query(TruckRegistry).filter(
            or_(TruckRegistry.truck_id == rec.truck_id, TruckRegistry.vehicle_number == rec.truck_number)
        ).first()
        if truck:
            truck.current_status = "AVAILABLE"
            truck.current_dispatch_id = None
            truck.destination = None
            truck.last_location = f"{rec.destination_minor_warehouse} Yard"
            truck.last_gps_update = datetime.utcnow()

        db.commit()
        db.refresh(rec)

        uname = user.username if user else req.receiver_name or "minor_wh_officer"
        role_str = (user.role.value if hasattr(user.role, 'value') else str(user.role)) if user else "MINOR_WAREHOUSE_MANAGER"
        db.add(AuditLog(
            table_name="minor_wh_inward_records",
            record_id=str(inward_rec.id if inward_rec else rec.id),
            field_name="receiving_completed",
            old_value=old_status,
            new_value=f"Received {received_qty}kg (Sent: {sent_qty}kg, Diff: {difference_kg}kg, Status: {rec.status})",
            edited_by=uname,
            edited_by_role=role_str,
            change_reason=discrepancy_note
        ))
        db.commit()

        return {
            "dispatch": rec.to_dict(),
            "inward_receipt": inward_rec.to_dict() if inward_rec else None,
            "difference_kg": difference_kg,
            "has_discrepancy": has_discrepancy,
            "status": rec.status,
            "message": f"Successfully received {received_qty} kg of {rec.crop_name}. Status: {rec.status}."
        }

    def get_dispatch_tracking(self, db: Session, dispatch_id_or_pk: Any) -> Dict[str, Any]:
        """
        Retrieves real-time GPS tracking details and Google Maps deep link for a dispatch.
        """
        query = db.query(MajorWarehouseDispatch)
        if str(dispatch_id_or_pk).isdigit():
            rec = query.filter(MajorWarehouseDispatch.id == int(dispatch_id_or_pk)).first()
        else:
            rec = query.filter(MajorWarehouseDispatch.dispatch_id == str(dispatch_id_or_pk)).first()
        if not rec:
            raise HTTPException(status_code=404, detail=f"Dispatch '{dispatch_id_or_pk}' not found.")

        return {
            "dispatch_id": rec.dispatch_id,
            "batch_id": rec.batch_id,
            "crop_name": rec.crop_name,
            "final_grade": rec.final_grade or "A",
            "dispatch_quantity_kg": rec.dispatch_quantity_kg,
            "sent_quantity_kg": rec.dispatch_quantity_kg,
            "origin_warehouse": rec.origin_warehouse,
            "destination_minor_warehouse": rec.destination_minor_warehouse,
            "truck_id": rec.truck_id,
            "truck_number": rec.truck_number,
            "driver_name": rec.driver_name,
            "driver_phone": rec.driver_phone,
            "departure_time": rec.departure_time,
            "expected_arrival": rec.expected_arrival,
            "actual_arrival": rec.actual_arrival,
            "status": rec.status,
            "delivery_status": rec.delivery_status or rec.status,
            "is_gps_active": bool(rec.is_gps_active),
            "current_location": rec.current_location if (rec.is_gps_active or rec.status not in ("Received", "Completed")) else (rec.destination_minor_warehouse or "Arrived at Destination"),
            "latitude": rec.latitude if rec.latitude is not None else 18.5204,
            "longitude": rec.longitude if rec.longitude is not None else 73.8567,
            "last_gps_update": rec.last_gps_update.strftime("%Y-%m-%d %H:%M:%S") if rec.last_gps_update else None,
            "google_maps_url": rec.google_maps_url,
            "notes": rec.notes or ""
        }

central_ai_service = CentralAIService()





