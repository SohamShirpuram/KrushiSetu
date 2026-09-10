import random
from sqlalchemy.orm import Session
from backend.models.user import User

def generate_farmer_id(db: Session) -> str:
    """
    Generates a unique Farmer ID formatted as KS-FMR-XXXX (e.g. KS-FMR-1001).
    Ensures no collision with existing farmers.
    """
    last_farmer = (
        db.query(User)
        .filter(User.farmer_id.isnot(None))
        .order_by(User.id.desc())
        .first()
    )
    
    if last_farmer and last_farmer.farmer_id:
        try:
            parts = last_farmer.farmer_id.split("-")
            last_num = int(parts[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1001
    else:
        new_num = 1001

    candidate_id = f"KS-FMR-{new_num:04d}"
    
    # Safety check against collisions
    while db.query(User).filter(User.farmer_id == candidate_id).first():
        new_num += 1
        candidate_id = f"KS-FMR-{new_num:04d}"
        
    return candidate_id


def generate_buyer_id(db: Session) -> str:
    """
    Generates a unique Bulk Buyer ID formatted as KS-BYR-XXXX (e.g. KS-BYR-5001).
    Ensures no collision with existing bulk buyers.
    """
    last_buyer = (
        db.query(User)
        .filter(User.buyer_id.isnot(None))
        .order_by(User.id.desc())
        .first()
    )
    
    if last_buyer and last_buyer.buyer_id:
        try:
            parts = last_buyer.buyer_id.split("-")
            last_num = int(parts[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 5001
    else:
        new_num = 5001

    candidate_id = f"KS-BYR-{new_num:04d}"
    
    while db.query(User).filter(User.buyer_id == candidate_id).first():
        new_num += 1
        candidate_id = f"KS-BYR-{new_num:04d}"
        
    return candidate_id

