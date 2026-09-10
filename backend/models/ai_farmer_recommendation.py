from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, Index
from backend.database.connection import Base

class AIFarmerRecommendationRecord(Base):
    """
    KrushiSetu Central AI/ML Engine — Gram Panchayat to Farmer Crop Recommendation Record.
    Enforces DUAL-STORAGE architecture:
    1. Immutable AI Recommendations (ai_recommended_*) permanently preserved.
    2. Human Gram Panchayat review decisions (human_final_*) stored separately.
    3. Mandatory correction reason whenever human modifies AI recommendation.
    4. Linked directly to farmer's parcel, laboratory soil tests, and certified Soil Health Card.
    """
    __tablename__ = "ai_farmer_recommendation_records"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_code = Column(String(50), unique=True, nullable=False, index=True) # e.g. REC-FMR-2026-0001
    batch_code = Column(String(50), nullable=False, index=True)                       # e.g. BATCH-FRA-2026-001
    gp_allocation_id = Column(Integer, nullable=True, index=True)                     # Parent AIGPAllocationRecord ID
    panchayat_samiti_name = Column(String(100), nullable=False)
    gp_code = Column(String(30), nullable=False, index=True)
    gp_name = Column(String(100), nullable=False, index=True)

    # Farmer Master & Parcel Info
    farmer_id = Column(String(30), nullable=False, index=True)                        # e.g. KS-FMR-1001
    farmer_name = Column(String(100), nullable=False)
    survey_number = Column(String(50), nullable=True)
    village_name = Column(String(100), nullable=True)
    crop_name = Column(String(50), nullable=False)
    season = Column(String(30), nullable=False)
    target_year = Column(Integer, default=2026)
    farmer_total_land_acres = Column(Float, default=0.0)
    farmer_available_land_acres = Column(Float, default=0.0)

    # AI Recommendation (Permanent & Immutable)
    ai_recommended_area_acres = Column(Float, nullable=False)
    ai_recommended_quantity_quintals = Column(Float, nullable=False)
    ai_suitability = Column(String(50), default="HIGH")                               # HIGH, MEDIUM, LOW
    ai_priority = Column(String(50), default="HIGH")                                  # CRITICAL, HIGH, NORMAL
    ai_reasoning = Column(Text, nullable=True)
    ai_confidence_score = Column(Float, default=0.94)
    model_name = Column(String(100), default="Central AI - GPToFarmerRecommendationModel")
    model_version = Column(String(50), default="v1.0.0-prototype")
    ai_factors = Column(JSON, nullable=True)

    # Human Gram Panchayat Review (Dual Storage)
    review_status = Column(String(30), default="PENDING_REVIEW", nullable=False, index=True) # PENDING_REVIEW, APPROVED, CORRECTED
    human_final_crop = Column(String(50), nullable=True)
    human_final_area_acres = Column(Float, nullable=True)
    human_final_quantity_quintals = Column(Float, nullable=True)
    human_final_priority = Column(String(50), nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    correction_reason = Column(Text, nullable=True) # Mandatory if modified from AI recommendation
    human_review_notes = Column(Text, nullable=True)

    # Audit & Timestamp Fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_farmer_rec_batch_status", "batch_code", "review_status"),
        Index("idx_farmer_rec_gp_crop", "gp_name", "crop_name"),
        Index("idx_farmer_rec_farmer_crop", "farmer_id", "crop_name"),
    )

    @property
    def soil_report_url(self):
        f = self.ai_factors or {}
        return f.get("soil_report_url") or f.get("soil_test_doc_url") or "/uploads/soil_reports/soil_health_card_KS-FMR-1001.svg"

    @property
    def soil_ph(self):
        f = self.ai_factors or {}
        return f.get("soil_ph") or f.get("ph_level")

    @property
    def suitability_score(self):
        f = self.ai_factors or {}
        return f.get("composite_suitability_score") or f.get("suitability_score") or self.ai_confidence_score

    def to_dict(self):
        factors = self.ai_factors or {}
        doc_url = factors.get("soil_report_url") or factors.get("soil_test_doc_url") or "/uploads/soil_reports/soil_health_card_KS-FMR-1001.svg"
        ph = factors.get("soil_ph") or factors.get("ph_level")
        suit_score = factors.get("composite_suitability_score") or factors.get("suitability_score") or self.ai_confidence_score

        return {
            "id": self.id,
            "recommendation_code": self.recommendation_code,
            "batch_code": self.batch_code,
            "gp_allocation_id": self.gp_allocation_id,
            "panchayat_samiti_name": self.panchayat_samiti_name,
            "gp_code": self.gp_code,
            "gp_name": self.gp_name,
            "farmer_id": self.farmer_id,
            "farmer_name": self.farmer_name,
            "survey_number": self.survey_number,
            "village_name": self.village_name,
            "crop_name": self.crop_name,
            "season": self.season,
            "target_year": self.target_year,
            "farmer_total_land_acres": self.farmer_total_land_acres,
            "farmer_available_land_acres": self.farmer_available_land_acres,
            
            # AI Recommendation (Preserved)
            "ai_recommended_area_acres": self.ai_recommended_area_acres,
            "ai_recommended_quantity_quintals": self.ai_recommended_quantity_quintals,
            "ai_suitability": self.ai_suitability,
            "ai_priority": self.ai_priority,
            "ai_reasoning": self.ai_reasoning,
            "ai_confidence_score": self.ai_confidence_score,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "ai_factors": factors,

            # Flattened fields for UI & API response
            "soil_report_url": doc_url,
            "soil_ph": ph,
            "soil_type": factors.get("soil_type"),
            "irrigation_source": factors.get("irrigation_source"),
            "nitrogen_kg_ha": factors.get("nitrogen_kg_ha"),
            "organic_carbon_pct": factors.get("organic_carbon_pct"),
            "suitability_score": suit_score,
            "ai_rationale": factors.get("ai_rationale") or self.ai_reasoning,
            "gp_approved_quota_mt": factors.get("gp_approved_quota_mt"),
            
            # Human Review (Dual Storage)
            "review_status": self.review_status,
            "human_final_crop": self.human_final_crop,
            "human_final_area_acres": self.human_final_area_acres,
            "human_final_quantity_quintals": self.human_final_quantity_quintals,
            "human_final_priority": self.human_final_priority,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "correction_reason": self.correction_reason,
            "human_review_notes": self.human_review_notes,
            
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
