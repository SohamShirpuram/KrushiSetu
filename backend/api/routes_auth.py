from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.database.connection import get_db
from backend.models.user import User
from backend.models.enums import UserRole, ROLE_METADATA
from backend.models.schemas import (
    LoginRequest,
    TokenResponse,
    UserResponse,
    UserRegisterRequest,
)
from backend.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    format_user_response,
)
from backend.services.id_generator import generate_farmer_id, generate_buyer_id

router = APIRouter(prefix="/api/auth", tags=["Authentication & Roles"])

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user by username or email.
    Returns signed JWT access token and user role profile.
    """
    user = (
        db.query(User)
        .filter(or_(User.username == request.username, User.email == request.username))
        .first()
    )
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please verify your username and password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Please contact system administrator.",
        )

    access_token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role.value,
            "id": user.id,
        }
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=format_user_response(user),
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieve profile and role info for currently authenticated user."""
    return format_user_response(current_user)


@router.post("/register", response_model=UserResponse)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Register new user.
    Open registration is permitted for Farmer and Bulk Buyer with auto-assigned unique IDs:
    - Farmer: KS-FMR-XXXX
    - Bulk Buyer: KS-BYR-XXXX
    Institutional and administrative roles are provisioned by Admin.
    """
    # Verify unique username and email
    if db.query(User).filter(User.username == request.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered. Please choose another username.",
        )
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address already registered. Please use another email.",
        )

    # Validate allowed self-registration roles
    if request.role not in [UserRole.FARMER, UserRole.BULK_BUYER]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Self-registration is available only for Farmers and Bulk Buyers. Institutional roles require administrator provisioning.",
        )

    farmer_id = None
    buyer_id = None

    if request.role == UserRole.FARMER:
        farmer_id = generate_farmer_id(db)
    elif request.role == UserRole.BULK_BUYER:
        buyer_id = generate_buyer_id(db)

    new_user = User(
        username=request.username,
        email=request.email,
        hashed_password=hash_password(request.password),
        role=request.role,
        farmer_id=farmer_id,
        buyer_id=buyer_id,
        full_name=request.full_name,
        phone=request.phone,
        jurisdiction_or_location=request.jurisdiction_or_location,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return format_user_response(new_user)


@router.get("/roles", response_model=List[Dict[str, Any]])
def list_roles():
    """Returns metadata for all 8 defined KrushiSetu roles."""
    roles_list = []
    for role_enum, meta in ROLE_METADATA.items():
        roles_list.append({
            "key": role_enum.value,
            "title": meta.get("title"),
            "description": meta.get("description"),
            "tier_index": meta.get("tier_index"),
            "is_supply_chain_node": meta.get("is_supply_chain_node"),
            "requires_custom_id": meta.get("requires_custom_id", False),
            "id_prefix": meta.get("id_prefix"),
        })
    return sorted(roles_list, key=lambda x: x["tier_index"])

