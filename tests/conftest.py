import pytest
from datetime import date
from indietrack import create_app, db
from indietrack.models import User, ArtistProfile, Song, Release, Campaign, CampaignMetric, Asset, AuditLog


@pytest.fixture
def app():
    """Create and configure a clean testing application with in-memory database."""
    app = create_app("testing")

    with app.app_context():
        db.create_all()

        # Seed Primary Test Artist
        artist_user = User(email="testartist@example.com", role="artist", is_active=True)
        artist_user.set_password("SecurePass123!")
        db.session.add(artist_user)
        db.session.flush()

        artist_profile = ArtistProfile(
            user_id=artist_user.user_id,
            artist_name="Test Artist Band",
            primary_genre="Indie Rock"
        )
        db.session.add(artist_profile)

        # Seed Secondary Artist (For cross-user isolation testing)
        other_user = User(email="otherartist@example.com", role="artist", is_active=True)
        other_user.set_password("OtherPass123!")
        db.session.add(other_user)
        db.session.flush()

        other_profile = ArtistProfile(
            user_id=other_user.user_id,
            artist_name="Other Artist",
            primary_genre="Electronic"
        )
        db.session.add(other_profile)

        # Seed Admin User
        admin_user = User(email="testadmin@example.com", role="admin", is_active=True)
        admin_user.set_password("AdminPass123!")
        db.session.add(admin_user)

        # Seed an initial song for primary artist
        song = Song(
            artist_id=artist_profile.artist_id,
            title="First Demo Track",
            genre="Indie Rock",
            duration_seconds=180,
            status="in-progress"
        )
        db.session.add(song)
        db.session.flush()

        # Seed an initial campaign for primary artist's song
        camp = Campaign(
            song_id=song.song_id,
            campaign_name="Initial Spotify Push",
            platform="Spotify",
            budget=100.00,
            start_date=date.today(),
            status="active"
        )
        db.session.add(camp)

        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client for HTTP requests."""
    return app.test_client()


class AuthActions:
    def __init__(self, client):
        self._client = client

    def login_artist(self):
        self.logout()
        return self._client.post("/auth/login", data={
            "email": "testartist@example.com",
            "password": "SecurePass123!"
        }, follow_redirects=True)

    def login_other_artist(self):
        self.logout()
        return self._client.post("/auth/login", data={
            "email": "otherartist@example.com",
            "password": "OtherPass123!"
        }, follow_redirects=True)

    def login_admin(self):
        self.logout()
        return self._client.post("/auth/login", data={
            "email": "testadmin@example.com",
            "password": "AdminPass123!"
        }, follow_redirects=True)

    def logout(self):
        return self._client.get("/auth/logout", follow_redirects=True)


@pytest.fixture
def auth(client):
    return AuthActions(client)
