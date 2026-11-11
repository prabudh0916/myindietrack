import os
import tempfile
from pathlib import Path
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import config_by_name, Config

# Initialize global extensions
db = SQLAlchemy()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)


def create_app(config_name=None):
    """Application factory for IndieTrack."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    instance_path = str(Path(tempfile.gettempdir()) / "indietrack_instance") if os.environ.get("VERCEL") else None
    app = Flask(__name__, instance_path=instance_path, instance_relative_config=True)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Ensure required instance and upload directories exist (with fallback for serverless read-only filesystems)
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass
    if app.config.get("LOCAL_UPLOAD_FOLDER"):
        try:
            os.makedirs(app.config["LOCAL_UPLOAD_FOLDER"], exist_ok=True)
        except OSError:
            pass

    # Initialize extensions with app
    db.init_app(app)
    csrf.init_app(app)
    
    # Configure limiter only if enabled in config
    if app.config.get("RATELIMIT_ENABLED", True):
        limiter.init_app(app)

    # Register Jinja context processors & custom filters
    @app.context_processor
    def inject_global_template_vars():
        from indietrack.services.auth_service import get_current_user
        from config import Config
        return {
            "current_user": get_current_user(),
            "is_azure_storage": Config.is_azure_storage_configured(),
            "is_azure_sql": Config.is_azure_sql(),
            "power_bi_url": app.config.get("POWER_BI_REPORT_URL", "")
        }

    # Register error handlers
    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        # Do not expose internal stack trace or secrets to user
        return render_template("errors/500.html"), 500

    # Register blueprints
    from indietrack.routes.main import main_bp
    from indietrack.routes.auth import auth_bp
    from indietrack.routes.dashboard import dashboard_bp
    from indietrack.routes.songs import songs_bp
    from indietrack.routes.releases import releases_bp
    from indietrack.routes.campaigns import campaigns_bp
    from indietrack.routes.metrics import metrics_bp
    from indietrack.routes.assets import assets_bp
    from indietrack.routes.analytics import analytics_bp
    from indietrack.routes.admin import admin_bp
    from indietrack.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(songs_bp, url_prefix="/songs")
    app.register_blueprint(releases_bp, url_prefix="/releases")
    app.register_blueprint(campaigns_bp, url_prefix="/campaigns")
    app.register_blueprint(metrics_bp, url_prefix="/metrics")
    app.register_blueprint(assets_bp, url_prefix="/assets")
    app.register_blueprint(analytics_bp, url_prefix="/analytics")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")

    # Add security response headers
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Content Security Policy allowing local assets and standard CDNs (Bootstrap, Chart.js)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https: blob:; "
            "font-src 'self' https://cdn.jsdelivr.net data:; "
            "connect-src 'self';"
        )
        return response

    return app
