from datetime import date, datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ...extensions import db
from ...forms import ContactForm, NewsletterForm, PrayerRequestForm
from ...models import (
    Album,
    Announcement,
    ContactMessage,
    Deacon,
    District,
    Elder,
    Event,
    ChurchGroup,
    Member,
    Minister,
    NewsletterSubscriber,
    PrayerRequest,
    Sermon,
)

bp = Blueprint("main", __name__)


@bp.app_context_processor
def inject_year():
    return {"current_year": datetime.now().year}


@bp.route("/")
def home():
    latest_sermon = Sermon.query.order_by(Sermon.preached_on.desc()).first()
    upcoming_events = (
        Event.query.filter(Event.event_date >= date.today())
        .order_by(Event.event_date.asc())
        .limit(3)
        .all()
    )
    announcements = (
        Announcement.query.filter_by(is_active=True)
        .order_by(Announcement.start_date.desc())
        .limit(5)
        .all()
    )
    newsletter_form = NewsletterForm()

    return render_template(
        "main/home.html",
        latest_sermon=latest_sermon,
        upcoming_events=upcoming_events,
        announcements=announcements,
        newsletter_form=newsletter_form,
    )


@bp.route("/about")
def about():
    return render_template("main/about.html")


@bp.route("/our-team")
def our_team():
    ministers = Minister.query.filter_by(is_active=True).order_by(Minister.full_name.asc()).all()
    elders = Elder.query.filter_by(is_active=True).order_by(Elder.full_name.asc()).all()
    deacons = Deacon.query.filter_by(is_active=True).order_by(Deacon.full_name.asc()).all()
    return render_template(
        "main/our_team.html",
        ministers=ministers,
        elders=elders,
        deacons=deacons,
    )


@bp.route("/sermons")
def sermons():
    preacher_id = request.args.get("preacher", type=int)
    query = Sermon.query.order_by(Sermon.preached_on.desc())
    if preacher_id:
        query = query.filter(Sermon.minister_id == preacher_id)

    sermons_list = query.all()
    ministers = Minister.query.filter_by(is_active=True).order_by(Minister.full_name.asc()).all()
    return render_template(
        "main/sermons.html",
        sermons=sermons_list,
        ministers=ministers,
        preacher_id=preacher_id,
    )


@bp.route("/sermons/<int:sermon_id>")
def sermon_detail(sermon_id: int):
    sermon = Sermon.query.get_or_404(sermon_id)
    return render_template("main/sermon_detail.html", sermon=sermon)


@bp.route("/events")
def events():
    district_id = request.args.get("district", type=int)
    group_id = request.args.get("group", type=int)

    query = Event.query.order_by(Event.event_date.asc())
    if district_id:
        query = query.filter(Event.district_id == district_id)
    if group_id:
        query = query.filter(Event.group_id == group_id)

    events_list = query.all()
    districts = District.query.filter_by(is_active=True).order_by(District.name.asc()).all()
    groups = ChurchGroup.query.filter_by(is_active=True).order_by(ChurchGroup.name.asc()).all()

    return render_template(
        "main/events.html",
        events=events_list,
        districts=districts,
        groups=groups,
        district_id=district_id,
        group_id=group_id,
    )


@bp.route("/events/<int:event_id>")
def event_detail(event_id: int):
    event = Event.query.get_or_404(event_id)
    return render_template("main/event_detail.html", event=event)


@bp.route("/districts")
def districts():
    districts_list = District.query.filter_by(is_active=True).order_by(District.name.asc()).all()
    return render_template("main/districts.html", districts=districts_list)


@bp.route("/districts/<int:district_id>")
def district_detail(district_id: int):
    district = District.query.get_or_404(district_id)
    member_count = Member.query.filter_by(district_id=district.id, is_active=True).count()
    return render_template("main/district_detail.html", district=district, member_count=member_count)


@bp.route("/groups")
def groups():
    groups_list = ChurchGroup.query.filter_by(is_active=True).order_by(ChurchGroup.name.asc()).all()
    return render_template("main/groups.html", groups=groups_list)


@bp.route("/groups/<int:group_id>")
def group_detail(group_id: int):
    group = ChurchGroup.query.get_or_404(group_id)
    return render_template("main/group_detail.html", group=group)


@bp.route("/gallery")
def gallery():
    albums = Album.query.order_by(Album.event_date.desc()).all()
    return render_template("main/gallery.html", albums=albums)


@bp.route("/give")
def give():
    return render_template("main/give.html")


@bp.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        message = ContactMessage(
            name=form.name.data.strip(),
            email=form.email.data.strip().lower(),
            phone=(form.phone.data or "").strip() or None,
            subject=form.subject.data.strip(),
            message=form.message.data.strip(),
        )
        db.session.add(message)
        db.session.commit()
        flash("Your message has been sent successfully.", "success")
        return redirect(url_for("main.contact"))

    return render_template("main/contact.html", form=form)


@bp.route("/prayer", methods=["GET", "POST"])
def prayer():
    form = PrayerRequestForm()
    if form.validate_on_submit():
        prayer_request = PrayerRequest(
            name=form.name.data.strip(),
            email=(form.email.data or "").strip().lower() or None,
            request_text=form.request_text.data.strip(),
        )
        db.session.add(prayer_request)
        db.session.commit()
        flash("Prayer request submitted. Our prayer team is with you.", "success")
        return redirect(url_for("main.prayer"))

    return render_template("main/prayer.html", form=form)


@bp.route("/announcements")
def announcements():
    announcement_items = (
        Announcement.query.filter_by(is_active=True)
        .order_by(Announcement.start_date.desc())
        .all()
    )
    return render_template("main/announcements.html", announcements=announcement_items)


@bp.route("/newsletter/subscribe", methods=["POST"])
def subscribe_newsletter():
    form = NewsletterForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        subscriber = NewsletterSubscriber.query.filter_by(email=email).first()
        if subscriber:
            subscriber.is_active = True
            if form.name.data:
                subscriber.name = form.name.data.strip()
        else:
            subscriber = NewsletterSubscriber(
                email=email,
                name=(form.name.data or "").strip() or None,
            )
            db.session.add(subscriber)

        db.session.commit()
        flash("You are now subscribed to our newsletter.", "success")
    else:
        flash("Please provide a valid email address.", "warning")

    return redirect(url_for("main.home"))
