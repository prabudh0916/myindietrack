from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from indietrack import db
from indietrack.models.song import Song
from indietrack.models.campaign import Campaign
from indietrack.forms.campaign_forms import CampaignForm, MetricForm
from indietrack.services.auth_service import login_required, get_current_user, verify_campaign_ownership
from indietrack.services.audit_service import AuditService

campaigns_bp = Blueprint("campaigns", __name__)


@campaigns_bp.route("/")
@login_required
def index():
    """List promotional campaigns for artist with platform and status filters."""
    user = get_current_user()
    if not user.artist_profile:
        return redirect(url_for("auth.profile"))

    artist_id = user.artist_profile.artist_id
    query = Campaign.query.join(Song).filter(Song.artist_id == artist_id)

    # Filter by platform
    platform_filter = request.args.get("platform", "").strip()
    if platform_filter:
        query = query.filter(Campaign.platform == platform_filter)

    # Filter by status
    status_filter = request.args.get("status", "").strip()
    if status_filter:
        query = query.filter(Campaign.status == status_filter)

    campaigns = query.order_by(Campaign.start_date.desc()).all()
    platforms = [
        "Spotify", "YouTube", "Instagram", "TikTok", "Meta Ads", "Apple Music", "SoundCloud", "Other"
    ]

    return render_template(
        "campaigns/index.html",
        campaigns=campaigns,
        platforms=platforms,
        platform_filter=platform_filter,
        status_filter=status_filter
    )


@campaigns_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    """Create new promotional campaign."""
    user = get_current_user()
    if not user.artist_profile:
        return redirect(url_for("auth.profile"))

    artist_songs = Song.query.filter_by(artist_id=user.artist_profile.artist_id).order_by(Song.title.asc()).all()
    if not artist_songs:
        flash("You need to add at least one song to your library before creating a campaign.", "warning")
        return redirect(url_for("songs.create"))

    form = CampaignForm()
    form.song_id.choices = [(s.song_id, f"{s.title} ({s.genre})") for s in artist_songs]

    preselected_song = request.args.get("song_id", type=int)
    if preselected_song and any(s.song_id == preselected_song for s in artist_songs):
        form.song_id.data = preselected_song

    if form.validate_on_submit():
        selected_song = db.session.get(Song, form.song_id.data)
        if not selected_song or selected_song.artist_id != user.artist_profile.artist_id:
            abort(403)

        campaign = Campaign(
            song_id=form.song_id.data,
            campaign_name=form.campaign_name.data.strip(),
            platform=form.platform.data,
            objective=form.objective.data,
            budget=form.budget.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            status=form.status.data,
            landing_url=form.landing_url.data.strip() if form.landing_url.data else None
        )
        db.session.add(campaign)
        db.session.commit()

        AuditService.log("CAMPAIGN_CREATED", "Campaign", campaign.campaign_id, f"Created campaign '{campaign.campaign_name}' on {campaign.platform}")
        flash(f"Campaign '{campaign.campaign_name}' created successfully.", "success")
        return redirect(url_for("campaigns.detail", campaign_id=campaign.campaign_id))

    return render_template("campaigns/form.html", form=form, title="Create Promotion Campaign", is_edit=False)


@campaigns_bp.route("/<int:campaign_id>")
@login_required
def detail(campaign_id: int):
    """View campaign details, performance KPIs, and dated metric history."""
    user = get_current_user()
    campaign = Campaign.query.get_or_404(campaign_id)

    if not verify_campaign_ownership(campaign, user):
        abort(403)

    metric_form = MetricForm()
    return render_template(
        "campaigns/detail.html",
        campaign=campaign,
        metric_form=metric_form
    )


@campaigns_bp.route("/<int:campaign_id>/edit", methods=["GET", "POST"])
@login_required
def edit(campaign_id: int):
    """Edit campaign details with ownership verification."""
    user = get_current_user()
    campaign = Campaign.query.get_or_404(campaign_id)

    if not verify_campaign_ownership(campaign, user):
        abort(403)

    artist_songs = Song.query.filter_by(artist_id=user.artist_profile.artist_id).order_by(Song.title.asc()).all()
    form = CampaignForm(obj=campaign)
    form.song_id.choices = [(s.song_id, f"{s.title} ({s.genre})") for s in artist_songs]

    if form.validate_on_submit():
        selected_song = Song.query.get(form.song_id.data)
        if not selected_song or selected_song.artist_id != user.artist_profile.artist_id:
            abort(403)

        campaign.song_id = form.song_id.data
        campaign.campaign_name = form.campaign_name.data.strip()
        campaign.platform = form.platform.data
        campaign.objective = form.objective.data
        campaign.budget = form.budget.data
        campaign.start_date = form.start_date.data
        campaign.end_date = form.end_date.data
        campaign.status = form.status.data
        campaign.landing_url = form.landing_url.data.strip() if form.landing_url.data else None
        db.session.commit()

        AuditService.log("CAMPAIGN_UPDATED", "Campaign", campaign.campaign_id, f"Updated campaign '{campaign.campaign_name}'")
        flash(f"Campaign '{campaign.campaign_name}' updated successfully.", "success")
        return redirect(url_for("campaigns.detail", campaign_id=campaign.campaign_id))

    return render_template("campaigns/form.html", form=form, campaign=campaign, title="Edit Campaign", is_edit=True)


@campaigns_bp.route("/<int:campaign_id>/delete", methods=["POST"])
@login_required
def delete(campaign_id: int):
    """Delete campaign and associated metrics with ownership verification."""
    user = get_current_user()
    campaign = Campaign.query.get_or_404(campaign_id)

    if not verify_campaign_ownership(campaign, user):
        abort(403)

    name = campaign.campaign_name
    db.session.delete(campaign)
    db.session.commit()

    AuditService.log("CAMPAIGN_DELETED", "Campaign", campaign_id, f"Deleted campaign '{name}'")
    flash(f"Campaign '{name}' and its metrics have been deleted.", "info")
    return redirect(url_for("campaigns.index"))
