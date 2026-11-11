import os
import tempfile
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Attempt loading .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass


class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "indietrack-development-insecure-secret-key-32chars")
    APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://127.0.0.1:5000")
    
    # Database Configuration
    # Defaults to local SQLite for development if Azure SQL is not provided.
    # On Vercel, the local filesystem is read-only except for tempfile.gettempdir() (/tmp).
    _default_db = (
        f"sqlite:///{Path(tempfile.gettempdir()) / 'indietrack_dev.db'}"
        if os.environ.get("VERCEL")
        else f"sqlite:///{BASE_DIR / 'instance' / 'indietrack_dev.db'}"
    )
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", _default_db)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }

    # Azure Blob Storage Configuration
    AZURE_STORAGE_CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")
    AZURE_STORAGE_CONTAINER = os.environ.get("AZURE_STORAGE_CONTAINER", "indietrack-assets")
    
    # Local Storage Fallback Folder (used in development when Azure Storage is not configured)
    _default_upload = (
        str(Path(tempfile.gettempdir()) / "uploads")
        if os.environ.get("VERCEL")
        else str(BASE_DIR / "uploads")
    )
    LOCAL_UPLOAD_FOLDER = os.environ.get("LOCAL_UPLOAD_FOLDER", _default_upload)
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB max file upload size
    
    # Allowed file extensions and MIME content-types for security
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "mp3", "wav", "flac", "pdf"}
    ALLOWED_MIME_TYPES = {
        "image/png",
        "image/jpeg",
        "image/webp",
        "audio/mpeg",
        "audio/wav",
        "audio/x-wav",
        "audio/flac",
        "application/pdf"
    }

    # Security & Session Settings
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds
    
    # Rate Limiting
    RATELIMIT_DEFAULT = os.environ.get("RATELIMIT_DEFAULT", "200 per day;50 per hour")
    RATELIMIT_AUTH = os.environ.get("RATELIMIT_AUTH", "5 per minute")
    
    # Power BI Configuration (Optional)
    POWER_BI_REPORT_URL = os.environ.get("POWER_BI_REPORT_URL", "")

    @classmethod
    def is_azure_sql(cls) -> bool:
        """Checks if current database URI targets Azure SQL / MS SQL Server."""
        uri = cls.SQLALCHEMY_DATABASE_URI or ""
        return uri.startswith("mssql") or ".database.windows.net" in uri

    @classmethod
    def is_azure_storage_configured(cls) -> bool:
        """Checks if Azure Blob Storage has a configured connection string."""
        conn = cls.AZURE_STORAGE_CONNECTION_STRING or ""
        return bool(conn.strip()) and not conn.startswith("replace-") and conn.upper() != "LOCAL_DEV"

    @classmethod
    def validate_production_config(cls) -> list[str]:
        """Validates critical settings for production and returns missing setting names only."""
        missing = []
        if not os.environ.get("SECRET_KEY") or os.environ.get("SECRET_KEY").startswith("replace-"):
            missing.append("SECRET_KEY")
        if not os.environ.get("DATABASE_URL") or os.environ.get("DATABASE_URL").startswith("replace-"):
            missing.append("DATABASE_URL")
        return missing


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False


class TestingConfig(Config):
    """Testing environment configuration."""
    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False  # Allows straightforward testing of POST routes
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    AZURE_STORAGE_CONNECTION_STRING = ""
    LOCAL_UPLOAD_FOLDER = str(BASE_DIR / "tests" / "test_uploads")
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    """Production deployment configuration (Azure App Service)."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Strict"


# Configuration dictionary for factory selection
config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
