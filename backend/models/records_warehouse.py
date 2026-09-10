from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean
from backend.database.connection import Base

class MajorWarehouseIntake(Base):
    """
    Intake Record at Major Strategic Warehouse.
    Connects:
    - Farmer ID
    - Batch ID (KS-BATCH-XXXX)
    - Dual Grading: AI Predicted Score/Grade AND Human Final Score/Grade
    - Storage location & Silo Bay
    """
    __tablename__ = "major_warehouse_intakes"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(50), unique=True, nullable=False, index=True) # e.g. KS-BATCH-1001
    farmer_id = Column(String(30), nullable=False, index=True)            # Links to Farmer
    farmer_name = Column(String(100), nullable=False)
    crop_name = Column(String(50), nullable=False, index=True)
    
    # Weight metrics (kg)
    gross_weight_kg = Column(Float, nullable=False)
    tare_weight_kg = Column(Float, nullable=False)
    net_weight_kg = Column(Float, nullable=False)

    # DUAL GRADING: AI Prediction vs Human Final Decision
    ai_predicted_score = Column(Float, nullable=True)                      # Central AI Computer Vision Output
    ai_predicted_grade = Column(String(10), nullable=True)                 # Grade A, B, C, REJECTED
    human_final_score = Column(Float, nullable=True)                       # Final confirmed score
    human_final_grade = Column(String(10), nullable=True)                  # Final confirmed grade
    review_status = Column(String(30), default="PENDING")                  # PENDING, CONFIRMED, REJECTED, OVERRIDDEN
    reviewed_by = Column(String(100), nullable=True)                       # Inspector Username
    reviewed_at = Column(DateTime, nullable=True)

    crop_image_url = Column(String(255), nullable=True)                    # Proof / Camera snapshot
    grading_notes = Column(Text, nullable=True)

    # Storage allocation details
    storage_silo_bay = Column(String(50), default="SILO-A-01")             # Silo Bay Identifier
    storage_temp_celsius = Column(Float, default=21.5)
    storage_humidity_pct = Column(Float, default=55.0)
    intake_status = Column(String(30), default="RECEIVED")                 # RECEIVED, GRADED, STORED, DISPATCHED

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "farmer_id": self.farmer_id,
            "farmer_name": self.farmer_name,
            "crop_name": self.crop_name,
            "gross_weight_kg": self.gross_weight_kg,
            "tare_weight_kg": self.tare_weight_kg,
            "net_weight_kg": self.net_weight_kg,
            "ai_predicted_score": self.ai_predicted_score,
            "ai_predicted_grade": self.ai_predicted_grade,
            "human_final_score": self.human_final_score,
            "human_final_grade": self.human_final_grade,
            "review_status": self.review_status,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.strftime("%Y-%m-%d %H:%M") if self.reviewed_at else None,
            "crop_image_url": self.crop_image_url,
            "grading_notes": self.grading_notes,
            "storage_silo_bay": self.storage_silo_bay,
            "storage_temp_celsius": self.storage_temp_celsius,
            "storage_humidity_pct": self.storage_humidity_pct,
            "intake_status": self.intake_status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
        }

