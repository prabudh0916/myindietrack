from datetime import date, datetime, timedelta
from sqlalchemy import func
from indietrack import db
from indietrack.models.song import Song
from indietrack.models.release import Release
from indietrack.models.campaign import Campaign, CampaignMetric


class AnalyticsService:
    """Computes aggregated KPIs and Chart.js datasets from database queries."""

    @classmethod
    def get_dashboard_summary(cls, artist_id: int) -> dict:
        """Computes top-level KPI metrics and recent items for the artist dashboard."""
        today = date.today()

        # 1. Total Songs
        total_songs = Song.query.filter_by(artist_id=artist_id).count()

        # 2. Upcoming Releases
        upcoming_releases_query = (
            Release.query.join(Song)
            .filter(Song.artist_id == artist_id)
            .filter(Release.release_date >= today)
            .filter(Release.status.in_(["scheduled", "planned"]))
            .order_by(Release.release_date.asc())
        )
        upcoming_releases_count = upcoming_releases_query.count()
        upcoming_releases_list = upcoming_releases_query.limit(5).all()

        # 3. Active Campaigns
        active_campaigns = (
            Campaign.query.join(Song)
            .filter(Song.artist_id == artist_id)
            .filter(Campaign.status == "active")
            .count()
        )

        # 4. Aggregated Metrics via SQL JOIN & SUM
        metrics_agg = (
            db.session.query(
                func.coalesce(func.sum(CampaignMetric.impressions), 0).label("total_impressions"),
                func.coalesce(func.sum(CampaignMetric.clicks), 0).label("total_clicks"),
                func.coalesce(func.sum(CampaignMetric.engagement), 0).label("total_engagement"),
                func.coalesce(func.sum(CampaignMetric.reported_streams), 0).label("total_streams"),
                func.coalesce(func.sum(CampaignMetric.spend), 0.00).label("total_spend"),
                func.max(CampaignMetric.data_source).label("any_source")
            )
            .join(Campaign, CampaignMetric.campaign_id == Campaign.campaign_id)
            .join(Song, Campaign.song_id == Song.song_id)
            .filter(Song.artist_id == artist_id)
            .first()
        )

        total_impressions = int(metrics_agg.total_impressions) if metrics_agg else 0
        total_clicks = int(metrics_agg.total_clicks) if metrics_agg else 0
        total_engagement = int(metrics_agg.total_engagement) if metrics_agg else 0
        total_streams = int(metrics_agg.total_streams) if metrics_agg else 0
        total_spend = float(metrics_agg.total_spend) if metrics_agg else 0.0

        # Safe derived calculations
        cost_per_click = round(total_spend / total_clicks, 2) if total_clicks > 0 else 0.00
        click_through_rate = round((total_clicks / total_impressions) * 100.0, 2) if total_impressions > 0 else 0.00
        cost_per_stream = round(total_spend / total_streams, 2) if total_streams > 0 else 0.00

        # Check if sample data exists in the database
        has_sample_data = (
            CampaignMetric.query.join(Campaign).join(Song)
            .filter(Song.artist_id == artist_id)
            .filter(CampaignMetric.data_source == "sample_data")
            .first() is not None
        )

        # Recent Campaign performance (last 5 active or completed)
        recent_campaigns = (
            Campaign.query.join(Song)
            .filter(Song.artist_id == artist_id)
            .order_by(Campaign.created_at.desc())
            .limit(5)
            .all()
        )

        return {
            "total_songs": total_songs,
            "upcoming_releases_count": upcoming_releases_count,
            "upcoming_releases_list": upcoming_releases_list,
            "active_campaigns": active_campaigns,
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_engagement": total_engagement,
            "total_streams": total_streams,
            "total_spend": total_spend,
            "cost_per_click": cost_per_click,
            "click_through_rate": click_through_rate,
            "cost_per_stream": cost_per_stream,
            "has_sample_data": has_sample_data,
            "recent_campaigns": recent_campaigns
        }

    @classmethod
    def get_time_series_data(cls, artist_id: int, start_date=None, end_date=None, song_id=None, platform=None, campaign_id=None) -> dict:
        """Returns date-grouped metrics for Chart.js line charts."""
        query = (
            db.session.query(
                CampaignMetric.metric_date,
                func.sum(CampaignMetric.impressions).label("impressions"),
                func.sum(CampaignMetric.clicks).label("clicks"),
                func.sum(CampaignMetric.engagement).label("engagement"),
                func.sum(CampaignMetric.reported_streams).label("streams"),
                func.sum(CampaignMetric.spend).label("spend")
            )
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

        results = query.group_by(CampaignMetric.metric_date).order_by(CampaignMetric.metric_date.asc()).all()

        labels = [r.metric_date.strftime("%Y-%m-%d") for r in results]
        clicks = [int(r.clicks or 0) for r in results]
        streams = [int(r.streams or 0) for r in results]
        spend = [float(r.spend or 0.0) for r in results]
        impressions = [int(r.impressions or 0) for r in results]
        engagement = [int(r.engagement or 0) for r in results]

        return {
            "labels": labels,
            "clicks": clicks,
            "streams": streams,
            "spend": spend,
            "impressions": impressions,
            "engagement": engagement
        }

    @classmethod
    def get_platform_distribution(cls, artist_id: int) -> dict:
        """Returns spend and click distribution grouped by platform for Doughnut/Bar charts."""
        results = (
            db.session.query(
                Campaign.platform,
                func.sum(CampaignMetric.spend).label("total_spend"),
                func.sum(CampaignMetric.clicks).label("total_clicks"),
                func.sum(CampaignMetric.reported_streams).label("total_streams")
            )
            .join(CampaignMetric, Campaign.campaign_id == CampaignMetric.campaign_id)
            .join(Song, Campaign.song_id == Song.song_id)
            .filter(Song.artist_id == artist_id)
            .group_by(Campaign.platform)
            .all()
        )

        platforms = [r.platform for r in results]
        spend = [float(r.total_spend or 0.0) for r in results]
        clicks = [int(r.total_clicks or 0) for r in results]
        streams = [int(r.total_streams or 0) for r in results]

        return {
            "platforms": platforms,
            "spend": spend,
            "clicks": clicks,
            "streams": streams
        }
