from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from backend.models.enums import UserRole

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username or Email")
    password: str = Field(..., min_length=4, max_length=100)

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: UserRole
    role_title: str
    farmer_id: Optional[str] = None
    buyer_id: Optional[str] = None
    full_name: str
    phone: Optional[str] = None
    jurisdiction_or_location: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    role: UserRole
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = None
    jurisdiction_or_location: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    project: str = "KrushiSetu"
    version: str = "1.0.0"
    database: str
    ai_engine_ready: bool

class SupplyChainNode(BaseModel):
    tier: int
    role: UserRole
    name: str
    description: str
    requires_custom_id: bool
    id_format: Optional[str] = None

class SupplyChainResponse(BaseModel):
    pipeline: str = "Food Department → Panchayat Samiti → Gram Panchayat → Farmer → Major Warehouse → Minor Warehouse → Bulk Buyer"
    total_tiers: int
    nodes: List[SupplyChainNode]

