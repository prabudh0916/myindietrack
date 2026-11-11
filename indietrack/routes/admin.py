from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from indietrack import db
from indietrack.models.user import User
from indietrack.models.audit import AuditLog
from indietrack.services.auth_service import admin_required, get_current_user
from indietrack.services.audit_service import AuditService

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/users")
@admin_required
def users():
    """Admin user directory (passwords and hashes are strictly excluded)."""
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/<int:user_id>/toggle-status", methods=["POST"])
@admin_required
def toggle_user_status(user_id: int):
    """Toggle user active / deactivated status."""
    current_admin = get_current_user()
    if current_admin.user_id == user_id:
        flash("You cannot deactivate your own administrative account.", "warning")
        return redirect(url_for("admin.users"))

    target_user = User.query.get_or_404(user_id)
    target_user.is_active = not target_user.is_active
    db.session.commit()

    action_label = "activated" if target_user.is_active else "deactivated"
    AuditService.log(
        "ADMIN_USER_STATUS_CHANGE",
        "User",
        user_id,
        f"Admin {current_admin.email} {action_label} user {target_user.email}"
    )
    flash(f"User account for '{target_user.email}' has been {action_label}.", "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/change-role", methods=["POST"])
@admin_required
def change_role(user_id: int):
    """Update user role (artist <-> admin)."""
    current_admin = get_current_user()
    target_user = User.query.get_or_404(user_id)

    new_role = request.form.get("role")
    if new_role not in ["artist", "admin"]:
        flash("Invalid role specified.", "danger")
        return redirect(url_for("admin.users"))

    if target_user.user_id == current_admin.user_id and new_role != "admin":
        flash("You cannot remove your own admin privileges.", "warning")
        return redirect(url_for("admin.users"))

    target_user.role = new_role
    db.session.commit()

    AuditService.log(
        "ADMIN_ROLE_CHANGE",
        "User",
        user_id,
        f"Admin {current_admin.email} changed role of {target_user.email} to {new_role}"
    )
    flash(f"Role for '{target_user.email}' updated to {new_role}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/audit")
@admin_required
def audit():
    """System-wide security and activity audit log viewer."""
    action_filter = request.args.get("action", "").strip()
    query = AuditLog.query

    if action_filter:
        query = query.filter(AuditLog.action == action_filter)

    logs = query.order_by(AuditLog.timestamp.desc()).limit(150).all()

    # Get distinct action types for filter dropdown
    distinct_actions = [r[0] for r in db.session.query(AuditLog.action).distinct().all()]

    return render_template(
        "admin/audit.html",
        logs=logs,
        distinct_actions=distinct_actions,
        action_filter=action_filter
    )
