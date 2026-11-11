from datetime import datetime, timezone
from indietrack import db


class AuditLog(db.Model):
    """Immutable audit trail for security-critical and administrative actions."""
    __tablename__ = "audit_logs"

    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(100), nullable=False)
    entity_id = db.Column(db.Integer, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    details = db.Column(db.String(1000), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    user = db.relationship("User", back_populates="audit_logs")

    @classmethod
    def log_event(cls, action: str, entity_type: str, entity_id: int = None, details: str = None, user_id: int = None, ip_address: str = None):
        """Records an audit event safely without secrets."""
        try:
            log_entry = cls(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                ip_address=ip_address,
                details=details
            )
            db.session.add(log_entry)
            db.session.commit()
            return log_entry
        except Exception:
            db.session.rollback()
            return None

    def __repr__(self) -> str:
        return f"<AuditLog {self.log_id} - {self.action} on {self.entity_type}:{self.entity_id}>"
