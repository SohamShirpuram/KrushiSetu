from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from backend.database.connection import Base

class GramPanchayat(Base):
    __tablename__ = "gp_master"

    id = Column(Integer, primary_key=True, index=True)
    gp_code = Column(String(30), unique=True, nullable=False, index=True)
    gp_name = Column(String(100), nullable=False)
    panchayat_samiti_name = Column(String(100), nullable=False)
    sarpanch_name = Column(String(100), nullable=False)
    secretary_name = Column(String(100), nullable=False)
    office_phone = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "gp_code": self.gp_code,
            "gp_name": self.gp_name,
            "panchayat_samiti_name": self.panchayat_samiti_name,
            "sarpanch_name": self.sarpanch_name,
            "secretary_name": self.secretary_name,
            "office_phone": self.office_phone,
        }

class FarmerRegistry(Base):
    """Official farmer master registry maintained by Gram Panchayat"""
    __tablename__ = "gp_farmer_registry"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(String(30), unique=True, nullable=False, index=True) # e.g. KS-FMR-1001
    farmer_name = Column(String(100), nullable=False)
    contact_phone = Column(String(20), nullable=True)
    aadhaar_masked = Column(String(20), nullable=True)
    gp_name = Column(String(100), nullable=False, index=True)
    panchayat_samiti_name = Column(String(100), default="Baramati Block Panchayat Samiti")
    district = Column(String(100), default="Pune")
    village_name = Column(String(100), nullable=False)
    total_land_acres = Column(Float, default=0.0)
    bank_account_masked = Column(String(30), nullable=True)
    soil_health_card_no = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "farmer_id": self.farmer_id,
            "farmer_name": self.farmer_name,
            "contact_phone": self.contact_phone,
            "aadhaar_masked": self.aadhaar_masked or "XXXX-XXXX-8921",
            "gp_name": self.gp_name,
            "panchayat_samiti_name": self.panchayat_samiti_name,
            "district": self.district,
            "village_name": self.village_name,
            "total_land_acres": self.total_land_acres,
            "bank_account_masked": self.bank_account_masked or "SBIN000XXXX4412",
            "soil_health_card_no": self.soil_health_card_no or f"SHC-{self.farmer_id}",
            "created_at": self.created_at.strftime("%Y-%m-%d") if self.created_at else None,
        }

class FarmerLandRecord(Base):
    """Farmer Land parcel details maintained by Gram Panchayat"""
    __tablename__ = "gp_farmer_land_records"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(String(30), nullable=False, index=True) # Unique Farmer ID e.g. KS-FMR-1001
    farmer_name = Column(String(100), nullable=False)
    survey_number = Column(String(50), nullable=False) # Gat / Survey No
    village_name = Column(String(100), nullable=False)
    land_area_acres = Column(Float, nullable=False)
    soil_type = Column(String(50), nullable=False)
    irrigation_source = Column(String(50), default="CANAL") # CANAL, BOREWELL, WELL, RAINFED
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "farmer_id": self.farmer_id,
            "farmer_name": self.farmer_name,
            "survey_number": self.survey_number,
            "village_name": self.village_name,
            "land_area_acres": self.land_area_acres,
            "soil_type": self.soil_type,
            "irrigation_source": self.irrigation_source,
            "created_at": self.created_at.strftime("%Y-%m-%d") if self.created_at else None,
        }

class SoilTestRecord(Base):
    """Laboratory soil test metrics & document attachments for farmer plots"""
    __tablename__ = "gp_soil_tests"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(String(30), nullable=False, index=True) # Unique Farmer ID
    survey_number = Column(String(50), nullable=False)
    sample_date = Column(String(20), nullable=False)
    ph_level = Column(Float, nullable=False)
    nitrogen_kg_ha = Column(Float, nullable=False)
    phosphorus_kg_ha = Column(Float, nullable=False)
    potassium_kg_ha = Column(Float, nullable=False)
    organic_carbon_pct = Column(Float, nullable=False)
    soil_test_doc_url = Column(String(255), nullable=True) # e.g. /uploads/soil_report_1001.jpg
    testing_lab = Column(String(100), default="District Agri Soil Lab")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "farmer_id": self.farmer_id,
            "survey_number": self.survey_number,
            "sample_date": self.sample_date,
            "ph_level": self.ph_level,
            "nitrogen_kg_ha": self.nitrogen_kg_ha,
            "phosphorus_kg_ha": self.phosphorus_kg_ha,
            "potassium_kg_ha": self.potassium_kg_ha,
            "organic_carbon_pct": self.organic_carbon_pct,
            "soil_test_doc_url": self.soil_test_doc_url or "soil_test_sample_card.jpg",
            "testing_lab": self.testing_lab,
            "created_at": self.created_at.strftime("%Y-%m-%d") if self.created_at else None,
        }

class GPCropAssignment(Base):
    """Crop target assignments issued to specific farmers"""
    __tablename__ = "gp_crop_assignments"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(String(30), nullable=False, index=True)
    farmer_name = Column(String(100), nullable=False)
    crop_name = Column(String(50), nullable=False)
    season = Column(String(30), nullable=False)
    assigned_acres = Column(Float, nullable=False)
    required_quantity_quintals = Column(Float, nullable=False)
    status = Column(String(30), default="AI_GENERATED") # AI_GENERATED, UNDER_REVIEW, EDITED_BY_HUMAN, APPROVED, ASSIGNED, SOWN, HARVESTING, DELIVERED

    # AI Recommendation (Preserved)
    ai_recommended_acres = Column(Float, nullable=True)
    ai_recommended_quintals = Column(Float, nullable=True)
    ai_rationale = Column(Text, nullable=True)
    ai_confidence_score = Column(Float, default=0.94)

    # Human Final Review
    human_final_acres = Column(Float, nullable=True)
    human_final_quintals = Column(Float, nullable=True)
    finalized_by = Column(String(50), nullable=True)
    finalized_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "farmer_id": self.farmer_id,
            "farmer_name": self.farmer_name,
            "crop_name": self.crop_name,
            "season": self.season,
            "assigned_acres": self.assigned_acres,
            "required_quantity_quintals": self.required_quantity_quintals,
            "status": self.status,
            "ai_recommended_acres": self.ai_recommended_acres or self.assigned_acres,
            "ai_recommended_quintals": self.ai_recommended_quintals or self.required_quantity_quintals,
            "human_final_acres": self.human_final_acres,
            "human_final_quintals": self.human_final_quintals,
            "ai_rationale": self.ai_rationale,
            "ai_confidence_score": self.ai_confidence_score,
            "finalized_by": self.finalized_by,
            "finalized_at": self.finalized_at.strftime("%Y-%m-%d %H:%M") if self.finalized_at else None,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
        }

