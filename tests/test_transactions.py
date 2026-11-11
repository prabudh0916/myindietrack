import pytest
from datetime import date
from indietrack import db
from indietrack.models import Song, Release, AuditLog, ArtistProfile


def test_atomic_transaction_success(app):
    """Demonstrates atomic multi-step transaction commit."""
    with app.app_context():
        profile = ArtistProfile.query.first()

        # Begin atomic transaction block
        try:
            # Step 1: Create Song
            song = Song(
                artist_id=profile.artist_id,
                title="Atomic Success Song",
                genre="Synthwave",
                status="mastered"
            )
            db.session.add(song)
            db.session.flush()  # Generate song.song_id

            # Step 2: Create Release
            release = Release(
                song_id=song.song_id,
                release_date=date.today(),
                status="scheduled"
            )
            db.session.add(release)

            # Step 3: Record Audit Log
            log = AuditLog(
                user_id=profile.user_id,
                action="ATOMIC_LAUNCH",
                entity_type="Song",
                entity_id=song.song_id,
                details="Song and release created atomically"
            )
            db.session.add(log)

            # Commit all steps together
            db.session.commit()
        except Exception:
            db.session.rollback()
            pytest.fail("Atomic transaction unexpectedly failed.")

        # Verify all entities were persisted
        assert Song.query.filter_by(title="Atomic Success Song").first() is not None
        assert Release.query.filter_by(song_id=song.song_id).first() is not None
        assert AuditLog.query.filter_by(action="ATOMIC_LAUNCH").first() is not None


def test_atomic_transaction_rollback_on_failure(app):
    """Demonstrates atomic multi-step transaction rollback upon error, ensuring no partial data remains."""
    with app.app_context():
        profile = ArtistProfile.query.first()

        try:
            # Step 1: Add Song
            song = Song(
                artist_id=profile.artist_id,
                title="Will Be Rolled Back Song",
                genre="Lo-Fi",
                status="demo"
            )
            db.session.add(song)
            db.session.flush()

            # Step 2: Simulate unexpected failure / invalid constraint violation
            raise ValueError("Simulated unexpected network failure or constraint error during release scheduling!")

            # (Step 3 never reached)
            db.session.commit()
        except ValueError:
            # Atomic rollback on exception
            db.session.rollback()

        # Verify that Step 1 was cleanly rolled back and no phantom record exists
        rolled_back_song = Song.query.filter_by(title="Will Be Rolled Back Song").first()
        assert rolled_back_song is None, "Rollback failed: partial song record remained in database!"
