from functools import wraps
from flask import session, redirect, url_for, flash, request, abort
from indietrack import db
from indietrack.models.user import User, ArtistProfile
from indietrack.models.song import Song
from indietrack.models.release import Release
from indietrack.models.campaign import Campaign
from indietrack.models.asset import Asset


def get_current_user():
    """Retrieve logged-in user object from current session, or None."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    user = db.session.get(User, user_id)
    if user and user.is_active:
        return user
    # If user was deactivated or deleted, clear stale session
    session.pop("user_id", None)
    return None


def login_user(user: User):
    """Establishes an authenticated session for user."""
    session.clear()
    session["user_id"] = user.user_id
    session.permanent = True


def logout_user():
    """Clears authenticated session."""
    session.clear()


def login_required(view_func):
    """Decorator ensuring route can only be accessed by authenticated users."""
    @wraps(view_func)
    def decorated_view(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view_func(*args, **kwargs)
    return decorated_view


def admin_required(view_func):
    """Decorator ensuring route can only be accessed by users with the 'admin' role."""
    @wraps(view_func)
    def decorated_view(*args, **kwargs):
        user = get_current_user()
        if not user or not user.is_admin:
            abort(403)
        return view_func(*args, **kwargs)
    return decorated_view


def artist_required(view_func):
    """Decorator ensuring route is accessed by an active artist with a profile."""
    @wraps(view_func)
    def decorated_view(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        if not user.artist_profile and not user.is_admin:
            flash("Please complete your artist profile first.", "info")
            return redirect(url_for("auth.profile"))
        return view_func(*args, **kwargs)
    return decorated_view


def verify_song_ownership(song: Song, user: User) -> bool:
    """Verifies user owns the song or is an administrator."""
    if not song or not user:
        return False
    if user.is_admin:
        return True
    return bool(user.artist_profile and song.artist_id == user.artist_profile.artist_id)


def verify_release_ownership(release: Release, user: User) -> bool:
    """Verifies user owns the release via song ownership."""
    if not release or not user:
        return False
    if user.is_admin:
        return True
    return bool(user.artist_profile and release.song.artist_id == user.artist_profile.artist_id)


def verify_campaign_ownership(campaign: Campaign, user: User) -> bool:
    """Verifies user owns the campaign via song ownership."""
    if not campaign or not user:
        return False
    if user.is_admin:
        return True
    return bool(user.artist_profile and campaign.song.artist_id == user.artist_profile.artist_id)


def verify_asset_ownership(asset: Asset, user: User) -> bool:
    """Verifies user owns the uploaded asset or is an administrator."""
    if not asset or not user:
        return False
    if user.is_admin:
        return True
    return asset.user_id == user.user_id
