from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, DecimalField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, URL


class CampaignForm(FlaskForm):
    """Form to manage a promotional marketing campaign."""
    song_id = SelectField("Target Song", coerce=int, validators=[
        DataRequired(message="Please select the song being promoted.")
    ])
    campaign_name = StringField("Campaign Name", validators=[
        DataRequired(message="Campaign name is required."),
        Length(min=2, max=200, message="Campaign name must be between 2 and 200 characters.")
    ])
    platform = SelectField("Promotional Platform / Channel", choices=[
        ("Spotify", "Spotify Ads & Marquee"),
        ("YouTube", "YouTube Ads & Shorts Promo"),
        ("Instagram", "Instagram Reels & Feed Boost"),
        ("TikTok", "TikTok Spark Ads & Creator Sounds"),
        ("Meta Ads", "Meta Ads Manager (FB/IG)"),
        ("Apple Music", "Apple Music Pitch Campaign"),
        ("SoundCloud", "SoundCloud Promoted Track"),
        ("Other", "Other Channel")
    ], validators=[DataRequired()])
    objective = SelectField("Primary Objective", choices=[
        ("awareness", "Brand Awareness & Discovery"),
        ("pre-save", "Pre-Save / Pre-Order Campaign"),
        ("streams", "Direct Streams & Playlist Adds"),
        ("engagement", "Audience Engagement & Follows"),
        ("merch", "Live Shows & Merchandise Sales")
    ], default="awareness", validators=[DataRequired()])
    budget = DecimalField("Budget (USD)", places=2, validators=[
        DataRequired(message="Budget is required."),
        NumberRange(min=0.00, message="Budget cannot be negative.")
    ], default=0.00)
    start_date = DateField("Campaign Start Date", validators=[
        DataRequired(message="Start date is required.")
    ])
    end_date = DateField("Campaign End Date (Optional)", validators=[
        Optional()
    ])
    status = SelectField("Campaign Status", choices=[
        ("planning", "Planning"),
        ("active", "Active / Running"),
        ("paused", "Paused"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled")
    ], default="planning", validators=[DataRequired()])
    landing_url = StringField("Landing Page / SmartURL / Hyperfollow Link", validators=[
        Optional(),
        Length(max=500)
    ])
    submit = SubmitField("Save Campaign Details")


class MetricForm(FlaskForm):
    """Form to record dated empirical performance metrics."""
    metric_date = DateField("Metric Date", validators=[
        DataRequired(message="Date is required.")
    ])
    impressions = IntegerField("Impressions / Reach (Views)", validators=[
        DataRequired(message="Impressions are required."),
        NumberRange(min=0, message="Impressions must be non-negative.")
    ], default=0)
    clicks = IntegerField("Link Clicks (Swipes / Visits)", validators=[
        DataRequired(message="Clicks are required."),
        NumberRange(min=0, message="Clicks must be non-negative.")
    ], default=0)
    engagement = IntegerField("Engagement (Likes, Shares, Comments, Saves)", validators=[
        DataRequired(message="Engagement is required."),
        NumberRange(min=0, message="Engagement must be non-negative.")
    ], default=0)
    reported_streams = IntegerField("Reported DSP Streams (Estimated / Verified)", validators=[
        DataRequired(message="Streams are required."),
        NumberRange(min=0, message="Streams must be non-negative.")
    ], default=0)
    spend = DecimalField("Spend Amount for Date (USD)", places=2, validators=[
        DataRequired(message="Spend amount is required."),
        NumberRange(min=0.00, message="Spend must be non-negative.")
    ], default=0.00)
    data_source = SelectField("Data Provenance / Source", choices=[
        ("manual_entry", "Manual Entry (Artist / Manager Verified)"),
        ("sample_data", "Sample / Demo Metric Record"),
        ("csv_import", "Platform CSV Export Import")
    ], default="manual_entry", validators=[DataRequired()])
    notes = StringField("Observations / Notes for Date", validators=[
        Optional(),
        Length(max=500)
    ])
    submit = SubmitField("Save Metric Entry")
