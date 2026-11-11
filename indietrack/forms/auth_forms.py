from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional


class LoginForm(FlaskForm):
    """User login form with email and password."""
    email = StringField("Email Address", validators=[
        DataRequired(message="Email is required."),
        Email(message="Please enter a valid email address.")
    ])
    password = PasswordField("Password", validators=[
        DataRequired(message="Password is required.")
    ])
    remember_me = BooleanField("Remember this device")
    submit = SubmitField("Sign In to IndieTrack")


class RegisterForm(FlaskForm):
    """Artist registration form."""
    artist_name = StringField("Artist or Band Name", validators=[
        DataRequired(message="Artist name is required."),
        Length(min=2, max=150, message="Artist name must be between 2 and 150 characters.")
    ])
    email = StringField("Email Address", validators=[
        DataRequired(message="Email is required."),
        Email(message="Please enter a valid email address."),
        Length(max=255)
    ])
    primary_genre = StringField("Primary Music Genre", validators=[
        DataRequired(message="Primary genre is required."),
        Length(max=100)
    ])
    password = PasswordField("Password", validators=[
        DataRequired(message="Password is required."),
        Length(min=8, message="Password must be at least 8 characters long.")
    ])
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(message="Please confirm your password."),
        EqualTo("password", message="Passwords must match.")
    ])
    submit = SubmitField("Create Artist Account")


class ProfileForm(FlaskForm):
    """Artist profile update form."""
    artist_name = StringField("Artist Name", validators=[
        DataRequired(message="Artist name is required."),
        Length(min=2, max=150)
    ])
    primary_genre = StringField("Primary Genre", validators=[
        DataRequired(message="Primary genre is required."),
        Length(max=100)
    ])
    country = StringField("Country / City", validators=[
        Optional(),
        Length(max=100)
    ])
    bio = TextAreaField("Artist Bio", validators=[
        Optional(),
        Length(max=2000)
    ])
    submit = SubmitField("Save Profile Details")


class ChangePasswordForm(FlaskForm):
    """Password change form."""
    current_password = PasswordField("Current Password", validators=[
        DataRequired(message="Current password is required.")
    ])
    new_password = PasswordField("New Password", validators=[
        DataRequired(message="New password is required."),
        Length(min=8, message="Password must be at least 8 characters long.")
    ])
    confirm_new_password = PasswordField("Confirm New Password", validators=[
        DataRequired(message="Please confirm your new password."),
        EqualTo("new_password", message="New passwords must match.")
    ])
    submit = SubmitField("Update Password")
