from datetime import datetime, date, timezone
from flask import Blueprint, render_template, request, Response, redirect, url_for, flash, current_app
from indietrack import db
from indietrack.models.song import Song
from indietrack.models.campaign import Campaign, CampaignMetric
from indietrack.services.auth_service import login_required, get_current_user
from indietrack.services.analytics_service import AnalyticsService
from indietrack.services.export_service import ExportService
from indietrack.services.audit_service import AuditService

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/")
@login_required
def index():
    """Deep-dive analytics dashboard with multi-dimensional filtering."""
    user = get_current_user()
    if not user.artist_profile:
        return redirect(url_for("auth.profile"))

    artist_id = user.artist_profile.artist_id

    # Filter parameters
    start_date_str = request.args.get("start_date", "").strip()
    end_date_str = request.args.get("end_date", "").strip()
    song_id = request.args.get("song_id", type=int)
    platform = request.args.get("platform", "").strip()
    campaign_id = request.args.get("campaign_id", type=int)

    start_date = None
    end_date = None
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    # Build filtered query for table and summary
    query = (
        db.session.query(CampaignMetric, Campaign, Song)
        .join(Campaign, CampaignMetric.campaign_id == Campaign.campaign_id)
        .join(Song, Campaign.song_id == Song.song_id)
        .filter(Song.artist_id == artist_id)
    )

    if start_date:
        query = query.filter(CampaignMetric.metric_date >= start_date)
    if end_date:
        query = query.filter(CampaignMetric.metric_date <= end_date)
    if song_id:
        query = query.filter(Song.song_id == song_id)
    if platform:
        query = query.filter(Campaign.platform == platform)
    if campaign_id:
        query = query.filter(Campaign.campaign_id == campaign_id)

    records = query.order_by(CampaignMetric.metric_date.desc()).all()

    # Calculate filtered KPI totals
    total_imps = sum(r[0].impressions for r in records)
    total_clicks = sum(r[0].clicks for r in records)
    total_eng = sum(r[0].engagement for r in records)
    total_streams = sum(r[0].reported_streams for r in records)
    total_spend = sum(float(r[0].spend) for r in records)
    overall_cpc = round(total_spend / total_clicks, 2) if total_clicks > 0 else 0.00
    overall_ctr = round((total_clicks / total_imps) * 100.0, 2) if total_imps > 0 else 0.00

    has_sample_data = any(r[0].data_source == "sample_data" for r in records)

    # Time series for charts
    time_series = AnalyticsService.get_time_series_data(
        artist_id, start_date=start_date, end_date=end_date, song_id=song_id, platform=platform, campaign_id=campaign_id
    )
    platform_dist = AnalyticsService.get_platform_distribution(artist_id)

    # Filter options for select dropdowns
    artist_songs = Song.query.filter_by(artist_id=artist_id).order_by(Song.title.asc()).all()
    artist_campaigns = Campaign.query.join(Song).filter(Song.artist_id == artist_id).order_by(Campaign.campaign_name.asc()).all()
    platforms = ["Spotify", "YouTube", "Instagram", "TikTok", "Meta Ads", "Apple Music", "SoundCloud", "Other"]

    return render_template(
        "analytics/index.html",
        records=records,
        total_imps=total_imps,
        total_clicks=total_clicks,
        total_eng=total_eng,
        total_streams=total_streams,
        total_spend=total_spend,
        overall_cpc=overall_cpc,
        overall_ctr=overall_ctr,
        has_sample_data=has_sample_data,
        time_series=time_series,
        platform_dist=platform_dist,
        artist_songs=artist_songs,
        artist_campaigns=artist_campaigns,
        platforms=platforms,
        selected_song=song_id,
        selected_platform=platform,
        selected_campaign=campaign_id,
        start_date=start_date_str,
        end_date=end_date_str,
        is_dev_mode=(current_app.config.get("ENV") == "development" or current_app.debug)
    )


@analytics_bp.route("/export")
@login_required
def export_csv():
    """Export filtered metrics report to CSV with protection against spreadsheet formula injection."""
    user = get_current_user()
    if not user.artist_profile:
        return redirect(url_for("auth.profile"))

    artist_id = user.artist_profile.artist_id

    # Read active filters
    start_date_str = request.args.get("start_date", "").strip()
    end_date_str = request.args.get("end_date", "").strip()
    song_id = request.args.get("song_id", type=int)
    platform = request.args.get("platform", "").strip()
    campaign_id = request.args.get("campaign_id", type=int)

    query = (
        db.session.query(CampaignMetric, Campaign, Song)
        .join(Campaign, CampaignMetric.campaign_id == Campaign.campaign_id)
        .join(Song, Campaign.song_id == Song.song_id)
        .filter(Song.artist_id == artist_id)
    )

    if start_date_str:
        try:
            query = query.filter(CampaignMetric.metric_date >= datetime.strptime(start_date_str, "%Y-%m-%d").date())
        except ValueError:
            pass
    if end_date_str:
        try:
            query = query.filter(CampaignMetric.metric_date <= datetime.strptime(end_date_str, "%Y-%m-%d").date())
        except ValueError:
            pass
    if song_id:
        query = query.filter(Song.song_id == song_id)
    if platform:
        query = query.filter(Campaign.platform == platform)
    if campaign_id:
        query = query.filter(Campaign.campaign_id == campaign_id)

    results = query.order_by(CampaignMetric.metric_date.asc()).all()

    export_rows = []
    for m, c, s in results:
        export_rows.append({
            "metric_id": m.metric_id,
            "metric_date": m.metric_date.strftime("%Y-%m-%d"),
            "song_title": s.title,
            "campaign_name": c.campaign_name,
            "platform": c.platform,
            "impressions": m.impressions,
            "clicks": m.clicks,
            "engagement": m.engagement,
            "reported_streams": m.reported_streams,
            "spend": float(m.spend),
            "data_source": m.data_source,
            "notes": m.notes or ""
        })

    csv_data = ExportService.generate_campaign_csv_report(export_rows, user.artist_profile.artist_name)
    AuditService.log("REPORT_EXPORTED_CSV", "Analytics", details=f"Exported {len(export_rows)} metric rows to CSV")

    filename = f"indietrack_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    response = Response(csv_data, mimetype="text/csv")
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@analytics_bp.route("/clear-sample-data", methods=["POST"])
@login_required
def clear_sample_data():
    """Removes all sample/demo metrics for logged in artist so only user-entered records remain."""
    user = get_current_user()
    if not user.artist_profile:
        return redirect(url_for("auth.profile"))

    artist_id = user.artist_profile.artist_id
    sample_metrics = (
        CampaignMetric.query.join(Campaign).join(Song)
        .filter(Song.artist_id == artist_id)
        .filter(CampaignMetric.data_source == "sample_data")
        .all()
    )

    count = len(sample_metrics)
    for sm in sample_metrics:
        db.session.delete(sm)
    db.session.commit()

    AuditService.log("SAMPLE_DATA_CLEARED", "CampaignMetric", details=f"Cleared {count} sample data metrics")
    flash(f"Cleared {count} sample data entries. Your dashboard now reflects only your manually recorded data.", "info")
    return redirect(url_for("analytics.index"))
