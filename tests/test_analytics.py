from datetime import date
from indietrack.models import Campaign, CampaignMetric
from indietrack.services.export_service import sanitize_csv_cell, ExportService


def test_formula_injection_defense():
    """CRITICAL SECURITY TEST: Ensure spreadsheet formula injection characters (=, +, -, @, tab, cr) are sanitized."""
    assert sanitize_csv_cell("=1+1") == "'=1+1"
    assert sanitize_csv_cell("+cmd|' /C calc'!A0") == "'+cmd|' /C calc'!A0"
    assert sanitize_csv_cell("-5+2") == "'-5+2"
    assert sanitize_csv_cell("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    assert sanitize_csv_cell("\tDangerousTab") == "'\tDangerousTab"
    assert sanitize_csv_cell("Normal Song Title") == "Normal Song Title"
    assert sanitize_csv_cell(1234) == "1234"
    assert sanitize_csv_cell(None) == ""


def test_export_csv_endpoint(client, auth, app):
    """Test CSV export endpoint returns valid CSV file with formula-safe values."""
    auth.login_artist()

    with app.app_context():
        camp = Campaign.query.filter_by(campaign_name="Initial Spotify Push").first()
        m = CampaignMetric(
            campaign_id=camp.campaign_id,
            metric_date=date.today(),
            impressions=500,
            clicks=40,
            engagement=25,
            reported_streams=35,
            spend=10.00,
            data_source="manual_entry",
            notes="=DDE('calc')"  # Formula payload to verify escaping
        )
        from indietrack import db
        db.session.add(m)
        db.session.commit()

    resp = client.get("/analytics/export")
    assert resp.status_code == 200
    assert resp.mimetype == "text/csv"
    assert "attachment;" in resp.headers["Content-Disposition"]
    
    # Verify formula was sanitized with leading apostrophe
    content = resp.data.decode("utf-8")
    assert "'=DDE('calc')" in content or "''=DDE" in content
    assert "IndieTrack Analytics Report" in content
    assert "manual_entry" in content
