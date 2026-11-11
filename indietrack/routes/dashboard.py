from flask import Blueprint, render_template, redirect, url_for, flash
from indietrack.services.auth_service import login_required, get_current_user
from indietrack.services.analytics_service import AnalyticsService

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    """Artist central dashboard with real database-backed KPIs and visual analytics."""
    user = get_current_user()
    if not user.artist_profile:
        flash("Please set up your artist profile to access the analytics workspace.", "info")
        return redirect(url_for("auth.profile"))

    stats = AnalyticsService.get_dashboard_summary(user.artist_profile.artist_id)
    time_series = AnalyticsService.get_time_series_data(user.artist_profile.artist_id)
    platform_dist = AnalyticsService.get_platform_distribution(user.artist_profile.artist_id)

    return render_template(
        "dashboard/index.html",
        user=user,
        profile=user.artist_profile,
        stats=stats,
        time_series=time_series,
        platform_dist=platform_dist
    )
