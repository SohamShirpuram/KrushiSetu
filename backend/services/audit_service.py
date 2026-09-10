from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.models.audit import AuditLog
from backend.models.user import User

EXCLUDED_AUDIT_FIELDS = {"id", "created_at", "updated_at", "hashed_password"}

def log_audit_changes(
    db: Session,
    table_name: str,
    record_id: Any,
    old_obj: Any,
    new_data: Dict[str, Any],
    user: User,
    change_reason: str = "Operational update"
) -> List[AuditLog]:
    """
    Compares the fields of an existing model instance with new submitted values.
    For every field that changed, creates an immutable AuditLog entry recording:
    - Table Name
    - Record ID
    - Field Name
    - Old Value
    - New Value
    - Edited By (username)
    - Edited By Role
    - Date/Time
    - Reason / Operational Note
    """
    created_logs = []
    
    for field, new_val in new_data.items():
        if field in EXCLUDED_AUDIT_FIELDS:
            continue
            
        if not hasattr(old_obj, field):
            continue
            
        old_val = getattr(old_obj, field)
        
        # Normalize comparison (handle floats, strings, None)
        old_str = str(old_val) if old_val is not None else ""
        new_str = str(new_val) if new_val is not None else ""
        
        if old_str != new_str:
            audit_entry = AuditLog(
                table_name=table_name,
                record_id=str(record_id),
                field_name=field,
                old_value=old_str,
                new_value=new_str,
                edited_by=user.username if user else "system",
                edited_by_role=user.role.value if (user and hasattr(user.role, 'value')) else (str(user.role) if user else "ADMIN"),
                change_reason=change_reason or "Operational modification",
            )
            db.add(audit_entry)
            created_logs.append(audit_entry)
            
            # Apply the update to the target object
            setattr(old_obj, field, new_val)
            
    return created_logs


def get_record_audit_history(db: Session, table_name: str, record_id: Any) -> List[Dict[str, Any]]:
    """Retrieves chronological audit history for any table record."""
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.table_name == table_name, AuditLog.record_id == str(record_id))
        .order_by(AuditLog.created_at.desc())
        .all()
    )
    return [log.to_dict() for log in logs]

