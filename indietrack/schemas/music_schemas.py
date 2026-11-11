from marshmallow import Schema, fields, validate, post_load


class SongSchema(Schema):
    """Explicit request schema for song data validation."""
    title = fields.String(required=True, validate=validate.Length(min=1, max=200))
    genre = fields.String(required=True, validate=validate.Length(min=1, max=100))
    description = fields.String(allow_none=True, validate=validate.Length(max=2000))
    duration_seconds = fields.Integer(allow_none=True, validate=validate.Range(min=1, max=7200))
    status = fields.String(load_default="in-progress", validate=validate.OneOf(["demo", "in-progress", "mastered", "archived"]))


class ReleaseSchema(Schema):
    """Explicit request schema for release data validation."""
    song_id = fields.Integer(required=True)
    release_date = fields.Date(required=True)
    release_type = fields.String(load_default="single", validate=validate.OneOf(["single", "ep", "album", "remix"]))
    status = fields.String(load_default="planned", validate=validate.OneOf(["draft", "planned", "scheduled", "released", "cancelled"]))
    notes = fields.String(allow_none=True, validate=validate.Length(max=2000))


class CampaignSchema(Schema):
    """Explicit request schema for campaign data validation."""
    song_id = fields.Integer(required=True)
    campaign_name = fields.String(required=True, validate=validate.Length(min=2, max=200))
    platform = fields.String(required=True, validate=validate.Length(min=1, max=100))
    objective = fields.String(load_default="awareness", validate=validate.Length(max=100))
    budget = fields.Decimal(as_string=True, load_default="0.00", validate=validate.Range(min=0.0))
    start_date = fields.Date(required=True)
    end_date = fields.Date(allow_none=True)
    status = fields.String(load_default="planning", validate=validate.OneOf(["planning", "active", "paused", "completed", "cancelled"]))
    landing_url = fields.String(allow_none=True, validate=validate.Length(max=500))


class MetricSchema(Schema):
    """Explicit request schema for campaign metrics validation."""
    campaign_id = fields.Integer(required=True)
    metric_date = fields.Date(required=True)
    impressions = fields.Integer(load_default=0, validate=validate.Range(min=0))
    clicks = fields.Integer(load_default=0, validate=validate.Range(min=0))
    engagement = fields.Integer(load_default=0, validate=validate.Range(min=0))
    reported_streams = fields.Integer(load_default=0, validate=validate.Range(min=0))
    spend = fields.Decimal(as_string=True, load_default="0.00", validate=validate.Range(min=0.0))
    data_source = fields.String(load_default="manual_entry", validate=validate.OneOf(["manual_entry", "sample_data", "csv_import"]))
    notes = fields.String(allow_none=True, validate=validate.Length(max=500))
