from flask import Blueprint, render_template, jsonify
from indietrack import db
from indietrack.services.storage_service import StorageService
from config import Config

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Public landing page showcasing IndieTrack capabilities and architecture."""
    return render_template("main/index.html")


@main_bp.route("/about")
def about():
    """Project background, architecture details, and academic credits."""
    return render_template("main/about.html")


@main_bp.route("/health")
@main_bp.route("/api/health")
@main_bp.route("/api/v1/health")
def health_check():
    """
    Readiness and liveness probe.
    Tests database and storage connectivity without revealing secrets or credentials.
    """
    # 1. Test Relational Database
    db_status = "unhealthy"
    try:
        db.session.execute(db.text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        pass

    # 2. Test Storage Service
    storage_type = "azure_blob" if Config.is_azure_storage_configured() else "local_dev"
    azure_connected, azure_msg = StorageService.test_azure_connection()

    status_code = 200 if db_status == "healthy" else 503
    return jsonify({
        "status": "UP" if db_status == "healthy" else "DEGRADED",
        "database": {
            "status": db_status,
            "target": "Azure SQL Database" if Config.is_azure_sql() else "SQLite Development Adapter"
        },
        "storage": {
            "backend": storage_type,
            "azure_connected": azure_connected,
            "message": azure_msg
        },
        "version": "1.0.0"
    }), status_code
