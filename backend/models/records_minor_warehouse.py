from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from backend.database.connection import Base

class MinorWarehouseInward(Base):
    """Inward grain receipts transferred from Major Strategic Warehouse"""
    __tablename__ = "minor_wh_inward_records"

    id = Column(Integer, primary_key=True, index=True)
    dispatch_id = Column(String(50), nullable=False, index=True)
    batch_id = Column(String(50), nullable=False, index=True)
    crop_name = Column(String(50), nullable=False)
    source_major_wh = Column(String(100), default="Pune Central Silo")
    truck_number = Column(String(30), nullable=False)
    driver_name = Column(String(100), nullable=False)
    sent_quantity_kg = Column(Float, nullable=True)
    received_quantity_kg = Column(Float, nullable=False)
    difference_kg = Column(Float, default=0.0)
    dispatch_time = Column(String(30), default="10:30 AM")
    arrival_time = Column(String(30), default="02:15 PM")
    discrepancy_reason = Column(String(255), nullable=True)
    intake_date = Column(String(20), nullable=False)
    verification_status = Column(String(30), default="VERIFIED_IN_STOCK") # VERIFIED_IN_STOCK, WEIGHT_MISMATCH
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        sent_qty = self.sent_quantity_kg if self.sent_quantity_kg is not None else self.received_quantity_kg
        diff = self.difference_kg if self.difference_kg is not None else round(sent_qty - self.received_quantity_kg, 2)
        return {
            "id": self.id,
            "dispatch_id": self.dispatch_id,
            "batch_id": self.batch_id,
            "crop_name": self.crop_name,
            "source_major_wh": self.source_major_wh,
            "truck_number": self.truck_number,
            "driver_name": self.driver_name,
            "sent_quantity_kg": sent_qty,
            "received_quantity_kg": self.received_quantity_kg,
            "difference_kg": diff,
            "dispatch_time": self.dispatch_time or "10:30 AM",
            "arrival_time": self.arrival_time or "02:15 PM",
            "discrepancy_reason": self.discrepancy_reason or ("In transit spillage tolerance" if diff != 0 else "Exact Match"),
            "intake_date": self.intake_date,
            "verification_status": self.verification_status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
        }

class MinorWarehouseStock(Base):
    """Current stock on hand at Minor / APMC Transit Godown"""
    __tablename__ = "minor_wh_stock"

    id = Column(Integer, primary_key=True, index=True)
    crop_name = Column(String(50), nullable=False, index=True)
    batch_id = Column(String(50), nullable=False, index=True)
    current_stock_kg = Column(Float, nullable=False)
    warehouse_location = Column(String(100), default="Baramati APMC Godown No. 3")
    last_replenished = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "crop_name": self.crop_name,
            "batch_id": self.batch_id,
            "current_stock_kg": self.current_stock_kg,
            "warehouse_location": self.warehouse_location,
            "last_replenished": self.last_replenished,
        }

class MinorWarehouseDemand(Base):
    """Regional block/cluster level demand data"""
    __tablename__ = "minor_wh_regional_demand"

    id = Column(Integer, primary_key=True, index=True)
    region_name = Column(String(100), nullable=False, index=True) # e.g. Baramati Cluster
    crop_name = Column(String(50), nullable=False)
    monthly_demand_kg = Column(Float, nullable=False)
    urgency_level = Column(String(30), default="NORMAL") # LOW, NORMAL, CRITICAL
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "region_name": self.region_name,
            "crop_name": self.crop_name,
            "monthly_demand_kg": self.monthly_demand_kg,
            "urgency_level": self.urgency_level,
            "notes": self.notes,
        }

class MinorWarehouseDistribution(Base):
    """Local distribution dispatches from Minor Godown to distribution outlets"""
    __tablename__ = "minor_wh_distributions"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(50), nullable=False, index=True)
    crop_name = Column(String(50), nullable=False)
    recipient_center = Column(String(100), nullable=False) # e.g. Shirsuphal FPS #12
    quantity_kg = Column(Float, nullable=False)
    receipt_no = Column(String(50), unique=True, nullable=False)
    distribution_date = Column(String(20), nullable=False)
    status = Column(String(30), default="COMPLETED")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "crop_name": self.crop_name,
            "recipient_center": self.recipient_center,
            "quantity_kg": self.quantity_kg,
            "receipt_no": self.receipt_no,
            "distribution_date": self.distribution_date,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
        }

class MinorWarehouseRestock(Base):
    """Restock requests sent upwards to Major Warehouse"""
    __tablename__ = "minor_wh_restock_requests"

    id = Column(Integer, primary_key=True, index=True)
    crop_name = Column(String(50), nullable=False)
    requested_quantity_kg = Column(Float, nullable=False)
    urgency = Column(String(30), default="HIGH") # NORMAL, HIGH, EMERGENCY
    request_date = Column(String(20), nullable=False)
    status = Column(String(30), default="PENDING_MAJOR_DISPATCH") # PENDING_MAJOR_DISPATCH, DISPATCHED, FULFILLED
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "crop_name": self.crop_name,
            "requested_quantity_kg": self.requested_quantity_kg,
            "urgency": self.urgency,
            "request_date": self.request_date,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
        }

