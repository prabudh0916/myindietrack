from datetime import date, timedelta
from indietrack.models import Song, Release


def test_schedule_release(client, auth, app):
    """Test scheduling a release for an owned song."""
    auth.login_artist()
    with app.app_context():
        song = Song.query.filter_by(title="First Demo Track").first()
        song_id = song.song_id

    rel_date = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
    resp = client.post("/releases/new", data={
        "song_id": song_id,
        "release_date": rel_date,
        "release_type": "single",
        "status": "scheduled",
        "notes": "Distributed via DistroKid"
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert b"scheduled" in resp.data

    with app.app_context():
        rel = Release.query.filter_by(song_id=song_id).first()
        assert rel is not None
        assert rel.status == "scheduled"
        assert rel.is_upcoming is True


def test_cross_user_release_isolation(client, auth, app):
    """Ensure another artist cannot attach a release to a song they do not own."""
    with app.app_context():
        song = Song.query.filter_by(title="First Demo Track").first()
        song_id = song.song_id

    # Log in as otherartist@example.com
    auth.login_other_artist()

    rel_date = (date.today() + timedelta(days=20)).strftime("%Y-%m-%d")
    resp = client.post("/releases/new", data={
        "song_id": song_id,
        "release_date": rel_date,
        "release_type": "single",
        "status": "scheduled"
    })

    assert resp.status_code == 403
