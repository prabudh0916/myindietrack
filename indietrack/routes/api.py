from flask import Blueprint, jsonify, request, abort
from marshmallow import ValidationError
from indietrack import db
from indietrack.models.song import Song
from indietrack.models.campaign import Campaign
from indietrack.schemas.music_schemas import SongSchema, CampaignSchema, MetricSchema
from indietrack.services.auth_service import get_current_user, login_required
from indietrack.services.analytics_service import AnalyticsService

api_bp = Blueprint("api", __name__)


@api_bp.route("/chart/timeseries")
@login_required
def chart_timeseries():
    """
    JSON endpoint for dynamic Chart.js time-series updates.
    Returns: { labels: [...], clicks: [...], streams: [...], spend: [...] }
    """
    user = get_current_user()
    if not user.artist_profile:
        return jsonify({"error": "No artist profile"}), 400

    song_id = request.args.get("song_id", type=int)
    platform = request.args.get("platform", "").strip() or None
    campaign_id = request.args.get("campaign_id", type=int)

    data = AnalyticsService.get_time_series_data(
        artist_id=user.artist_profile.artist_id,
        song_id=song_id,
        platform=platform,
        campaign_id=campaign_id
    )
    return jsonify(data), 200


@api_bp.route("/chart/platforms")
@login_required
def chart_platforms():
    """
    JSON endpoint returning platform distribution for Doughnut chart.
    Returns: { platforms: [...], spend: [...], clicks: [...], streams: [...] }
    """
    user = get_current_user()
    if not user.artist_profile:
        return jsonify({"error": "No artist profile"}), 400

    data = AnalyticsService.get_platform_distribution(artist_id=user.artist_profile.artist_id)
    return jsonify(data), 200


@api_bp.route("/songs", methods=["POST"])
@login_required
def create_song_api():
    """
    Programmatic JSON API to create a song record with explicit schema validation.
    Payload: { "title": "...", "genre": "...", "duration_seconds": 210, "status": "in-progress" }
    """
    user = get_current_user()
    if not user.artist_profile:
        return jsonify({"error": "Artist profile required"}), 403

    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "Missing JSON request body"}), 400

    schema = SongSchema()
    try:
        validated = schema.load(json_data)
    except ValidationError as err:
        return jsonify({"error": "Validation failed", "messages": err.messages}), 422

    song = Song(
        artist_id=user.artist_profile.artist_id,
        title=validated["title"],
        genre=validated["genre"],
        duration_seconds=validated.get("duration_seconds"),
        status=validated.get("status", "in-progress"),
        description=validated.get("description")
    )
    db.session.add(song)
    db.session.commit()

    return jsonify({
        "message": "Song created successfully",
        "song": {
            "song_id": song.song_id,
            "title": song.title,
            "genre": song.genre,
            "status": song.status,
            "created_at": song.created_at.isoformat()
        }
    }), 201
