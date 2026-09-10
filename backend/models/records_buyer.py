from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from backend.database.connection import Base

class BulkBuyerRegistry(Base):
    """Authorized Bulk Buyer Registry"""
    __tablename__ = "bulk_buyer_registry"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(String(30), unique=True, nullable=False, index=True) # e.g. KS-BYR-5001
    company_name = Column(String(150), nullable=False)
    business_type = Column(String(50), nullable=False) # Agro Processor, Exporter, Retail Distributor
    gst_number = Column(String(30), nullable=True)
    contact_person = Column(String(100), nullable=False)
    contact_phone = Column(String(20), nullable=False)
    official_email = Column(String(100), nullable=False)
    status = Column(String(30), default="VERIFIED_BUYER")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "buyer_id": self.buyer_id,
            "company_name": self.company_name,
            "business_type": self.business_type,
            "gst_number": self.gst_number,
            "contact_person": self.contact_person,
            "contact_phone": self.contact_phone,
            "official_email": self.official_email,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d") if self.created_at else None,
        }

class BulkBuyerEntry(Base):
    """Procurement demand and grain order inquiries submitted by Bulk Buyers"""
    __tablename__ = "bulk_buyer_entries"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(String(30), nullable=False, index=True) # Linked via unique Buyer ID
    crop_name = Column(String(50), nullable=False, index=True)
    required_quantity_mt = Column(Float, nullable=False)
    target_grade = Column(String(10), default="A") # "A", "B"
    max_price_offer_per_quintal = Column(Float, nullable=False)
    delivery_hub = Column(String(100), default="Pune Central Logistics Hub")
    required_by_date = Column(String(20), nullable=False)
    status = Column(String(30), default="ENTRY_RECORDED") # ENTRY_RECORDED, MATCHED, FULFILLED
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "buyer_id": self.buyer_id,
            "crop_name": self.crop_name,
            "required_quantity_mt": self.required_quantity_mt,
            "target_grade": self.target_grade,
            "max_price_offer_per_quintal": self.max_price_offer_per_quintal,
            "delivery_hub": self.delivery_hub,
            "required_by_date": self.required_by_date,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
        }

