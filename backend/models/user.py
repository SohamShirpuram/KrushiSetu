from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from backend.database.connection import Base
from backend.models.enums import UserRole

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, index=True)

    # Unique IDs for specific roles as per specifications
    farmer_id = Column(String(30), unique=True, index=True, nullable=True)
    buyer_id = Column(String(30), unique=True, index=True, nullable=True)

    # Profile & Jurisdictional details
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    jurisdiction_or_location = Column(String(150), nullable=True)  # e.g., District, Panchayat, Warehouse location

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value if hasattr(self.role, "value") else str(self.role),
            "farmer_id": self.farmer_id,
            "buyer_id": self.buyer_id,
            "full_name": self.full_name,
            "phone": self.phone,
            "jurisdiction_or_location": self.jurisdiction_or_location,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

