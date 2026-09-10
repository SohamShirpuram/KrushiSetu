from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from backend.database.connection import Base

class FarmerHarvestRecord(Base):
    """Harvest yields logged by farmers"""
    __tablename__ = "farmer_harvest_records"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(String(30), nullable=False, index=True) # Connected by unique Farmer ID
    crop_name = Column(String(50), nullable=False)
    season = Column(String(30), nullable=False)
    harvest_date = Column(String(20), nullable=False)
    actual_yield_kg = Column(Float, nullable=False)
    quality_condition = Column(String(50), default="GOOD") # EXCELLENT, GOOD, FAIR, DAMAGED
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "farmer_id": self.farmer_id,
            "crop_name": self.crop_name,
            "season": self.season,
            "harvest_date": self.harvest_date,
            "actual_yield_kg": self.actual_yield_kg,
            "quality_condition": self.quality_condition,
            "notes": self.notes,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
        }

class FarmerDeliveryRecord(Base):
    """Deliveries dispatched from farm to warehouse"""
    __tablename__ = "farmer_delivery_records"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(String(30), nullable=False, index=True)
    crop_name = Column(String(50), nullable=False)
    target_warehouse_name = Column(String(100), nullable=False) # e.g. Central Strategic Silo Pune
    vehicle_slip_number = Column(String(50), nullable=False)
    declared_weight_kg = Column(Float, nullable=False)
    weighbridge_net_weight_kg = Column(Float, nullable=True)
    batch_id = Column(String(50), nullable=True, index=True) # Linked after warehouse intake
    delivery_date = Column(String(20), nullable=False)
    status = Column(String(30), default="IN_TRANSIT") # IN_TRANSIT, RECEIVED_AT_WH, GRADED, STORED
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "farmer_id": self.farmer_id,
            "crop_name": self.crop_name,
            "target_warehouse_name": self.target_warehouse_name,
            "vehicle_slip_number": self.vehicle_slip_number,
            "declared_weight_kg": self.declared_weight_kg,
            "weighbridge_net_weight_kg": self.weighbridge_net_weight_kg,
            "batch_id": self.batch_id,
            "delivery_date": self.delivery_date,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
        }

class FarmerPaymentRecord(Base):
    """Payment settlement records for grain deliveries"""
    __tablename__ = "farmer_payment_records"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(String(30), nullable=False, index=True)
    batch_id = Column(String(50), nullable=False, index=True)
    crop_name = Column(String(50), nullable=False)
    net_weight_kg = Column(Float, nullable=False)
    confirmed_grade = Column(String(10), default="A")
    rate_per_kg = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    payment_status = Column(String(30), default="APPROVED") # PENDING, APPROVED, DISBURSED
    transaction_ref = Column(String(100), nullable=True)
    payment_date = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "farmer_id": self.farmer_id,
            "batch_id": self.batch_id,
            "crop_name": self.crop_name,
            "net_weight_kg": self.net_weight_kg,
            "confirmed_grade": self.confirmed_grade,
            "rate_per_kg": self.rate_per_kg,
            "total_amount": self.total_amount,
            "payment_status": self.payment_status,
            "transaction_ref": self.transaction_ref,
            "payment_date": self.payment_date,
            "created_at": self.created_at.strftime("%Y-%m-%d") if self.created_at else None,
        }

