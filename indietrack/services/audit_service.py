from flask import request
from indietrack.models.audit import AuditLog
from indietrack.services.auth_service import get_current_user


class AuditService:
    """Helper to record audit trail entries with current user and client IP context."""

    @classmethod
    def log(cls, action: str, entity_type: str, entity_id: int = None, details: str = None, user_id: int = None):
        """Records an audit log using request context."""
        ip = None
        current_u = get_current_user()
        if user_id is None and current_u:
            user_id = current_u.user_id

        try:
            ip = request.headers.get("X-Forwarded-For", request.remote_addr)
            if ip and "," in ip:
                ip = ip.split(",")[0].strip()
        except Exception:
            pass

        return AuditLog.log_event(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            user_id=user_id,
            ip_address=ip
        )