class MajorWarehouseDispatch(Base):
    """Outward Dispatches from Major Silo Hub to Minor/Sub-district Warehouses"""
    __tablename__ = "major_warehouse_dispatches"

    id = Column(Integer, primary_key=True, index=True)
    dispatch_id = Column(String(50), unique=True, nullable=False, index=True) # e.g. KS-DSP-7001
    batch_id = Column(String(50), nullable=False, index=True)
    crop_name = Column(String(50), nullable=False)
    final_grade = Column(String(10), default="A", nullable=False)             # Task 5 confirmed grade
    dispatch_quantity_kg = Column(Float, nullable=False)
    origin_warehouse = Column(String(100), default="Pune Central Major Warehouse")
    origin_warehouse_id = Column(String(50), default="MWH-PUN-01")
    destination_minor_warehouse = Column(String(100), nullable=False)         # e.g. Baramati APMC Godown No. 3
    destination_minor_warehouse_id = Column(String(50), default="MIN-BMT-01")
    truck_id = Column(String(50), default="TRK-001", nullable=True)
    truck_number = Column(String(30), nullable=False)                         # e.g. MH-12-Q-4521
    driver_id = Column(String(50), default="DRV-001", nullable=True)
    driver_name = Column(String(100), nullable=False)
    driver_phone = Column(String(20), nullable=True)
    dispatch_date = Column(String(20), nullable=False)
    departure_time = Column(String(30), default="10:30 AM")
    expected_arrival = Column(String(30), nullable=True)                      # ETA
    actual_arrival = Column(String(30), nullable=True)
    status = Column(String(30), default="Dispatched")                         # Pending, Dispatched, In Transit, Arrived, Received, Completed, Discrepancy
    delivery_status = Column(String(30), default="In Transit")

    # Truck GPS Tracking Fields
    current_location = Column(String(150), default="Pune Hub Outward Logistics Gate")
    latitude = Column(Float, default=18.5204)
    longitude = Column(Float, default=73.8567)
    last_gps_update = Column(DateTime, default=datetime.utcnow)
    is_gps_active = Column(Boolean, default=True)                             # Active duty only during transit
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def google_maps_url(self) -> Optional[str]:
        if self.latitude is not None and self.longitude is not None:
            return f"https://www.google.com/maps/search/?api=1&query={self.latitude},{self.longitude}"
        return None

    def to_dict(self):
        return {
            "id": self.id,
            "dispatch_id": self.dispatch_id,
            "batch_id": self.batch_id,
            "crop_name": self.crop_name,
            "final_grade": self.final_grade or "A",
            "dispatch_quantity_kg": self.dispatch_quantity_kg,
            "sent_quantity_kg": self.dispatch_quantity_kg,
            "origin_warehouse": self.origin_warehouse,
            "origin_warehouse_id": self.origin_warehouse_id or "MWH-PUN-01",
            "destination_minor_warehouse": self.destination_minor_warehouse,
            "destination_minor_warehouse_id": self.destination_minor_warehouse_id or "MIN-BMT-01",
            "truck_id": self.truck_id or "TRK-001",
            "truck_number": self.truck_number,
            "driver_id": self.driver_id or "DRV-001",
            "driver_name": self.driver_name,
            "driver_phone": self.driver_phone or "",
            "dispatch_date": self.dispatch_date,
            "departure_time": self.departure_time or "10:30 AM",
            "expected_arrival": self.expected_arrival or "02:30 PM",
            "actual_arrival": self.actual_arrival or "",
            "status": self.status,
            "delivery_status": self.delivery_status or self.status,
            "current_location": self.current_location if self.is_gps_active or self.status not in ("Received", "Completed") else (self.destination_minor_warehouse or "Arrived at Destination"),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "last_gps_update": self.last_gps_update.strftime("%Y-%m-%d %H:%M") if self.last_gps_update else None,
            "is_gps_active": bool(self.is_gps_active),
            "google_maps_url": self.google_maps_url,
            "notes": self.notes or "",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M") if self.updated_at else None,
        }

class TruckRegistry(Base):
    """Transport fleet vehicle and driver registry"""
    __tablename__ = "trucks_registry"

    id = Column(Integer, primary_key=True, index=True)
    truck_id = Column(String(50), unique=True, nullable=False, index=True) # e.g. TRK-001
    vehicle_number = Column(String(30), unique=True, nullable=False, index=True) # e.g. MH-12-Q-4521
    vehicle_type = Column(String(50), default="16-Wheeler Heavy Grain Carrier")
    capacity_mt = Column(Float, default=25.0)
    driver_name = Column(String(100), nullable=False)
    driver_phone = Column(String(20), nullable=True)
    driver_id = Column(String(50), default="DRV-001", nullable=True)
    current_status = Column(String(30), default="AVAILABLE") # AVAILABLE, ASSIGNED, IN_TRANSIT, MAINTENANCE, OFF_DUTY
    current_dispatch_id = Column(String(50), nullable=True)
    origin_base = Column(String(100), default="Pune Central Major Silo Hub")
    destination = Column(String(100), nullable=True)
    last_location = Column(String(150), default="Pune Hub Logistics Yard")
    last_latitude = Column(Float, default=18.5204)
    last_longitude = Column(Float, default=73.8567)
    last_gps_update = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "truck_id": self.truck_id,
            "vehicle_number": self.vehicle_number,
            "vehicle_type": self.vehicle_type,
            "capacity_mt": self.capacity_mt,
            "driver_name": self.driver_name,
            "driver_phone": self.driver_phone or "",
            "driver_id": self.driver_id or "",
            "current_status": self.current_status,
            "current_dispatch_id": self.current_dispatch_id or "",
            "origin_base": self.origin_base,
            "destination": self.destination or "",
            "last_location": self.last_location,
            "last_latitude": self.last_latitude,
            "last_longitude": self.last_longitude,
            "last_gps_update": self.last_gps_update.strftime("%Y-%m-%d %H:%M") if self.last_gps_update else None,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M") if self.updated_at else None,
        }

