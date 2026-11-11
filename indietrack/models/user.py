from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from indietrack import db


class User(db.Model):
    """User account entity for authentication and role authorization."""
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="artist")  # 'artist' or 'admin'
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime, 
        nullable=False, 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    artist_profile = db.relationship("ArtistProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    assets = db.relationship("Asset", back_populates="user", cascade="all, delete-orphan")
    audit_logs = db.relationship("AuditLog", back_populates="user")

    def set_password(self, password: str) -> None:
        """Securely hash password using recommended scrypt / pbkdf2 algorithm."""
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify candidate plaintext password against stored hash."""
        if not self.password_hash or not password:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_artist(self) -> bool:
        return self.role == "artist"

    def __repr__(self) -> str:
        return f"<User {self.user_id} - {self.email} ({self.role})>"


class ArtistProfile(db.Model):
    """Normalized artist profile attributes separated from authentication credentials (3NF)."""
    __tablename__ = "artist_profiles"

    artist_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    artist_name = db.Column(db.String(150), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    country = db.Column(db.String(100), nullable=True)
    primary_genre = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime, 
        nullable=False, 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = db.relationship("User", back_populates="artist_profile")
    songs = db.relationship("Song", back_populates="artist", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ArtistProfile {self.artist_id} - {self.artist_name}>"
