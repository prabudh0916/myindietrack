from datetime import datetime, date, timezone
from indietrack import db


class Release(db.Model):
    """Release entity representing a scheduled or past commercial release of a song."""
    __tablename__ = "releases"

    release_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    song_id = db.Column(db.Integer, db.ForeignKey("songs.song_id", ondelete="CASCADE"), nullable=False, index=True)
    release_date = db.Column(db.Date, nullable=False, index=True)
    release_type = db.Column(db.String(50), nullable=False, default="single")  # single, ep, album, remix
    status = db.Column(db.String(50), nullable=False, default="planned", index=True)  # draft, planned, scheduled, released, cancelled
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime, 
        nullable=False, 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    song = db.relationship("Song", back_populates="releases")

    @property
    def is_upcoming(self) -> bool:
        return self.release_date >= date.today() and self.status in ("planned", "scheduled")

    @property
    def is_released(self) -> bool:
        return self.status == "released" or (self.release_date <= date.today() and self.status == "scheduled")

    def __repr__(self) -> str:
        return f"<Release {self.release_id} - Song {self.song_id} on {self.release_date} ({self.status})>"
