import os
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta
from werkzeug.utils import secure_filename
from flask import current_app

from indietrack import db
from indietrack.models.asset import Asset
from config import Config

# Magic bytes signature validation for secure content-type verification
MAGIC_BYTES = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"RIFF": "audio/wav",  # First 4 bytes, with 'WAVE' later
    b"ID3": "audio/mpeg",  # MP3 with ID3v2 tag
    b"\xff\xfb": "audio/mpeg",  # MP3 MPEG-1 Layer 3 without ID3
    b"\xff\xf3": "audio/mpeg",  # MP3 MPEG-2 Layer 3
    b"fLaC": "audio/flac",
    b"%PDF": "application/pdf",
    b"WEBP": "image/webp"
}


def detect_mime_type(stream, client_mime: str, filename: str) -> str:
    """Sniffs leading magic bytes from file stream to prevent MIME spoofing."""
    pos = stream.tell()
    header = stream.read(32)
    stream.seek(pos)

    # Check magic signatures
    for sig, mime in MAGIC_BYTES.items():
        if header.startswith(sig):
            return mime
    # Check WebP (RIFF....WEBP)
    if header.startswith(b"RIFF") and b"WEBP" in header[:16]:
        return "image/webp"
    if header.startswith(b"RIFF") and b"WAVE" in header[:16]:
        return "audio/wav"

    # Fallback to client MIME if in allowed list, otherwise empty
    if client_mime in Config.ALLOWED_MIME_TYPES:
        return client_mime

    return "application/octet-stream"


class StorageService:
    """Service managing asset uploads and downloads via Azure Blob Storage or Local Fallback."""

    @classmethod
    def is_azure_available(cls) -> bool:
        return Config.is_azure_storage_configured()

    @classmethod
    def get_blob_service_client(cls):
        """Initializes and returns official Azure BlobServiceClient if configured."""
        if not cls.is_azure_available():
            return None
        try:
            from azure.storage.blob import BlobServiceClient
            return BlobServiceClient.from_connection_string(Config.AZURE_STORAGE_CONNECTION_STRING)
        except Exception:
            return None

    @classmethod
    def test_azure_connection(cls) -> tuple[bool, str]:
        """Tests live Azure Blob Storage connectivity without exposing secrets."""
        if not cls.is_azure_available():
            return False, "Azure Storage Connection String is not configured (using local fallback adapter)."
        try:
            client = cls.get_blob_service_client()
            if not client:
                return False, "Failed to instantiate Azure BlobServiceClient."
            # Ping service by querying containers
            containers = list(client.list_containers(name_starts_with=Config.AZURE_STORAGE_CONTAINER, results_per_page=1))
            return True, f"Successfully connected to Azure Blob Storage (Container: {Config.AZURE_STORAGE_CONTAINER})."
        except Exception as e:
            return False, f"Azure Blob connection test failed: {type(e).__name__}"

    @classmethod
    def upload_file(cls, file_storage, user_id: int, song_id: int = None, campaign_id: int = None) -> tuple[Asset, str]:
        """
        Validates, encrypts/sanitizes, and stores file in Azure Blob Storage or local fallback directory.
        Returns: (Asset model instance, error_message or "")
        """
        if not file_storage or not file_storage.filename:
            return None, "No file was selected for upload."

        orig_filename = secure_filename(file_storage.filename)
        if not orig_filename:
            return None, "Invalid file name."

        # Extension check
        ext = orig_filename.rsplit(".", 1)[-1].lower() if "." in orig_filename else ""
        if ext not in Config.ALLOWED_EXTENSIONS:
            return None, f"File extension '.{ext}' is not permitted. Allowed: {', '.join(sorted(Config.ALLOWED_EXTENSIONS))}"

        # Detect true MIME type via magic bytes
        detected_mime = detect_mime_type(file_storage.stream, file_storage.mimetype, orig_filename)
        if detected_mime not in Config.ALLOWED_MIME_TYPES:
            return None, f"File content type '{detected_mime}' is not permitted."

        # Calculate file size
        file_storage.stream.seek(0, os.SEEK_END)
        size_bytes = file_storage.stream.tell()
        file_storage.stream.seek(0)

        if size_bytes > Config.MAX_CONTENT_LENGTH:
            return None, f"File exceeds maximum allowed size of {Config.MAX_CONTENT_LENGTH // (1024 * 1024)} MB."

        if size_bytes == 0:
            return None, "Uploaded file is empty."

        # Generate unique non-colliding blob name
        unique_id = uuid.uuid4().hex
        blob_name = f"user_{user_id}/{unique_id}_{orig_filename}"

        backend = "azure_blob" if cls.is_azure_available() else "local_dev"

        if backend == "azure_blob":
            try:
                blob_service = cls.get_blob_service_client()
                container_client = blob_service.get_container_client(Config.AZURE_STORAGE_CONTAINER)
                if not container_client.exists():
                    container_client.create_container()
                
                blob_client = container_client.get_blob_client(blob_name)
                blob_client.upload_blob(
                    file_storage.stream,
                    overwrite=True,
                    content_settings={"content_type": detected_mime}
                )
            except Exception as e:
                return None, f"Azure Blob Storage upload failed: {str(e)}"
        else:
            # Local development fallback
            upload_dir = Path(Config.LOCAL_UPLOAD_FOLDER) / f"user_{user_id}"
            upload_dir.mkdir(parents=True, exist_ok=True)
            local_path = upload_dir / f"{unique_id}_{orig_filename}"
            file_storage.save(str(local_path))

        # Save metadata to database
        asset = Asset(
            user_id=user_id,
            song_id=song_id,
            campaign_id=campaign_id,
            blob_name=blob_name,
            original_filename=orig_filename,
            content_type=detected_mime,
            size_bytes=size_bytes,
            storage_backend=backend
        )
        db.session.add(asset)
        db.session.commit()

        return asset, ""

    @classmethod
    def get_asset_stream(cls, asset: Asset):
        """Returns binary stream or file path for secure authorized downloads."""
        if asset.storage_backend == "azure_blob" and cls.is_azure_available():
            try:
                blob_service = cls.get_blob_service_client()
                container_client = blob_service.get_container_client(Config.AZURE_STORAGE_CONTAINER)
                blob_client = container_client.get_blob_client(asset.blob_name)
                downloader = blob_client.download_blob()
                return downloader.readall(), asset.content_type, asset.original_filename
            except Exception:
                return None, None, None
        else:
            # Local development path
            local_path = Path(Config.LOCAL_UPLOAD_FOLDER) / asset.blob_name
            if local_path.exists():
                return local_path.read_bytes(), asset.content_type, asset.original_filename
            return None, None, None

    @classmethod
    def delete_asset(cls, asset: Asset) -> bool:
        """Deletes file from storage backend and metadata from database."""
        try:
            if asset.storage_backend == "azure_blob" and cls.is_azure_available():
                blob_service = cls.get_blob_service_client()
                container_client = blob_service.get_container_client(Config.AZURE_STORAGE_CONTAINER)
                blob_client = container_client.get_blob_client(asset.blob_name)
                if blob_client.exists():
                    blob_client.delete_blob()
            else:
                local_path = Path(Config.LOCAL_UPLOAD_FOLDER) / asset.blob_name
                if local_path.exists():
                    local_path.unlink()

            db.session.delete(asset)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False
