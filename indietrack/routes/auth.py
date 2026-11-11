from flask import Blueprint, render_template, redirect, url_for, flash, request
from indietrack import db, limiter
from indietrack.models.user import User, ArtistProfile
from indietrack.forms.auth_forms import LoginForm, RegisterForm, ProfileForm, ChangePasswordForm
from indietrack.services.auth_service import login_user, logout_user, login_required, get_current_user
from indietrack.services.audit_service import AuditService

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    """User login view."""
    if get_current_user():
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash("This account has been deactivated. Please contact an administrator.", "danger")
                return render_template("auth/login.html", form=form)

            login_user(user)
            AuditService.log("USER_LOGIN", "User", user.user_id, f"Login successful for {user.email}")
            flash(f"Welcome back to IndieTrack, {user.artist_profile.artist_name if user.artist_profile else user.email}!", "success")

            next_url = request.args.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect(url_for("dashboard.index"))
        else:
            AuditService.log("FAILED_LOGIN_ATTEMPT", "User", details=f"Failed login attempt for {form.email.data}")
            flash("Invalid email address or password.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Artist registration view creating User and 1-to-1 ArtistProfile in atomic transaction."""
    if get_current_user():
        return redirect(url_for("dashboard.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("An account with this email address already exists. Please log in.", "warning")
            return render_template("auth/register.html", form=form)

        try:
            # Atomic creation of User and ArtistProfile
            user = User(email=email, role="artist", is_active=True)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()  # Generate user.user_id

            profile = ArtistProfile(
                user_id=user.user_id,
                artist_name=form.artist_name.data.strip(),
                primary_genre=form.primary_genre.data.strip()
            )
            db.session.add(profile)
            db.session.commit()

            AuditService.log("USER_REGISTER", "User", user.user_id, f"Registered new artist: {profile.artist_name}")
            login_user(user)
            flash(f"Account successfully created! Welcome to IndieTrack, {profile.artist_name}.", "success")
            return redirect(url_for("dashboard.index"))

        except Exception as e:
            db.session.rollback()
            flash("An error occurred during account registration. Please try again.", "danger")

    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout")
def logout():
    """Logs out current user."""
    user = get_current_user()
    if user:
        AuditService.log("USER_LOGOUT", "User", user.user_id, f"Logged out {user.email}")
    logout_user()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("main.index"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """View and update artist profile settings."""
    user = get_current_user()
    profile = user.artist_profile
    if not profile:
        profile = ArtistProfile(user_id=user.user_id, artist_name="Artist")
        db.session.add(profile)
        db.session.commit()

    form = ProfileForm(obj=profile)
    pwd_form = ChangePasswordForm()

    if form.validate_on_submit() and "submit_profile" in request.form:
        profile.artist_name = form.artist_name.data.strip()
        profile.primary_genre = form.primary_genre.data.strip()
        profile.country = form.country.data.strip() if form.country.data else None
        profile.bio = form.bio.data.strip() if form.bio.data else None
        db.session.commit()

        AuditService.log("PROFILE_UPDATE", "ArtistProfile", profile.artist_id, "Updated profile information")
        flash("Profile updated successfully.", "success")
        return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html", user=user, profile=profile, form=form, pwd_form=pwd_form)


@auth_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    """Changes user password after verifying current password."""
    user = get_current_user()
    pwd_form = ChangePasswordForm()

    if pwd_form.validate_on_submit():
        if not user.check_password(pwd_form.current_password.data):
            flash("Current password is incorrect.", "danger")
            return redirect(url_for("auth.profile"))

        user.set_password(pwd_form.new_password.data)
        db.session.commit()
        AuditService.log("PASSWORD_CHANGED", "User", user.user_id, "Password updated successfully")
        flash("Your password has been changed successfully.", "success")
        return redirect(url_for("auth.profile"))

    flash("Please review the password requirements.", "danger")
    return redirect(url_for("auth.profile"))
