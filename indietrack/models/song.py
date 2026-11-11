from datetime import datetime, timezone
from indietrack import db


class Song(db.Model):
    """Song entity representing an original track created by an artist."""
    __tablename__ = "songs"

    song_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    artist_id = db.Column(db.Integer, db.ForeignKey("artist_profiles.artist_id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="in-progress")  # demo, in-progress, mastered, archived
    artwork_asset_id = db.Column(db.Integer, db.ForeignKey("assets.asset_id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime, 
        nullable=False, 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    artist = db.relationship("ArtistProfile", back_populates="songs")
    releases = db.relationship("Release", back_populates="song", cascade="all, delete-orphan", order_by="Release.release_date.desc()")
    campaigns = db.relationship("Campaign", back_populates="song", cascade="all, delete-orphan", order_by="Campaign.start_date.desc()")
    artwork_asset = db.relationship("Asset", foreign_keys=[artwork_asset_id], post_update=True)

    @property
    def formatted_duration(self) -> str:
        """Returns mm:ss representation of duration."""
        if not self.duration_seconds:
            return "--:--"
        mins, secs = divmod(self.duration_seconds, 60)
        return f"{mins:02d}:{secs:02d}"

    def __repr__(self) -> str:
        return f"<Song {self.song_id} - '{self.title}' ({self.status})>"
