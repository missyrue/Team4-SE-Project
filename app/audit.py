"""Audit trail helper (OBS-NF-006): call this after every administrator change."""
from sqlalchemy.orm import Session

from app.models import AuditLog


def log_action(db: Session, admin_id: int, action: str, record: str, detail: str = "") -> None:
    """Add an audit row to the *current* transaction (the caller commits)."""
    db.add(AuditLog(user_id=admin_id, action=action, record=record, detail=detail))
