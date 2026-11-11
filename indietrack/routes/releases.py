from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from indietrack import db
from indietrack.models.song import Song
from indietrack.models.release import Release
from indietrack.forms.music_forms import ReleaseForm
from indietrack.services.auth_service import login_required, get_current_user, verify_release_ownership
from indietrack.services.audit_service import AuditService

releases_bp = Blueprint("releases", __name__)


@releases_bp.route("/")
@login_required
def index():
    """View all scheduled, planned, and past releases for artist."""
    user = get_current_user()
    if not user.artist_profile:
        return redirect(url_for("auth.profile"))

    today = date.today()
    artist_id = user.artist_profile.artist_id

    upcoming_releases = (
        Release.query.join(Song)
        .filter(Song.artist_id == artist_id)
        .filter(Release.release_date >= today)
        .order_by(Release.release_date.asc())
        .all()
    )

    past_releases = (
        Release.query.join(Song)
        .filter(Song.artist_id == artist_id)
        .filter(Release.release_date < today)
        .order_by(Release.release_date.desc())
        .all()
    )

    return render_template(
        "releases/index.html",
        upcoming_releases=upcoming_releases,
        past_releases=past_releases,
        today=today
    )


@releases_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    """Create a new release associated with an artist's song."""
    user = get_current_user()
    if not user.artist_profile:
        return redirect(url_for("auth.profile"))

    # Direct authorization check on POST to prevent attaching to unowned songs
    if request.method == "POST":
        submitted_song_id = request.form.get("song_id", type=int)
        if submitted_song_id:
            target_song = db.session.get(Song, submitted_song_id)
            if not target_song or target_song.artist_id != user.artist_profile.artist_id:
                abort(403)

    artist_songs = Song.query.filter_by(artist_id=user.artist_profile.artist_id).order_by(Song.title.asc()).all()
    if not artist_songs:
        flash("You need to add at least one song to your library before scheduling a release.", "warning")
        return redirect(url_for("songs.create"))

    form = ReleaseForm()
    form.song_id.choices = [(s.song_id, f"{s.title} ({s.genre})") for s in artist_songs]

    preselected_song_id = request.args.get("song_id", type=int)
    if preselected_song_id and any(s.song_id == preselected_song_id for s in artist_songs):
        form.song_id.data = preselected_song_id

    if form.validate_on_submit():
        selected_song = db.session.get(Song, form.song_id.data)
        if not selected_song or selected_song.artist_id != user.artist_profile.artist_id:
            abort(403)

        release = Release(
            song_id=form.song_id.data,
            release_date=form.release_date.data,
            release_type=form.release_type.data,
            status=form.status.data,
            notes=form.notes.data.strip() if form.notes.data else None
        )
        db.session.add(release)
        db.session.commit()

        AuditService.log("RELEASE_CREATED", "Release", release.release_id, f"Scheduled release for '{selected_song.title}' on {release.release_date}")
        flash(f"Release for '{selected_song.title}' scheduled for {release.release_date}.", "success")
        return redirect(url_for("releases.index"))

    return render_template("releases/form.html", form=form, title="Schedule New Release", is_edit=False)


@releases_bp.route("/<int:release_id>/edit", methods=["GET", "POST"])
@login_required
def edit(release_id: int):
    """Edit release details with ownership verification."""
    user = get_current_user()
    release = db.session.get(Release, release_id)
    if not release:
        abort(404)

    if not verify_release_ownership(release, user):
        abort(403)

    artist_songs = Song.query.filter_by(artist_id=user.artist_profile.artist_id).order_by(Song.title.asc()).all()
    form = ReleaseForm(obj=release)
    form.song_id.choices = [(s.song_id, f"{s.title} ({s.genre})") for s in artist_songs]

    if form.validate_on_submit():
        selected_song = db.session.get(Song, form.song_id.data)
        if not selected_song or selected_song.artist_id != user.artist_profile.artist_id:
            abort(403)

        release.song_id = form.song_id.data
        release.release_date = form.release_date.data
        release.release_type = form.release_type.data
        release.status = form.status.data
        release.notes = form.notes.data.strip() if form.notes.data else None
        db.session.commit()

        AuditService.log("RELEASE_UPDATED", "Release", release.release_id, f"Updated release for '{selected_song.title}'")
        flash(f"Release for '{selected_song.title}' updated successfully.", "success")
        return redirect(url_for("releases.index"))

    return render_template("releases/form.html", form=form, release=release, title="Edit Release", is_edit=True)


@releases_bp.route("/<int:release_id>/delete", methods=["POST"])
@login_required
def delete(release_id: int):
    """Delete release schedule with ownership verification."""
    user = get_current_user()
    release = db.session.get(Release, release_id)
    if not release:
        abort(404)

    if not verify_release_ownership(release, user):
        abort(403)

    song_title = release.song.title
    db.session.delete(release)
    db.session.commit()

    AuditService.log("RELEASE_DELETED", "Release", release_id, f"Deleted release for '{song_title}'")
    flash(f"Release schedule for '{song_title}' has been removed.", "info")
    return redirect(url_for("releases.index"))
