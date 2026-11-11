from datetime import datetime, timezone
from decimal import Decimal
from indietrack import db


class Campaign(db.Model):
    """Marketing and promotional campaign associated with a song."""
    __tablename__ = "campaigns"

    campaign_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    song_id = db.Column(db.Integer, db.ForeignKey("songs.song_id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_name = db.Column(db.String(200), nullable=False)
    platform = db.Column(db.String(100), nullable=False, index=True)  # Spotify, YouTube, Instagram, TikTok, Meta Ads, etc.
    objective = db.Column(db.String(100), nullable=False, default="awareness")  # awareness, pre-save, streams, engagement
    budget = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="planning", index=True)  # planning, active, paused, completed, cancelled
    landing_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime, 
        nullable=False, 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    song = db.relationship("Song", back_populates="campaigns")
    metrics = db.relationship(
        "CampaignMetric", 
        back_populates="campaign", 
        cascade="all, delete-orphan", 
        order_by="CampaignMetric.metric_date.desc()"
    )
    assets = db.relationship("Asset", back_populates="campaign")

    @property
    def total_impressions(self) -> int:
        return sum(m.impressions for m in self.metrics)

    @property
    def total_clicks(self) -> int:
        return sum(m.clicks for m in self.metrics)

    @property
    def total_engagement(self) -> int:
        return sum(m.engagement for m in self.metrics)

    @property
    def total_reported_streams(self) -> int:
        return sum(m.reported_streams for m in self.metrics)

    @property
    def total_spend(self) -> float:
        return float(sum(m.spend for m in self.metrics))

    @property
    def cost_per_click(self) -> float:
        """Calculates derived Cost Per Click safely avoiding division by zero."""
        clicks = self.total_clicks
        if clicks <= 0:
            return 0.00
        return round(self.total_spend / clicks, 2)

    @property
    def click_through_rate(self) -> float:
        """Calculates CTR percentage safely."""
        imps = self.total_impressions
        if imps <= 0:
            return 0.00
        return round((self.total_clicks / imps) * 100.0, 2)

    @property
    def budget_utilized_pct(self) -> float:
        b = float(self.budget or 0)
        if b <= 0:
            return 0.00
        return round((self.total_spend / b) * 100.0, 1)

    def __repr__(self) -> str:
        return f"<Campaign {self.campaign_id} - '{self.campaign_name}' on {self.platform} ({self.status})>"


class CampaignMetric(db.Model):
    """Dated empirical metrics recorded for a campaign."""
    __tablename__ = "campaign_metrics"

    metric_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.campaign_id", ondelete="CASCADE"), nullable=False, index=True)
    metric_date = db.Column(db.Date, nullable=False, index=True)
    impressions = db.Column(db.Integer, nullable=False, default=0)
    clicks = db.Column(db.Integer, nullable=False, default=0)
    engagement = db.Column(db.Integer, nullable=False, default=0)
    reported_streams = db.Column(db.Integer, nullable=False, default=0)
    spend = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    data_source = db.Column(db.String(50), nullable=False, default="manual_entry")  # manual_entry, sample_data, csv_import
    notes = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    campaign = db.relationship("Campaign", back_populates="metrics")

    @property
    def cost_per_click(self) -> float:
        """Safe cost-per-click calculation for single day entry."""
        if not self.clicks or self.clicks <= 0:
            return 0.00
        return round(float(self.spend) / self.clicks, 2)

    @property
    def click_through_rate(self) -> float:
        if not self.impressions or self.impressions <= 0:
            return 0.00
        return round((self.clicks / self.impressions) * 100.0, 2)

    def __repr__(self) -> str:
        return f"<CampaignMetric {self.metric_id} for Camp {self.campaign_id} on {self.metric_date}>"
