"""
Sample Data Seeder for IndieTrack
Populates local database with demo artist & admin accounts, songs, releases,
promotional campaigns, and clearly labeled sample metrics.
"""

import sys
from pathlib import Path
from datetime import date, timedelta

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from indietrack import create_app, db
from indietrack.models import User, ArtistProfile, Song, Release, Campaign, CampaignMetric, AuditLog


def seed_database():
    app = create_app()
    with app.app_context():
        print("[*] Starting IndieTrack Database Seeder...")
        db.create_all()

        # 1. Admin Account
        admin = User.query.filter_by(email="admin@indietrack.local").first()
        if not admin:
            admin = User(email="admin@indietrack.local", role="admin", is_active=True)
            admin.set_password("AdminDemo@2026!")
            db.session.add(admin)
            print("[+] Created Demo Admin: admin@indietrack.local / AdminDemo@2026!")
        else:
            print("[.] Demo Admin already exists.")

        # 2. Artist Account & Profile
        artist_user = User.query.filter_by(email="artist@indietrack.local").first()
        if not artist_user:
            artist_user = User(email="artist@indietrack.local", role="artist", is_active=True)
            artist_user.set_password("ArtistDemo@2026!")
            db.session.add(artist_user)
            db.session.flush()

            profile = ArtistProfile(
                user_id=artist_user.user_id,
                artist_name="Luna Horizon",
                bio="Electronic-indie producer crafting atmospheric synthscapes and nocturnal pop melodies from Lucknow.",
                country="India",
                primary_genre="Synthwave / Indie Pop"
            )
            db.session.add(profile)
            print("[+] Created Demo Artist: artist@indietrack.local / ArtistDemo@2026! (Luna Horizon)")
        else:
            profile = artist_user.artist_profile
            print("[.] Demo Artist user already exists.")

        db.session.commit()
        artist_id = profile.artist_id

        # 3. Fictional Songs
        songs_data = [
            {
                "title": "Midnight City Lights",
                "genre": "Synthwave",
                "duration_seconds": 218,
                "status": "mastered",
                "description": "Upbeat retro synthwave anthem with shimmering 80s arpeggios and punchy LinnDrum samples."
            },
            {
                "title": "Echoes of Autumn",
                "genre": "Indie Folk",
                "duration_seconds": 194,
                "status": "mastered",
                "description": "Acoustic fingerpicked guitar and nostalgic vocal harmonies recorded with vintage ribbon mics."
            },
            {
                "title": "Neon Raindrop Dreams",
                "genre": "Lo-Fi Chill",
                "duration_seconds": 162,
                "status": "demo",
                "description": "Relaxed tape-saturated beats with warm Rhodes chords and soothing rain textures."
            },
            {
                "title": "Lucid Velocity",
                "genre": "Cyberpunk Electro",
                "duration_seconds": 245,
                "status": "in-progress",
                "description": "High-energy electronic dance track featuring driving basslines and acid synths."
            }
        ]

        song_map = {}
        for s_data in songs_data:
            song = Song.query.filter_by(artist_id=artist_id, title=s_data["title"]).first()
            if not song:
                song = Song(artist_id=artist_id, **s_data)
                db.session.add(song)
                db.session.flush()
                print(f"[+] Added Song: '{song.title}'")
            song_map[s_data["title"]] = song

        db.session.commit()

        # 4. Release Milestones
        s1 = song_map.get("Midnight City Lights")
        s2 = song_map.get("Echoes of Autumn")

        if s1 and not Release.query.filter_by(song_id=s1.song_id).first():
            rel1 = Release(
                song_id=s1.song_id,
                release_date=date.today() + timedelta(days=21),
                release_type="single",
                status="scheduled",
                notes="Distributed through DistroKid across all DSPs (Spotify, Apple Music, YouTube Music)."
            )
            db.session.add(rel1)
            print(f"[+] Scheduled Release for '{s1.title}' on {rel1.release_date}")

        if s2 and not Release.query.filter_by(song_id=s2.song_id).first():
            rel2 = Release(
                song_id=s2.song_id,
                release_date=date.today() + timedelta(days=45),
                release_type="single",
                status="planned",
                notes="Pending final master review and high-res cover art."
            )
            db.session.add(rel2)
            print(f"[+] Planned Release for '{s2.title}' on {rel2.release_date}")

        db.session.commit()

        # 5. Promotional Campaigns
        if s1 and not Campaign.query.filter_by(song_id=s1.song_id).first():
            camp1 = Campaign(
                song_id=s1.song_id,
                campaign_name="Spotify Editorial Pre-Save Push",
                platform="Spotify",
                objective="pre-save",
                budget=450.00,
                start_date=date.today() - timedelta(days=20),
                end_date=date.today() + timedelta(days=10),
                status="active",
                landing_url="https://distrokid.com/hyperfollow/lunahorizon/midnight-city-lights"
            )
            camp2 = Campaign(
                song_id=s1.song_id,
                campaign_name="YouTube Shorts Audio Promo",
                platform="YouTube",
                objective="awareness",
                budget=250.00,
                start_date=date.today() - timedelta(days=15),
                end_date=date.today() - timedelta(days=2),
                status="completed",
                landing_url="https://youtube.com/@lunahorizonmusic"
            )
            camp3 = Campaign(
                song_id=s1.song_id,
                campaign_name="Instagram Reels Trend Boost",
                platform="Instagram",
                objective="engagement",
                budget=300.00,
                start_date=date.today() - timedelta(days=10),
                end_date=date.today() + timedelta(days=15),
                status="active",
                landing_url="https://instagram.com/lunahorizon"
            )
            db.session.add_all([camp1, camp2, camp3])
            db.session.flush()
            print("[+] Created 3 Promotional Campaigns on Spotify, YouTube, and Instagram")

            # 6. Empirical Dated Metrics (All clearly marked data_source='sample_data')
            metrics_data = [
                # Campaign 1 (Spotify)
                (camp1.campaign_id, date.today() - timedelta(days=18), 1250, 85,  42, 60,  25.00, "Initial pre-save pitch"),
                (camp1.campaign_id, date.today() - timedelta(days=14), 2400, 190, 88, 140, 45.00, "Mid-week organic lift"),
                (camp1.campaign_id, date.today() - timedelta(days=9),  3800, 310, 155, 260, 70.00, "Synthwave playlist addition"),
                (camp1.campaign_id, date.today() - timedelta(days=5),  4100, 360, 210, 320, 80.00, "Weekend listener spike"),
                (camp1.campaign_id, date.today() - timedelta(days=1),  3200, 240, 130, 210, 55.00, "Sustained listener retention"),

                # Campaign 2 (YouTube Shorts)
                (camp2.campaign_id, date.today() - timedelta(days=14), 5600, 220, 480, 190, 60.00, "Behind-the-scenes synth teaser"),
                (camp2.campaign_id, date.today() - timedelta(days=8),  8900, 410, 920, 380, 110.00, "Viral short sound usage"),
                (camp2.campaign_id, date.today() - timedelta(days=3),  6100, 280, 640, 250, 75.00, "Promo cycle wrap-up"),

                # Campaign 3 (Instagram Reels)
                (camp3.campaign_id, date.today() - timedelta(days=9),  2800, 145, 310, 95,  40.00, "Studio production breakdown reel"),
                (camp3.campaign_id, date.today() - timedelta(days=4),  4200, 230, 520, 180, 65.00, "Remix stems preview"),
                (camp3.campaign_id, date.today() - timedelta(days=1),  5100, 290, 680, 240, 85.00, "Artist Q&A session reel"),
            ]

            for cid, m_date, imps, clicks, eng, streams, spend, note in metrics_data:
                m = CampaignMetric(
                    campaign_id=cid,
                    metric_date=m_date,
                    impressions=imps,
                    clicks=clicks,
                    engagement=eng,
                    reported_streams=streams,
                    spend=spend,
                    data_source="sample_data",
                    notes=note
                )
                db.session.add(m)

            print(f"[+] Populated {len(metrics_data)} dated metric entries (flagged data_source='sample_data')")

        # 7. Record Audit Log Entry
        AuditLog.log_event(
            action="SYSTEM_SEED_DEMO_DATA",
            entity_type="System",
            details="Seeded fictional songs, releases, campaigns, and sample metrics for local development."
        )

        db.session.commit()
        print("[+] Seed process completed successfully!")
        print("\nLogin Credentials for Local Testing:")
        print("  Artist Account : artist@indietrack.local / ArtistDemo@2026!")
        print("  Admin Account  : admin@indietrack.local  / AdminDemo@2026!\n")


if __name__ == "__main__":
    seed_database()
