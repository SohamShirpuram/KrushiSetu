from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from backend.database.connection import Base

class AuditLog(Base):
    """
    Universal Audit Log.
    Tracks every edit made to operational records across KrushiSetu.
    Captures: Old Value, New Value, Edited By, Date/Time, Reason/Note.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(50), nullable=False, index=True)
    record_id = Column(String(50), nullable=False, index=True)
    field_name = Column(String(50), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    edited_by = Column(String(50), nullable=False)        # username
    edited_by_role = Column(String(50), nullable=False)   # role title or key
    change_reason = Column(String(255), nullable=True)    # optional/required reason for edit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("idx_audit_table_record", "table_name", "record_id"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "table_name": self.table_name,
            "record_id": self.record_id,
            "field_name": self.field_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "edited_by": self.edited_by,
            "edited_by_role": self.edited_by_role,
            "change_reason": self.change_reason or "Operational modification",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }

