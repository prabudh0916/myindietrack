from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from indietrack import db
from indietrack.models.song import Song
from indietrack.forms.music_forms import SongForm
from indietrack.services.auth_service import login_required, get_current_user, verify_song_ownership
from indietrack.services.audit_service import AuditService

songs_bp = Blueprint("songs", __name__)


@songs_bp.route("/")
@login_required
def index():
    """Music library page with search, status filtering, and sorting."""
    user = get_current_user()
    if not user.artist_profile:
        return redirect(url_for("auth.profile"))

    query = Song.query.filter_by(artist_id=user.artist_profile.artist_id)

    # Search filter
    search_term = request.args.get("q", "").strip()
    if search_term:
        query = query.filter(
            (Song.title.ilike(f"%{search_term}%")) |
            (Song.genre.ilike(f"%{search_term}%"))
        )

    # Status filter
    status_filter = request.args.get("status", "").strip()
    if status_filter in ["demo", "in-progress", "mastered", "archived"]:
        query = query.filter_by(status=status_filter)

    # Sort
    sort_by = request.args.get("sort", "created_at_desc")
    if sort_by == "title_asc":
        query = query.order_by(Song.title.asc())
    elif sort_by == "title_desc":
        query = query.order_by(Song.title.desc())
    elif sort_by == "created_at_asc":
        query = query.order_by(Song.created_at.asc())
    else:
        query = query.order_by(Song.created_at.desc())

    songs = query.all()
    return render_template(
        "songs/index.html",
        songs=songs,
        search_term=search_term,
        status_filter=status_filter,
        sort_by=sort_by
    )


@songs_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    """Create a new song."""
    user = get_current_user()
    if not user.artist_profile:
        return redirect(url_for("auth.profile"))

    form = SongForm()
    if form.validate_on_submit():
        song = Song(
            artist_id=user.artist_profile.artist_id,
            title=form.title.data.strip(),
            genre=form.genre.data.strip(),
            duration_seconds=form.duration_seconds.data,
            status=form.status.data,
            description=form.description.data.strip() if form.description.data else None
        )
        db.session.add(song)
        db.session.commit()

        AuditService.log("SONG_CREATED", "Song", song.song_id, f"Created song: '{song.title}'")
        flash(f"Song '{song.title}' has been added to your library.", "success")
        return redirect(url_for("songs.detail", song_id=song.song_id))

    return render_template("songs/form.html", form=form, title="Add New Song", is_edit=False)


@songs_bp.route("/<int:song_id>")
@login_required
def detail(song_id: int):
    """View song details, release schedule, and promotional campaigns."""
    user = get_current_user()
    song = db.session.get(Song, song_id)
    if not song:
        abort(404)

    if not verify_song_ownership(song, user):
        abort(403)

    return render_template("songs/detail.html", song=song)


@songs_bp.route("/<int:song_id>/edit", methods=["GET", "POST"])
@login_required
def edit(song_id: int):
    """Edit existing song record with ownership verification."""
    user = get_current_user()
    song = db.session.get(Song, song_id)
    if not song:
        abort(404)

    if not verify_song_ownership(song, user):
        abort(403)

    form = SongForm(obj=song)
    if form.validate_on_submit():
        song.title = form.title.data.strip()
        song.genre = form.genre.data.strip()
        song.duration_seconds = form.duration_seconds.data
        song.status = form.status.data
        song.description = form.description.data.strip() if form.description.data else None
        db.session.commit()

        AuditService.log("SONG_UPDATED", "Song", song.song_id, f"Updated song: '{song.title}'")
        flash(f"Song '{song.title}' updated successfully.", "success")
        return redirect(url_for("songs.detail", song_id=song.song_id))

    return render_template("songs/form.html", form=form, song=song, title=f"Edit: {song.title}", is_edit=True)


@songs_bp.route("/<int:song_id>/delete", methods=["POST"])
@login_required
def delete(song_id: int):
    """Delete a song and cascaded releases/campaigns with ownership verification."""
    user = get_current_user()
    song = db.session.get(Song, song_id)
    if not song:
        abort(404)

    if not verify_song_ownership(song, user):
        abort(403)

    title = song.title
    db.session.delete(song)
    db.session.commit()

    AuditService.log("SONG_DELETED", "Song", song_id, f"Deleted song: '{title}'")
    flash(f"Song '{title}' and all associated releases and campaigns have been deleted.", "info")
    return redirect(url_for("songs.index"))