class MajorWarehouseStorage(Base):
    """Storage and inventory movements in Major Silo Warehouse"""
    __tablename__ = "major_warehouse_storage"

    id = Column(Integer, primary_key=True, index=True)
    storage_id = Column(String(50), unique=True, nullable=False, index=True) # e.g. KS-STR-8001
    batch_id = Column(String(50), nullable=False, index=True)
    warehouse_id = Column(String(50), default="MWH-PUN-01", nullable=True)
    warehouse_name = Column(String(100), default="Pune Central Major Warehouse", nullable=True)
    farmer_id = Column(String(50), nullable=True, index=True)
    farmer_name = Column(String(100), nullable=True)
    crop_name = Column(String(50), nullable=False)
    crop_category = Column(String(50), default="Grains") # Grains, Vegetables, Fruits
    quantity_kg = Column(Float, nullable=False)           # Initial stored quantity
    current_stock_kg = Column(Float, nullable=False)      # Current balance (quantity - dispatched)
    reserved_quantity_kg = Column(Float, default=0.0)     # Reserved for transit / order
    dispatched_quantity_kg = Column(Float, default=0.0)   # Total dispatched
    storage_location = Column(String(100), nullable=False) # e.g. Silo Bay A-3, Sector 4
    storage_type = Column(String(50), default="Silo Storage", nullable=True) # Silo Storage, Cold Storage, Dry Warehouse
    expiry_date = Column(String(30), nullable=True)
    temperature_celsius = Column(Float, nullable=True)
    humidity_percentage = Column(Float, nullable=True)
    movement_type = Column(String(50), default="INTAKE_STORAGE") # INTAKE_STORAGE, INTERNAL_TRANSFER, DISPATCH_PICK, COMPLETED
    status = Column(String(30), default="Stored")         # Stored, Reserved, Dispatched, Partially Dispatched, Completed
    storage_date = Column(String(20), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def available_quantity_kg(self) -> float:
        return max(0.0, round(float(self.current_stock_kg or 0.0) - float(self.reserved_quantity_kg or 0.0), 2))

    def to_dict(self):
        return {
            "id": self.id,
            "storage_id": self.storage_id,
            "batch_id": self.batch_id,
            "warehouse_id": self.warehouse_id or "MWH-PUN-01",
            "warehouse_name": self.warehouse_name or "Pune Central Major Warehouse",
            "farmer_id": self.farmer_id or "",
            "farmer_name": self.farmer_name or "",
            "crop_name": self.crop_name,
            "crop_category": self.crop_category or "Grains",
            "quantity_kg": self.quantity_kg,
            "current_stock_kg": self.current_stock_kg,
            "reserved_quantity_kg": self.reserved_quantity_kg or 0.0,
            "dispatched_quantity_kg": self.dispatched_quantity_kg or 0.0,
            "available_quantity_kg": self.available_quantity_kg,
            "storage_location": self.storage_location,
            "storage_type": self.storage_type or "Silo Storage",
            "expiry_date": self.expiry_date or "",
            "temperature_celsius": self.temperature_celsius,
            "humidity_percentage": self.humidity_percentage,
            "movement_type": self.movement_type,
            "status": self.status,
            "storage_date": self.storage_date,
            "notes": self.notes or "",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M") if self.updated_at else None,
        }


