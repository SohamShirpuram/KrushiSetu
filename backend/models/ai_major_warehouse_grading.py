from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, Index
from backend.database.connection import Base

class AIMajorWarehouseGradingRecord(Base):
    """
    KrushiSetu Central AI/ML Engine — Major Warehouse AI Crop Quality & Grading Record.
    
    DUAL-STORAGE ARCHITECTURE:
    1. Immutable AI Vision Predictions (ai_score, ai_grade, ai_confidence, ai_quality_factors, ai_warnings)
       are permanently preserved and never overwritten.
    2. Human Inspector Decisions (human_final_score, human_final_grade, reviewed_by, reviewed_at)
       are stored in distinct columns.
    3. If human changes AI grade or score, a mandatory correction reason (>= 5 chars) is enforced.
    4. Explicit segregation between 12 optical computer-vision parameters and physical measurements
       (moisture, certified scale weight).
    5. Permanent link to batch_id (KS-BATCH-XXXX) and farmer_id for end-to-end supply chain traceability.
    """
    __tablename__ = "ai_warehouse_grading_records"

    id = Column(Integer, primary_key=True, index=True)
    grading_code = Column(String(50), unique=True, nullable=False, index=True) # e.g. GRD-2026-0001
    batch_id = Column(String(50), nullable=False, index=True)                  # e.g. KS-BATCH-1001
    intake_id = Column(Integer, nullable=True, index=True)                     # Foreign key / link to major_warehouse_intakes.id
    
    # Traceability & Crop Metadata
    farmer_id = Column(String(30), nullable=False, index=True)                 # e.g. KS-FMR-1001
    farmer_name = Column(String(100), nullable=False)
    crop_name = Column(String(50), nullable=False, index=True)
    warehouse_id = Column(String(50), default="MWH-PUN-01", index=True)
    warehouse_name = Column(String(100), default="Pune Central Silo Complex")
    net_weight_kg = Column(Float, nullable=True)
    
    # Image reference (persisted to /uploads/grain_samples/)
    image_url = Column(String(255), nullable=True)

    # 1. AI Predictions (Permanent & Immutable)
    ai_score = Column(Float, nullable=False)                                   # 0 to 100
    ai_grade = Column(String(10), nullable=False)                              # A, B, C, REJECTED
    ai_confidence = Column(Float, default=0.92)                               # 0.0 to 1.0
    ai_quality_factors = Column(JSON, nullable=True)                           # 12 visual parameters + manual probe indicators
    ai_warnings = Column(JSON, nullable=True)                                  # Anomaly warnings list
    ai_reasoning = Column(Text, nullable=True)
    model_name = Column(String(100), default="Central AI - CropQualityVisionModel")
    model_version = Column(String(50), default="v1.0.0-prototype")
    prototype_disclaimer = Column(
        String(255),
        default="Prototype AI model — requires real crop image training dataset for production accuracy."
    )

    # 2. Human Inspector Review (Dual-Storage)
    # The AI prediction must NEVER become the final grade automatically
    review_status = Column(String(30), default="PENDING_REVIEW", nullable=False, index=True) # PENDING_REVIEW, APPROVED, CORRECTED
    human_final_score = Column(Float, nullable=True)                           # Human approved/corrected score (0-100)
    human_final_grade = Column(String(10), nullable=True)                      # Human approved/corrected grade (A, B, C, REJECTED)
    reviewed_by = Column(String(100), nullable=True)                           # Officer username
    reviewed_at = Column(DateTime, nullable=True)
    correction_reason = Column(Text, nullable=True)                            # Mandatory if review_status == CORRECTED (min 5 chars)
    human_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_wh_grading_batch_status", "batch_id", "review_status"),
        Index("idx_wh_grading_crop_grade", "crop_name", "ai_grade"),
        Index("idx_wh_grading_farmer", "farmer_id"),
    )

    @property
    def effective_final_grade(self) -> str:
        """Returns confirmed human final grade, or fallback to AI suggested grade if approved."""
        return self.human_final_grade or self.ai_grade

    @property
    def effective_final_score(self) -> float:
        """Returns confirmed human final score, or fallback to AI predicted score."""
        return self.human_final_score if self.human_final_score is not None else self.ai_score

    def to_dict(self):
        return {
            "id": self.id,
            "grading_code": self.grading_code,
            "batch_id": self.batch_id,
            "intake_id": self.intake_id,
            "farmer_id": self.farmer_id,
            "farmer_name": self.farmer_name,
            "crop_name": self.crop_name,
            "warehouse_id": self.warehouse_id,
            "warehouse_name": self.warehouse_name,
            "net_weight_kg": self.net_weight_kg,
            "image_url": self.image_url,
            "ai_score": self.ai_score,
            "ai_grade": self.ai_grade,
            "ai_confidence": self.ai_confidence,
            "ai_quality_factors": self.ai_quality_factors or {},
            "ai_warnings": self.ai_warnings or [],
            "ai_reasoning": self.ai_reasoning,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "prototype_disclaimer": self.prototype_disclaimer,
            "review_status": self.review_status,
            "human_final_score": self.human_final_score,
            "human_final_grade": self.human_final_grade,
            "effective_final_grade": self.effective_final_grade,
            "effective_final_score": self.effective_final_score,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "correction_reason": self.correction_reason,
            "human_notes": self.human_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

