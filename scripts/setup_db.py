"""
Database Initialization Script for IndieTrack
Initializes all 3NF tables and creates database views.
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from indietrack import create_app, db
from indietrack.models import User, ArtistProfile, Song, Release, Campaign, CampaignMetric, Asset, AuditLog
from config import Config


def init_database():
    app = create_app()
    with app.app_context():
        print("[*] Initializing IndieTrack Relational Database...")
        print(f"[*] Target Database Engine: {'Azure SQL Database' if Config.is_azure_sql() else 'SQLite Development Adapter'}")
        
        # 1. Create tables
        db.create_all()
        print("[+] Core relational tables created successfully:")
        print("    - users, artist_profiles, songs, releases, campaigns, campaign_metrics, assets, audit_logs")

        # 2. Create Views (compatible with SQLite and SQL Server)
        try:
            db.session.execute(db.text("DROP VIEW IF EXISTS CampaignPerformanceView;"))
            db.session.execute(db.text("""
                CREATE VIEW CampaignPerformanceView AS
                SELECT 
                    c.campaign_id,
                    c.campaign_name,
                    c.song_id,
                    s.title AS song_title,
                    s.artist_id,
                    ap.artist_name,
                    c.platform,
                    c.budget,
                    c.start_date,
                    c.status AS campaign_status,
                    COUNT(m.metric_id) AS total_metric_entries,
                    COALESCE(SUM(m.impressions), 0) AS total_impressions,
                    COALESCE(SUM(m.clicks), 0) AS total_clicks,
                    COALESCE(SUM(m.reported_streams), 0) AS total_reported_streams,
                    COALESCE(SUM(m.spend), 0.0) AS total_spend,
                    CASE 
                        WHEN COALESCE(SUM(m.clicks), 0) > 0 
                        THEN ROUND(CAST(SUM(m.spend) AS FLOAT) / SUM(m.clicks), 2)
                        ELSE 0.0 
                    END AS cost_per_click
                FROM campaigns c
                INNER JOIN songs s ON c.song_id = s.song_id
                INNER JOIN artist_profiles ap ON s.artist_id = ap.artist_id
                LEFT JOIN campaign_metrics m ON c.campaign_id = m.campaign_id
                GROUP BY c.campaign_id, c.campaign_name, c.song_id, s.title, s.artist_id, ap.artist_name, c.platform, c.budget, c.start_date, c.status;
            """))
            db.session.commit()
            print("[+] Database view 'CampaignPerformanceView' created successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"[-] Note on View creation: {e}")

        print("[+] Database setup complete.")


if __name__ == "__main__":
    init_database()
