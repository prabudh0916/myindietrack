from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from indietrack import db
from indietrack.models.campaign import Campaign, CampaignMetric
from indietrack.forms.campaign_forms import MetricForm
from indietrack.services.auth_service import login_required, get_current_user, verify_campaign_ownership
from indietrack.services.audit_service import AuditService

metrics_bp = Blueprint("metrics", __name__)


@metrics_bp.route("/<int:campaign_id>/add", methods=["POST"])
@login_required
def add(campaign_id: int):
    """Add dated empirical metric entry to campaign."""
    user = get_current_user()
    campaign = Campaign.query.get_or_404(campaign_id)

    if not verify_campaign_ownership(campaign, user):
        abort(403)

    form = MetricForm()
    if form.validate_on_submit():
        metric = CampaignMetric(
            campaign_id=campaign.campaign_id,
            metric_date=form.metric_date.data,
            impressions=form.impressions.data,
            clicks=form.clicks.data,
            engagement=form.engagement.data,
            reported_streams=form.reported_streams.data,
            spend=form.spend.data,
            data_source=form.data_source.data,
            notes=form.notes.data.strip() if form.notes.data else None
        )
        db.session.add(metric)
        db.session.commit()

        AuditService.log("METRIC_ADDED", "CampaignMetric", metric.metric_id, f"Added {metric.data_source} metric for {metric.metric_date} to {campaign.campaign_name}")
        flash(f"Performance metrics for {metric.metric_date} recorded successfully.", "success")
        return redirect(url_for("campaigns.detail", campaign_id=campaign.campaign_id))

    flash("Validation error while saving metrics. Please ensure all values are non-negative.", "danger")
    return redirect(url_for("campaigns.detail", campaign_id=campaign.campaign_id))


@metrics_bp.route("/<int:metric_id>/edit", methods=["GET", "POST"])
@login_required
def edit(metric_id: int):
    """Edit existing metric entry with ownership verification."""
    user = get_current_user()
    metric = CampaignMetric.query.get_or_404(metric_id)

    if not verify_campaign_ownership(metric.campaign, user):
        abort(403)

    form = MetricForm(obj=metric)
    if form.validate_on_submit():
        metric.metric_date = form.metric_date.data
        metric.impressions = form.impressions.data
        metric.clicks = form.clicks.data
        metric.engagement = form.engagement.data
        metric.reported_streams = form.reported_streams.data
        metric.spend = form.spend.data
        metric.data_source = form.data_source.data
        metric.notes = form.notes.data.strip() if form.notes.data else None
        db.session.commit()

        AuditService.log("METRIC_UPDATED", "CampaignMetric", metric.metric_id, f"Updated metric for {metric.metric_date}")
        flash(f"Metric entry for {metric.metric_date} updated successfully.", "success")
        return redirect(url_for("campaigns.detail", campaign_id=metric.campaign_id))

    return render_template("metrics/form.html", form=form, metric=metric, campaign=metric.campaign)


@metrics_bp.route("/<int:metric_id>/delete", methods=["POST"])
@login_required
def delete(metric_id: int):
    """Delete metric entry with ownership verification."""
    user = get_current_user()
    metric = CampaignMetric.query.get_or_404(metric_id)
    campaign_id = metric.campaign_id

    if not verify_campaign_ownership(metric.campaign, user):
        abort(403)

    db.session.delete(metric)
    db.session.commit()

    AuditService.log("METRIC_DELETED", "CampaignMetric", metric_id, f"Deleted metric from campaign {campaign_id}")
    flash("Metric entry deleted.", "info")
    return redirect(url_for("campaigns.detail", campaign_id=campaign_id))
