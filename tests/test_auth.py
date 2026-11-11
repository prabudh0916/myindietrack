from indietrack.models import User, ArtistProfile


def test_register_success(client, app):
    """Test successful artist registration with atomic User & ArtistProfile creation."""
    response = client.post("/auth/register", data={
        "artist_name": "New Indie Star",
        "email": "newstar@example.com",
        "primary_genre": "Dream Pop",
        "password": "ValidPassword123!",
        "confirm_password": "ValidPassword123!"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Welcome to IndieTrack" in response.data

    with app.app_context():
        u = User.query.filter_by(email="newstar@example.com").first()
        assert u is not None
        assert u.check_password("ValidPassword123!") is True
        assert u.artist_profile is not None
        assert u.artist_profile.artist_name == "New Indie Star"


def test_register_duplicate_email(client):
    """Test registration rejects duplicate email addresses."""
    response = client.post("/auth/register", data={
        "artist_name": "Duplicate Artist",
        "email": "testartist@example.com",
        "primary_genre": "Pop",
        "password": "ValidPassword123!",
        "confirm_password": "ValidPassword123!"
    }, follow_redirects=True)

    assert b"An account with this email address already exists" in response.data


def test_login_success(client, auth):
    """Test login with valid credentials."""
    response = auth.login_artist()
    assert response.status_code == 200
    assert b"Welcome back to IndieTrack" in response.data


def test_login_invalid_password(client):
    """Test login with wrong password fails."""
    response = client.post("/auth/login", data={
        "email": "testartist@example.com",
        "password": "WrongPassword!"
    }, follow_redirects=True)

    assert b"Invalid email address or password" in response.data


def test_login_deactivated_account(client, app):
    """Test that deactivated accounts cannot log in."""
    with app.app_context():
        u = User.query.filter_by(email="testartist@example.com").first()
        u.is_active = False
        from indietrack import db
        db.session.commit()

    response = client.post("/auth/login", data={
        "email": "testartist@example.com",
        "password": "SecurePass123!"
    }, follow_redirects=True)

    assert b"This account has been deactivated" in response.data


def test_logout(client, auth):
    """Test logging out clears the session."""
    auth.login_artist()
    response = auth.logout()
    assert b"You have been signed out successfully" in response.data

    # Protected dashboard should now redirect to login
    dash_resp = client.get("/dashboard/")
    assert dash_resp.status_code == 302
    assert "/auth/login" in dash_resp.headers["Location"]
