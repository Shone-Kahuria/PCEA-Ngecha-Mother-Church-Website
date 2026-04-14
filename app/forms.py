from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
    TimeField,
)
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=128)],
    )
    submit = SubmitField("Sign In")


class DistrictForm(FlaskForm):
    name = StringField("District Name", validators=[DataRequired(), Length(max=80)])
    description = TextAreaField("Description", validators=[Optional()])
    is_active = BooleanField("Is Active", default=True)
    submit = SubmitField("Save District")


class ElderForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=150)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=255)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    bio = TextAreaField("Bio", validators=[Optional()])
    district_id = SelectField("Assigned District", coerce=int, validators=[Optional()])
    is_active = BooleanField("Is Active", default=True)
    submit = SubmitField("Save Elder")


class MinisterForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=150)])
    title = StringField("Title", validators=[DataRequired(), Length(max=80)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=255)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    bio = TextAreaField("Bio", validators=[Optional()])
    is_reverend = BooleanField("Is Reverend", default=False)
    is_active = BooleanField("Is Active", default=True)
    submit = SubmitField("Save Minister")


class SermonForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    minister_id = SelectField("Preacher", coerce=int, validators=[DataRequired()])
    preached_on = DateField("Date", validators=[DataRequired()])
    scripture = StringField("Scripture", validators=[Optional(), Length(max=120)])
    sermon_series = StringField("Series", validators=[Optional(), Length(max=120)])
    audio_url = StringField("Audio URL", validators=[Optional(), Length(max=500)])
    video_url = StringField("Video URL", validators=[Optional(), Length(max=500)])
    description = TextAreaField("Description", validators=[Optional()])
    submit = SubmitField("Save Sermon")


class EventForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description", validators=[Optional()])
    event_date = DateField("Date", validators=[DataRequired()])
    event_time = TimeField("Time", validators=[Optional()])
    venue = StringField("Venue", validators=[Optional(), Length(max=200)])
    district_id = SelectField("District", coerce=int, validators=[Optional()])
    group_id = SelectField("Group", coerce=int, validators=[Optional()])
    is_featured = BooleanField("Featured", default=False)
    submit = SubmitField("Save Event")


class AnnouncementForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    body = TextAreaField("Message", validators=[DataRequired()])
    start_date = DateField("Start Date", validators=[DataRequired()])
    end_date = DateField("End Date", validators=[Optional()])
    district_id = SelectField("District", coerce=int, validators=[Optional()])
    group_id = SelectField("Group", coerce=int, validators=[Optional()])
    is_active = BooleanField("Is Active", default=True)
    submit = SubmitField("Save Announcement")


class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=150)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    subject = StringField("Subject", validators=[DataRequired(), Length(max=200)])
    message = TextAreaField("Message", validators=[DataRequired()])
    submit = SubmitField("Send Message")


class PrayerRequestForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=150)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=255)])
    request_text = TextAreaField("Prayer Request", validators=[DataRequired()])
    submit = SubmitField("Submit Request")


class NewsletterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    name = StringField("Name", validators=[Optional(), Length(max=150)])
    submit = SubmitField("Subscribe")


class MemberForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=150)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=255)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    district_id = SelectField("District", coerce=int, validators=[DataRequired()])
    is_active = BooleanField("Is Active", default=True)
    submit = SubmitField("Save Member")


class DeaconForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=150)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=255)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    zone = StringField("Zone", validators=[Optional(), Length(max=80)])
    district_id = SelectField("District", coerce=int, validators=[DataRequired()])
    is_active = BooleanField("Is Active", default=True)
    submit = SubmitField("Save Deacon")


class GroupForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=150)])
    category = StringField("Category", validators=[Optional(), Length(max=80)])
    description = TextAreaField("Description", validators=[Optional()])
    patron_elder_id = SelectField("Patron Elder", coerce=int, validators=[Optional()])
    is_active = BooleanField("Is Active", default=True)
    submit = SubmitField("Save Group")


class GroupOfficerForm(FlaskForm):
    member_name = StringField("Officer Name", validators=[DataRequired(), Length(max=150)])
    position = StringField("Position", validators=[DataRequired(), Length(max=80)])
    year = IntegerField("Year", validators=[DataRequired(), NumberRange(min=2000, max=2100)])
    is_current = BooleanField("Current", default=True)
    submit = SubmitField("Save Officer")
