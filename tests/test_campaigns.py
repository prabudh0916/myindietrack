from datetime import date
from indietrack.models import Campaign, CampaignMetric, Song


def test_create_campaign(client, auth, app):
    """Test campaign creation for an owned song."""
    auth.login_artist()
    with app.app_context():
        song = Song.query.filter_by(title="First Demo Track").first()
        song_id = song.song_id

    resp = client.post("/campaigns/new", data={
        "song_id": song_id,
        "campaign_name": "TikTok Sound Launch",
        "platform": "TikTok",
        "objective": "streams",
        "budget": 350.00,
        "start_date": date.today().strftime("%Y-%m-%d"),
        "status": "active"
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert b"TikTok Sound Launch" in resp.data

    with app.app_context():
        camp = Campaign.query.filter_by(campaign_name="TikTok Sound Launch").first()
        assert camp is not None
        assert float(camp.budget) == 350.00


def test_add_dated_metric_and_safe_cpc(client, auth, app):
    """Test recording dated metrics and verifying safe CPC calculation handling zero clicks."""
    auth.login_artist()
    with app.app_context():
        camp = Campaign.query.filter_by(campaign_name="Initial Spotify Push").first()
        camp_id = camp.campaign_id

    # Add metric entry
    resp = client.post(f"/metrics/{camp_id}/add", data={
        "metric_date": date.today().strftime("%Y-%m-%d"),
        "impressions": 1500,
        "clicks": 120,
        "engagement": 85,
        "reported_streams": 95,
        "spend": 30.00,
        "data_source": "manual_entry",
        "notes": "Verified via Spotify for Artists dashboard"
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert b"Performance metrics" in resp.data

    with app.app_context():
        m = CampaignMetric.query.filter_by(campaign_id=camp_id).first()
        assert m is not None
        assert m.clicks == 120
        assert m.impressions == 1500
        assert float(m.spend) == 30.00
        # CPC = 30.00 / 120 = 0.25
        assert m.cost_per_click == 0.25

        # Test zero-division safe calculation
        m.clicks = 0
        assert m.cost_per_click == 0.00


def test_cross_user_campaign_isolation(client, auth, app):
    """Security test: other artist cannot add metrics or view someone else's campaign."""
    with app.app_context():
        camp = Campaign.query.filter_by(campaign_name="Initial Spotify Push").first()
        camp_id = camp.campaign_id

    # Log in as other artist
    auth.login_other_artist()

    # Detail view -> 403
    resp = client.get(f"/campaigns/{camp_id}")
    assert resp.status_code == 403

    # Add metric -> 403
    resp = client.post(f"/metrics/{camp_id}/add", data={
        "metric_date": date.today().strftime("%Y-%m-%d"),
        "impressions": 100,
        "clicks": 10,
        "engagement": 5,
        "reported_streams": 8,
        "spend": 5.00,
        "data_source": "manual_entry"
    })
    assert resp.status_code == 403
