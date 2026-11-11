from indietrack.models import Song


def test_create_song(client, auth, app):
    """Test creating a song for logged-in artist."""
    auth.login_artist()
    response = client.post("/songs/new", data={
        "title": "Summer Sunset Groove",
        "genre": "Lo-Fi",
        "duration_seconds": 210,
        "status": "mastered",
        "description": "Chill vibes and Rhodes piano"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Summer Sunset Groove" in response.data

    with app.app_context():
        song = Song.query.filter_by(title="Summer Sunset Groove").first()
        assert song is not None
        assert song.genre == "Lo-Fi"
        assert song.duration_seconds == 210
        assert song.formatted_duration == "03:30"


def test_song_search_and_filter(client, auth):
    """Test searching and filtering songs in the library."""
    auth.login_artist()
    
    # Search for existing fixture song 'First Demo Track'
    resp = client.get("/songs/?q=First")
    assert b"First Demo Track" in resp.data

    # Search for non-existent song
    resp = client.get("/songs/?q=NonExistentSong12345")
    assert b"No songs found" in resp.data


def test_cross_user_song_isolation(client, auth, app):
    """CRITICAL SECURITY TEST: Ensure another artist cannot edit or delete first artist's song."""
    # Song #1 belongs to testartist@example.com
    with app.app_context():
        song = Song.query.filter_by(title="First Demo Track").first()
        song_id = song.song_id

    # Log in as otherartist@example.com
    auth.login_other_artist()

    # Attempt to view song detail -> 403 Forbidden
    detail_resp = client.get(f"/songs/{song_id}")
    assert detail_resp.status_code == 403

    # Attempt to edit song -> 403 Forbidden
    edit_resp = client.post(f"/songs/{song_id}/edit", data={
        "title": "Hacked Title",
        "genre": "Malicious",
        "status": "archived"
    })
    assert edit_resp.status_code == 403

    # Attempt to delete song -> 403 Forbidden
    delete_resp = client.post(f"/songs/{song_id}/delete")
    assert delete_resp.status_code == 403

    # Verify song title was unchanged
    with app.app_context():
        from indietrack import db
        s = db.session.get(Song, song_id)
        assert s.title == "First Demo Track"


def test_delete_song_success(client, auth, app):
    """Test owner can delete their own song."""
    auth.login_artist()
    with app.app_context():
        song = Song.query.filter_by(title="First Demo Track").first()
        song_id = song.song_id

    resp = client.post(f"/songs/{song_id}/delete", follow_redirects=True)
    assert resp.status_code == 200
    assert b"have been deleted" in resp.data

    with app.app_context():
        from indietrack import db
        assert db.session.get(Song, song_id) is None
