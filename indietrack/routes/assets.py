from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, Response, current_app
from indietrack.models.asset import Asset
from indietrack.models.song import Song
from indietrack.models.campaign import Campaign
from indietrack.services.auth_service import login_required, get_current_user, verify_asset_ownership
from indietrack.services.storage_service import StorageService
from indietrack.services.audit_service import AuditService
from config import Config

assets_bp = Blueprint("assets", __name__)


@assets_bp.route("/")
@login_required
def index():
    """List uploaded assets with storage configuration status indicator."""
    user = get_current_user()
    assets = Asset.query.filter_by(user_id=user.user_id).order_by(Asset.created_at.desc()).all()

    # Query songs and campaigns for association dropdowns
    songs = []
    campaigns = []
    if user.artist_profile:
        songs = Song.query.filter_by(artist_id=user.artist_profile.artist_id).all()
        campaigns = Campaign.query.join(Song).filter(Song.artist_id == user.artist_profile.artist_id).all()

    # Determine live Azure connectivity status without exposing keys
    azure_configured = Config.is_azure_storage_configured()
    azure_connected, azure_status_msg = StorageService.test_azure_connection() if azure_configured else (False, "Azure Blob Storage not configured; using local development adapter.")

    return render_template(
        "assets/index.html",
        assets=assets,
        songs=songs,
        campaigns=campaigns,
        azure_configured=azure_configured,
        azure_connected=azure_connected,
        azure_status_msg=azure_status_msg,
        allowed_extensions=", ".join(sorted(Config.ALLOWED_EXTENSIONS)),
        max_size_mb=Config.MAX_CONTENT_LENGTH // (1024 * 1024)
    )


@assets_bp.route("/upload", methods=["POST"])
@login_required
def upload():
    """Upload asset file to Azure Blob Storage or local fallback."""
    user = get_current_user()
    if "file" not in request.files:
        flash("No file was attached to upload request.", "warning")
        return redirect(url_for("assets.index"))

    file = request.files["file"]
    song_id = request.form.get("song_id", type=int)
    campaign_id = request.form.get("campaign_id", type=int)

    # Clean empty values
    if song_id == 0:
        song_id = None
    if campaign_id == 0:
        campaign_id = None

    asset, error_msg = StorageService.upload_file(
        file_storage=file,
        user_id=user.user_id,
        song_id=song_id,
        campaign_id=campaign_id
    )

    if error_msg:
        flash(f"Upload failed: {error_msg}", "danger")
        return redirect(url_for("assets.index"))

    AuditService.log("ASSET_UPLOADED", "Asset", asset.asset_id, f"Uploaded '{asset.original_filename}' ({asset.formatted_size}) via {asset.storage_backend}")
    flash(f"File '{asset.original_filename}' uploaded successfully to {asset.storage_backend}.", "success")
    return redirect(url_for("assets.index"))


@assets_bp.route("/<int:asset_id>/download")
@login_required
def download(asset_id: int):
    """Download asset via backend-authorized streaming after strict ownership check."""
    user = get_current_user()
    asset = Asset.query.get_or_404(asset_id)

    if not verify_asset_ownership(asset, user):
        abort(403)

    data, content_type, filename = StorageService.get_asset_stream(asset)
    if data is None:
        flash("File content could not be located in storage backend.", "danger")
        return redirect(url_for("assets.index"))

    AuditService.log("ASSET_DOWNLOADED", "Asset", asset.asset_id, f"Downloaded '{filename}'")

    response = Response(data, mimetype=content_type)
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@assets_bp.route("/<int:asset_id>/delete", methods=["POST"])
@login_required
def delete(asset_id: int):
    """Delete asset from storage backend and database."""
    user = get_current_user()
    asset = Asset.query.get_or_404(asset_id)

    if not verify_asset_ownership(asset, user):
        abort(403)

    filename = asset.original_filename
    success = StorageService.delete_asset(asset)

    if success:
        AuditService.log("ASSET_DELETED", "Asset", asset_id, f"Deleted asset '{filename}'")
        flash(f"Asset '{filename}' removed from storage.", "info")
    else:
        flash("Failed to delete asset from storage.", "danger")

    return redirect(url_for("assets.index"))
