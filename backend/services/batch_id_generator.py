from sqlalchemy.orm import Session
from backend.models.records_warehouse import MajorWarehouseIntake

def generate_batch_id(db: Session) -> str:
    """
    Generates a unique Batch ID formatted as KS-BATCH-XXXX (e.g. KS-BATCH-1001).
    Used to track crop lots throughout grading, storage, and warehouse movement.
    """
    last_batch = (
        db.query(MajorWarehouseIntake)
        .order_by(MajorWarehouseIntake.id.desc())
        .first()
    )
    
    if last_batch and last_batch.batch_id:
        try:
            parts = last_batch.batch_id.split("-")
            last_num = int(parts[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1001
    else:
        new_num = 1001

    candidate_id = f"KS-BATCH-{new_num:04d}"
    
    while db.query(MajorWarehouseIntake).filter(MajorWarehouseIntake.batch_id == candidate_id).first():
        new_num += 1
        candidate_id = f"KS-BATCH-{new_num:04d}"
        
    return candidate_id

