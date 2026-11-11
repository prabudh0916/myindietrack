from datetime import datetime, timezone
from indietrack import db


class Asset(db.Model):
    """Metadata reference for files stored in Azure Blob Storage or local fallback."""
    __tablename__ = "assets"

    asset_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    song_id = db.Column(db.Integer, db.ForeignKey("songs.song_id", ondelete="SET NULL"), nullable=True, index=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.campaign_id", ondelete="SET NULL"), nullable=True, index=True)
    blob_name = db.Column(db.String(260), nullable=False, unique=True)
    original_filename = db.Column(db.String(260), nullable=False)
    content_type = db.Column(db.String(100), nullable=False)
    size_bytes = db.Column(db.BigInteger, nullable=False)
    storage_backend = db.Column(db.String(50), nullable=False, default="azure_blob")  # azure_blob or local_dev
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = db.relationship("User", back_populates="assets")
    song = db.relationship("Song", foreign_keys=[song_id])
    campaign = db.relationship("Campaign", back_populates="assets")

    @property
    def formatted_size(self) -> str:
        """Returns human-readable file size."""
        if not self.size_bytes:
            return "0 B"
        bytes_val = float(self.size_bytes)
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} TB"

    @property
    def is_image(self) -> bool:
        return self.content_type.startswith("image/")

    @property
    def is_audio(self) -> bool:
        return self.content_type.startswith("audio/")

    def __repr__(self) -> str:
        return f"<Asset {self.asset_id} - '{self.original_filename}' ({self.storage_backend})>"
