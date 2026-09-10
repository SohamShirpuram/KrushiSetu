from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from backend.database.connection import Base

class PanchayatSamiti(Base):
    __tablename__ = "ps_master"

    id = Column(Integer, primary_key=True, index=True)
    ps_code = Column(String(30), unique=True, nullable=False, index=True)
    ps_name = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    block_officer = Column(String(100), nullable=False)
    contact_phone = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "ps_code": self.ps_code,
            "ps_name": self.ps_name,
            "district": self.district,
            "block_officer": self.block_officer,
            "contact_phone": self.contact_phone,
        }

class PSGPRegistry(Base):
    """GPs under the Panchayat Samiti and their land/area data"""
    __tablename__ = "ps_gp_registry"

    id = Column(Integer, primary_key=True, index=True)
    gp_code = Column(String(30), unique=True, nullable=False, index=True)
    gp_name = Column(String(100), nullable=False)
    panchayat_samiti_name = Column(String(100), nullable=False, index=True)
    district = Column(String(100), default="Pune")
    village_location = Column(String(150), nullable=True)
    total_area_hectares = Column(Float, nullable=False)
    cultivable_area_hectares = Column(Float, nullable=False)
    active_farmers_count = Column(Integer, default=0)
    sarpanch_name = Column(String(100), nullable=True)
    office_phone = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "gp_code": self.gp_code,
            "gp_name": self.gp_name,
            "panchayat_samiti_name": self.panchayat_samiti_name,
            "district": self.district or "Pune",
            "village_location": self.village_location or self.gp_name,
            "total_area_hectares": self.total_area_hectares,
            "cultivable_area_hectares": self.cultivable_area_hectares,
            "active_farmers_count": self.active_farmers_count,
            "sarpanch_name": self.sarpanch_name or "Official Sarpanch",
            "office_phone": self.office_phone or "+91 2112 255100",
            "created_at": self.created_at.strftime("%Y-%m-%d") if self.created_at else None,
        }

class PSSoilSuitability(Base):
    """Soil and crop suitability data across Gram Panchayats"""
    __tablename__ = "ps_soil_suitability"

    id = Column(Integer, primary_key=True, index=True)
    gp_name = Column(String(100), nullable=False, index=True)
    soil_type = Column(String(50), nullable=False) # Black Cotton Soil, Red Loamy, Sandy Loam
    primary_crops = Column(String(150), nullable=False) # Wheat, Soybean, Gram
    irrigation_coverage_pct = Column(Float, nullable=False)
    organic_matter_rating = Column(String(30), default="MEDIUM") # LOW, MEDIUM, HIGH
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "gp_name": self.gp_name,
            "soil_type": self.soil_type,
            "primary_crops": self.primary_crops,
            "irrigation_coverage_pct": self.irrigation_coverage_pct,
            "organic_matter_rating": self.organic_matter_rating,
        }

class PSGPAllocation(Base):
    """Crop allocation assigned from PS down to Gram Panchayats"""
    __tablename__ = "ps_gp_allocations"

    id = Column(Integer, primary_key=True, index=True)
    panchayat_samiti_name = Column(String(100), nullable=False)
    gp_name = Column(String(100), nullable=False, index=True)
    crop_name = Column(String(50), nullable=False)
    allocated_quantity_mt = Column(Float, nullable=False)
    season = Column(String(30), nullable=False)
    status = Column(String(30), default="AI_GENERATED") # AI_GENERATED, UNDER_REVIEW, EDITED_BY_HUMAN, APPROVED, ASSIGNED

    # AI Recommendation (Preserved)
    ai_recommended_quantity_mt = Column(Float, nullable=True)
    ai_rationale = Column(Text, nullable=True)
    ai_confidence_score = Column(Float, default=0.94)

    # Human Final Review
    human_final_quantity_mt = Column(Float, nullable=True)
    finalized_by = Column(String(50), nullable=True)
    finalized_at = Column(DateTime, nullable=True)
    human_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "panchayat_samiti_name": self.panchayat_samiti_name,
            "gp_name": self.gp_name,
            "crop_name": self.crop_name,
            "allocated_quantity_mt": self.allocated_quantity_mt,
            "season": self.season,
            "status": self.status,
            "ai_recommended_quantity_mt": self.ai_recommended_quantity_mt or self.allocated_quantity_mt,
            "human_final_quantity_mt": self.human_final_quantity_mt,
            "ai_rationale": self.ai_rationale,
            "ai_confidence_score": self.ai_confidence_score,
            "finalized_by": self.finalized_by,
            "finalized_at": self.finalized_at.strftime("%Y-%m-%d %H:%M") if self.finalized_at else None,
            "human_notes": self.human_notes,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
        }

