from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange


class SongForm(FlaskForm):
    """Form to create or update a song."""
    title = StringField("Song Title", validators=[
        DataRequired(message="Song title is required."),
        Length(min=1, max=200, message="Title must be between 1 and 200 characters.")
    ])
    genre = StringField("Genre", validators=[
        DataRequired(message="Genre is required."),
        Length(max=100)
    ])
    duration_seconds = IntegerField("Duration in Seconds (e.g. 210 for 3:30)", validators=[
        Optional(),
        NumberRange(min=1, max=7200, message="Duration must be between 1 and 7200 seconds.")
    ])
    status = SelectField("Song Status", choices=[
        ("demo", "Demo / Scratch Idea"),
        ("in-progress", "In Progress / Recording"),
        ("mastered", "Mastered / Ready for Release"),
        ("archived", "Archived")
    ], default="in-progress", validators=[DataRequired()])
    description = TextAreaField("Description & Production Notes", validators=[
        Optional(),
        Length(max=2000)
    ])
    submit = SubmitField("Save Song Record")


class ReleaseForm(FlaskForm):
    """Form to schedule and manage a commercial release."""
    song_id = SelectField("Associated Song", coerce=int, validators=[
        DataRequired(message="Please select an associated song.")
    ])
    release_date = DateField("Scheduled Release Date", validators=[
        DataRequired(message="Valid release date is required.")
    ])
    release_type = SelectField("Release Type", choices=[
        ("single", "Digital Single"),
        ("ep", "EP (Extended Play)"),
        ("album", "Full Album"),
        ("remix", "Remix / Alternative Edit")
    ], default="single", validators=[DataRequired()])
    status = SelectField("Release Status", choices=[
        ("draft", "Draft / Concept"),
        ("planned", "Planned / Scheduling"),
        ("scheduled", "Scheduled on Distribution Platform"),
        ("released", "Live & Released"),
        ("cancelled", "Cancelled")
    ], default="planned", validators=[DataRequired()])
    notes = TextAreaField("Distribution Details & ISRC / UPC Notes", validators=[
        Optional(),
        Length(max=2000)
    ])
    submit = SubmitField("Save Release Schedule")
