from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db, login_manager


def current_time():
    return datetime.now()


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=current_time, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=current_time,
        onupdate=current_time,
        nullable=False,
    )


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="viewer")
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))


class Minister(TimestampMixin, db.Model):
    __tablename__ = "ministers"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    title = db.Column(db.String(80), nullable=False)
    bio = db.Column(db.Text)
    photo_url = db.Column(db.String(500))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(30))
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_reverend = db.Column(db.Boolean, nullable=False, default=False)


class District(TimestampMixin, db.Model):
    __tablename__ = "districts"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, nullable=False, default=True)


class Elder(TimestampMixin, db.Model):
    __tablename__ = "elders"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    photo_url = db.Column(db.String(500))
    bio = db.Column(db.Text)
    email = db.Column(db.String(255))
    phone = db.Column(db.String(30))
    district_id = db.Column(db.Integer, db.ForeignKey("districts.id"), unique=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    district = db.relationship("District", backref=db.backref("elder", uselist=False))


class Deacon(TimestampMixin, db.Model):
    __tablename__ = "deacons"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    photo_url = db.Column(db.String(500))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(30))
    zone = db.Column(db.String(80))
    district_id = db.Column(db.Integer, db.ForeignKey("districts.id"), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    district = db.relationship("District", backref="deacons")


class Member(TimestampMixin, db.Model):
    __tablename__ = "members"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255))
    phone = db.Column(db.String(30))
    district_id = db.Column(db.Integer, db.ForeignKey("districts.id"), nullable=False)
    date_joined = db.Column(db.Date)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    district = db.relationship("District", backref="members")


class ChurchGroup(TimestampMixin, db.Model):
    __tablename__ = "church_groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    category = db.Column(db.String(80))
    description = db.Column(db.Text)
    patron_elder_id = db.Column(db.Integer, db.ForeignKey("elders.id"))
    image_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    patron_elder = db.relationship("Elder", backref="patroned_groups")


class GroupOfficer(TimestampMixin, db.Model):
    __tablename__ = "group_officers"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("church_groups.id"), nullable=False)
    member_name = db.Column(db.String(150), nullable=False)
    position = db.Column(db.String(80), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    is_current = db.Column(db.Boolean, nullable=False, default=True)

    group = db.relationship("ChurchGroup", backref="officers")


class Sermon(TimestampMixin, db.Model):
    __tablename__ = "sermons"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    minister_id = db.Column(db.Integer, db.ForeignKey("ministers.id"), nullable=False)
    preached_on = db.Column(db.Date, nullable=False)
    scripture = db.Column(db.String(120))
    audio_url = db.Column(db.String(500))
    video_url = db.Column(db.String(500))
    description = db.Column(db.Text)
    sermon_series = db.Column(db.String(120))

    minister = db.relationship("Minister", backref="sermons")


class Event(TimestampMixin, db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.Date, nullable=False)
    event_time = db.Column(db.Time)
    venue = db.Column(db.String(200))
    image_url = db.Column(db.String(500))
    group_id = db.Column(db.Integer, db.ForeignKey("church_groups.id"))
    district_id = db.Column(db.Integer, db.ForeignKey("districts.id"))
    is_featured = db.Column(db.Boolean, nullable=False, default=False)

    group = db.relationship("ChurchGroup", backref="events")
    district = db.relationship("District", backref="events")


class Announcement(TimestampMixin, db.Model):
    __tablename__ = "announcements"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    district_id = db.Column(db.Integer, db.ForeignKey("districts.id"))
    group_id = db.Column(db.Integer, db.ForeignKey("church_groups.id"))
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    district = db.relationship("District", backref="announcements")
    group = db.relationship("ChurchGroup", backref="announcements")


class Album(TimestampMixin, db.Model):
    __tablename__ = "albums"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    event_date = db.Column(db.Date)
    cover_image_url = db.Column(db.String(500))
    description = db.Column(db.Text)


class GalleryItem(TimestampMixin, db.Model):
    __tablename__ = "gallery"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey("albums.id"))
    description = db.Column(db.Text)

    album = db.relationship("Album", backref="items")


class Donation(TimestampMixin, db.Model):
    __tablename__ = "donations"

    id = db.Column(db.Integer, primary_key=True)
    donor_name = db.Column(db.String(150), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    method = db.Column(db.String(80), nullable=False)
    reference = db.Column(db.String(120), unique=True)
    donated_on = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)


class PrayerRequest(TimestampMixin, db.Model):
    __tablename__ = "prayer_requests"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255))
    request_text = db.Column(db.Text, nullable=False)
    is_answered = db.Column(db.Boolean, nullable=False, default=False)
    submitted_at = db.Column(db.DateTime, default=current_time, nullable=False)


class NewsletterSubscriber(TimestampMixin, db.Model):
    __tablename__ = "newsletter_subscribers"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(150))
    subscribed_at = db.Column(db.DateTime, default=current_time, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)


class ContactMessage(TimestampMixin, db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(30))
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=current_time, nullable=False)
