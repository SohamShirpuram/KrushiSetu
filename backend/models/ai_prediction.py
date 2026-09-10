from datetime import datetime
import json
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from backend.database.connection import Base

class AIPredictionRecord(Base):
    """
    CENTRAL AI PREDICTION STORAGE MODEL:
    Stores every AI prediction separately and immutably.
    Original AI recommendation values are never overwritten.
    Human reviews (Approvals & Corrections) are stored in dedicated columns
    alongside officer attribution, timestamp, and mandatory correction reasons.
    """
    __tablename__ = "ai_prediction_records"

    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(String(50), unique=True, index=True, nullable=False)
    module_name = Column(String(60), default="crop_requirement_recommendation", index=True)
    model_name = Column(String(60), default="ExplainableCropRequirementModel")
    model_version = Column(String(30), default="v1.0.0-prototype")
    
    # Authorized Input Data Reference (JSON snapshot of real database values used)
    input_data_reference = Column(Text, nullable=False)

    # Immutable AI Recommendations
    ai_recommended_crop = Column(String(60), nullable=False)
    ai_recommended_quantity = Column(Float, nullable=False)
    ai_priority = Column(String(20), nullable=False)
    ai_reasoning = Column(Text, nullable=False)
    ai_factors = Column(Text, nullable=False) # JSON breakdown of key contributing factors
    ai_confidence = Column(Float, default=0.92)
    suitable_region = Column(String(100), default="Baramati Block Panchayat Samiti")
    generated_at = Column(DateTime, default=datetime.utcnow)

    # Human Review Lifecycle (PENDING_REVIEW, APPROVED, CORRECTED)
    review_status = Column(String(30), default="PENDING_REVIEW", index=True)
    human_final_crop = Column(String(60), nullable=True)
    human_final_quantity = Column(Float, nullable=True)
    human_final_priority = Column(String(20), nullable=True)
    reviewed_by = Column(String(60), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    correction_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        factors = {}
        try:
            factors = json.loads(self.ai_factors) if self.ai_factors else {}
        except Exception:
            factors = {"raw": self.ai_factors}

        input_data = {}
        try:
            input_data = json.loads(self.input_data_reference) if self.input_data_reference else {}
        except Exception:
            input_data = {"raw": self.input_data_reference}

        return {
            "id": self.id,
            "prediction_id": self.prediction_id,
            "module_name": self.module_name,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "input_data_reference": input_data,
            "ai_recommended_crop": self.ai_recommended_crop,
            "ai_recommended_quantity": self.ai_recommended_quantity,
            "ai_priority": self.ai_priority,
            "ai_reasoning": self.ai_reasoning,
            "ai_factors": factors,
            "ai_confidence": self.ai_confidence,
            "suitable_region": self.suitable_region,
            "generated_at": self.generated_at.strftime("%Y-%m-%d %H:%M") if self.generated_at else None,
            "review_status": self.review_status,
            "human_final_crop": self.human_final_crop,
            "human_final_quantity": self.human_final_quantity,
            "human_final_priority": self.human_final_priority,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.strftime("%Y-%m-%d %H:%M") if self.reviewed_at else None,
            "correction_reason": self.correction_reason,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
        }

