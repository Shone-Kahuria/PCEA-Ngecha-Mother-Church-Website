from functools import wraps
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from ...extensions import db
from ...forms import (
    AlbumForm,
    AnnouncementForm,
    DeaconForm,
    DistrictForm,
    ElderForm,
    EventForm,
    GalleryItemForm,
    GroupForm,
    GroupOfficerForm,
    MemberForm,
    MinisterForm,
    SermonForm,
)
from ...models import (
    Album,
    Announcement,
    Deacon,
    ContactMessage,
    District,
    Elder,
    Event,
    GalleryItem,
    GroupOfficer,
    Member,
    Minister,
    NewsletterSubscriber,
    PrayerRequest,
    Sermon,
    Donation,
    ChurchGroup,
)

bp = Blueprint("admin", __name__, url_prefix="/admin")

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}


def roles_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if current_user.role not in allowed_roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def _optional_fk(value: int | None):
    if not value or value == 0:
        return None
    return value


def _save_uploaded_image(file_storage, folder: str) -> str | None:
    if not file_storage or not getattr(file_storage, "filename", ""):
        return None

    filename = secure_filename(file_storage.filename)
    if not filename:
        raise ValueError("Please choose a valid image file.")

    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_IMAGE_EXTENSIONS))
        raise ValueError(f"Unsupported image format. Allowed: {allowed}.")

    relative_folder = Path("uploads") / folder
    destination_folder = Path(current_app.static_folder) / relative_folder
    destination_folder.mkdir(parents=True, exist_ok=True)

    unique_name = f"{uuid4().hex}.{extension}"
    destination = destination_folder / unique_name
    file_storage.save(destination)

    return url_for("static", filename=f"{relative_folder.as_posix()}/{unique_name}")


def editor_or_admin_required(view):
    return roles_required("admin", "editor")(view)


@bp.route("/login")
def admin_login_redirect():
    return redirect(url_for("auth.login"))


@bp.route("/dashboard")
@login_required
@roles_required("admin", "editor", "viewer")
def dashboard():
    stats = {
        "districts": District.query.count(),
        "elders": Elder.query.filter_by(is_active=True).count(),
        "ministers": Minister.query.filter_by(is_active=True).count(),
        "sermons": Sermon.query.count(),
        "events": Event.query.count(),
        "announcements": Announcement.query.filter_by(is_active=True).count(),
        "members": Member.query.filter_by(is_active=True).count(),
        "prayer_requests": PrayerRequest.query.count(),
    }
    return render_template("admin/dashboard.html", stats=stats)


@bp.route("/districts")
@login_required
@roles_required("admin", "editor", "viewer")
def districts_list():
    districts = District.query.order_by(District.name.asc()).all()
    return render_template("admin/districts_list.html", districts=districts)


@bp.route("/districts/<int:district_id>")
@login_required
@roles_required("admin", "editor", "viewer")
def district_detail(district_id: int):
    district = District.query.get_or_404(district_id)
    return render_template("admin/district_detail.html", district=district)


@bp.route("/districts/new", methods=["GET", "POST"])
@login_required
@editor_or_admin_required
def district_create():
    form = DistrictForm()
    if form.validate_on_submit():
        try:
            image_url = _save_uploaded_image(form.image.data, "districts")
        except ValueError as exc:
            flash(str(exc), "warning")
            return render_template("admin/district_form.html", form=form, district=None)

        district = District(
            name=form.name.data.strip(),
            description=(form.description.data or "").strip() or None,
            image_url=image_url,
            is_active=form.is_active.data,
        )
        db.session.add(district)
        db.session.commit()
        flash("District created successfully.", "success")
        return redirect(url_for("admin.districts_list"))
    return render_template("admin/district_form.html", form=form, district=None)


@bp.route("/districts/<int:district_id>/edit", methods=["GET", "POST"])
@login_required
@editor_or_admin_required
def district_edit(district_id: int):
    district = District.query.get_or_404(district_id)
    form = DistrictForm(obj=district)
    if form.validate_on_submit():
        try:
            image_url = _save_uploaded_image(form.image.data, "districts")
        except ValueError as exc:
            flash(str(exc), "warning")
            return render_template("admin/district_form.html", form=form, district=district)

        district.name = form.name.data.strip()
        district.description = (form.description.data or "").strip() or None
        if image_url:
            district.image_url = image_url
        district.is_active = form.is_active.data
        db.session.commit()
        flash("District updated successfully.", "success")
        return redirect(url_for("admin.districts_list"))
    return render_template("admin/district_form.html", form=form, district=district)


@bp.route("/districts/<int:district_id>/delete", methods=["POST"])
@login_required
@editor_or_admin_required
def district_delete(district_id: int):
    district = District.query.get_or_404(district_id)
    member_count = Member.query.filter_by(district_id=district.id, is_active=True).count()
    if member_count > 0:
        flash("Cannot delete district with active members. Reassign members first.", "warning")
        return redirect(url_for("admin.districts_list"))

    district.is_active = False
    db.session.commit()
    flash("District deactivated successfully.", "success")
    return redirect(url_for("admin.districts_list"))


@bp.route("/elders")
@login_required
@roles_required("admin", "editor", "viewer")
def elders_list():
    elders = Elder.query.order_by(Elder.full_name.asc()).all()
    return render_template("admin/elders_list.html", elders=elders)


@bp.route("/elders/new", methods=["GET", "POST"])
@login_required
@editor_or_admin_required
def elder_create():
    form = ElderForm()
    district_choices = [(0, "Unassigned")] + [
        (d.id, d.name) for d in District.query.order_by(District.name.asc()).all()
    ]
    form.district_id.choices = district_choices

    if form.validate_on_submit():
        try:
            photo_url = _save_uploaded_image(form.photo.data, "elders")
        except ValueError as exc:
            flash(str(exc), "warning")
            return render_template("admin/elder_form.html", form=form, elder=None)

        elder = Elder(
            full_name=form.full_name.data.strip(),
            email=(form.email.data or "").strip().lower() or None,
            phone=(form.phone.data or "").strip() or None,
            bio=(form.bio.data or "").strip() or None,
            photo_url=photo_url,
            district_id=_optional_fk(form.district_id.data),
            is_active=form.is_active.data,
        )
        db.session.add(elder)
        db.session.commit()
        flash("Elder created successfully.", "success")
        return redirect(url_for("admin.elders_list"))
    return render_template("admin/elder_form.html", form=form, elder=None)


@bp.route("/elders/<int:elder_id>/edit", methods=["GET", "POST"])
@login_required
@editor_or_admin_required
def elder_edit(elder_id: int):
    elder = Elder.query.get_or_404(elder_id)
    form = ElderForm(obj=elder)
    district_choices = [(0, "Unassigned")] + [
        (d.id, d.name) for d in District.query.order_by(District.name.asc()).all()
    ]
    form.district_id.choices = district_choices
    if request.method == "GET":
        form.district_id.data = elder.district_id or 0

    if form.validate_on_submit():
        try:
            photo_url = _save_uploaded_image(form.photo.data, "elders")
        except ValueError as exc:
            flash(str(exc), "warning")
            return render_template("admin/elder_form.html", form=form, elder=elder)

        elder.full_name = form.full_name.data.strip()
        elder.email = (form.email.data or "").strip().lower() or None
        elder.phone = (form.phone.data or "").strip() or None
        elder.bio = (form.bio.data or "").strip() or None
        if photo_url:
            elder.photo_url = photo_url
        elder.district_id = _optional_fk(form.district_id.data)
        elder.is_active = form.is_active.data
        db.session.commit()
        flash("Elder updated successfully.", "success")
        return redirect(url_for("admin.elders_list"))
    return render_template("admin/elder_form.html", form=form, elder=elder)


@bp.route("/elders/<int:elder_id>/delete", methods=["POST"])
@login_required
@editor_or_admin_required
def elder_delete(elder_id: int):
    elder = Elder.query.get_or_404(elder_id)
    elder.is_active = False
    db.session.commit()
    flash("Elder deactivated successfully.", "success")
    return redirect(url_for("admin.elders_list"))


@bp.route("/ministers")
@login_required
@roles_required("admin", "editor", "viewer")
def ministers_list():
    ministers = Minister.query.order_by(Minister.full_name.asc()).all()
    return render_template("admin/ministers_list.html", ministers=ministers)


@bp.route("/ministers/new", methods=["GET", "POST"])
@login_required
@editor_or_admin_required
def minister_create():
    form = MinisterForm()
    if form.validate_on_submit():
        try:
            photo_url = _save_uploaded_image(form.photo.data, "ministers")
        except ValueError as exc:
            flash(str(exc), "warning")
            return render_template("admin/minister_form.html", form=form, minister=None)

        minister = Minister(
            full_name=form.full_name.data.strip(),
            title=form.title.data.strip(),
            email=(form.email.data or "").strip().lower() or None,
            phone=(form.phone.data or "").strip() or None,
            bio=(form.bio.data or "").strip() or None,
            photo_url=photo_url,
            is_reverend=form.is_reverend.data,
            is_active=form.is_active.data,
        )
        db.session.add(minister)
        db.session.commit()
        flash("Minister created successfully.", "success")
        return redirect(url_for("admin.ministers_list"))
    return render_template("admin/minister_form.html", form=form, minister=None)


@bp.route("/ministers/<int:minister_id>/edit", methods=["GET", "POST"])
@login_required
@editor_or_admin_required
def minister_edit(minister_id: int):
    minister = Minister.query.get_or_404(minister_id)
    form = MinisterForm(obj=minister)
    if form.validate_on_submit():
        try:
            photo_url = _save_uploaded_image(form.photo.data, "ministers")
        except ValueError as exc:
            flash(str(exc), "warning")
            return render_template("admin/minister_form.html", form=form, minister=minister)

        minister.full_name = form.full_name.data.strip()
        minister.title = form.title.data.strip()
        minister.email = (form.email.data or "").strip().lower() or None
        minister.phone = (form.phone.data or "").strip() or None
        minister.bio = (form.bio.data or "").strip() or None
        if photo_url:
            minister.photo_url = photo_url
        minister.is_reverend = form.is_reverend.data
        minister.is_active = form.is_active.data
        db.session.commit()
        flash("Minister updated successfully.", "success")
        return redirect(url_for("admin.ministers_list"))
    return render_template("admin/minister_form.html", form=form, minister=minister)


@bp.route("/ministers/<int:minister_id>/delete", methods=["POST"])
@login_required
@editor_or_admin_required
def minister_delete(minister_id: int):
    minister = Minister.query.get_or_404(minister_id)
    minister.is_active = False
    db.session.commit()
    flash("Minister deactivated successfully.", "success")
    return redirect(url_for("admin.ministers_list"))


@bp.route("/sermons")
@login_required
@roles_required("admin", "editor", "viewer")
def sermons_list():
    sermons = Sermon.query.order_by(Sermon.preached_on.desc()).all()
    return render_template("admin/sermons_list.html", sermons=sermons)


@bp.route("/sermons/new", methods=["GET", "POST"])
@login_required
@editor_or_admin_required
def sermon_create():
    form = SermonForm()
    form.minister_id.choices = [
        (m.id, f"{m.full_name} ({m.title})")
        for m in Minister.query.filter_by(is_active=True).order_by(Minister.full_name.asc()).all()
    ]
    if not form.minister_id.choices:
        flash("Add at least one minister before creating sermons.", "warning")
        return redirect(url_for("admin.ministers_list"))

    if form.validate_on_submit():
        sermon = Sermon(
            title=form.title.data.strip(),
            minister_id=form.minister_id.data,
            preached_on=form.preached_on.data,
            scripture=(form.scripture.data or "").strip() or None,
            sermon_series=(form.sermon_series.data or "").strip() or None,
            audio_url=(form.audio_url.data or "").strip() or None,
            video_url=(form.video_url.data or "").strip() or None,
            description=(form.description.data or "").strip() or None,
        )
        db.session.add(sermon)
        db.session.commit()
        flash("Sermon created successfully.", "success")
        return redirect(url_for("admin.sermons_list"))
    return render_template("admin/sermon_form.html", form=form, sermon=None)


@bp.route("/sermons/<int:sermon_id>/edit", methods=["GET", "POST"])
@login_required
@editor_or_admin_required
def sermon_edit(sermon_id: int):
    sermon = Sermon.query.get_or_404(sermon_id)
    form = SermonForm(obj=sermon)
    form.minister_id.choices = [
        (m.id, f"{m.full_name} ({m.title})")
        for m in Minister.query.filter_by(is_active=True).order_by(Minister.full_name.asc()).all()
    ]
    if form.validate_on_submit():
        sermon.title = form.title.data.strip()
        sermon.minister_id = form.minister_id.data
        sermon.preached_on = form.preached_on.data
        sermon.scripture = (form.scripture.data or "").strip() or None
        sermon.sermon_series = (form.sermon_series.data or "").strip() or None
        sermon.audio_url = (form.audio_url.data or "").strip() or None
        sermon.video_url = (form.video_url.data or "").strip() or None
        sermon.description = (form.description.data or "").strip() or None
        db.session.commit()
        flash("Sermon updated successfully.", "success")
        return redirect(url_for("admin.sermons_list"))
    return render_template("admin/sermon_form.html", form=form, sermon=sermon)


@bp.route("/sermons/<int:sermon_id>/delete", methods=["POST"])
@login_required
@editor_or_admin_required
def sermon_delete(sermon_id: int):
    sermon = Sermon.query.get_or_404(sermon_id)
    db.session.delete(sermon)
    db.session.commit()
    flash("Sermon deleted successfully.", "success")
    return redirect(url_for("admin.sermons_list"))


@bp.route("/events")
@login_required
@roles_required("admin", "editor", "viewer")
def events_list():
    events = Event.query.order_by(Event.event_date.desc()).all()
    return render_template("admin/events_list.html", events=events)


@bp.route("/events/new", methods=["GET", "POST"])
@login_required
@editor_or_admin_required
def event_create():
    form = EventForm()
    form.district_id.choices = [(0, "Church-wide")] + [
        (d.id, d.name) for d in District.query.order_by(District.name.asc()).all()
    ]
    form.group_id.choices = [(0, "Not group-specific")] + [
        (g.id, g.name) for g in ChurchGroup.query.order_by(ChurchGroup.name.asc()).all()
    ]

    if form.validate_on_submit():
        try:
            image_url = _save_uploaded_image(form.image.data, "events")
        except ValueError as exc:
            flash(str(exc), "warning")
            return render_template("admin/event_form.html", form=form, event=None)

        event = Event(
            title=form.title.data.strip(),
            description=(form.description.data or "").strip() or None,
            event_date=form.event_date.data,
            event_time=form.event_time.data,
            venue=(form.venue.data or "").strip() or None,
            image_url=image_url,
            district_id=_optional_fk(form.district_id.data),
            group_id=_optional_fk(form.group_id.data),
            is_featured=form.is_featured.data,
        )
        db.session.add(event)
        db.session.commit()
        flash("Event created successfully.", "success")
        return redirect(url_for("admin.events_list"))
    return render_template("admin/event_form.html", form=form, event=None)


@bp.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
@editor_or_admin_required
def event_edit(event_id: int):
    event = Event.query.get_or_404(event_id)
    form = EventForm(obj=event)
    form.district_id.choices = [(0, "Church-wide")] + [
        (d.id, d.name) for d in District.query.order_by(District.name.asc()).all()
    ]
    form.group_id.choices = [(0, "Not group-specific")] + [
        (g.id, g.name) for g in ChurchGroup.query.order_by(ChurchGroup.name.asc()).all()
    ]
    if request.method == "GET":
        form.district_id.data = event.district_id or 0
        form.group_id.data = event.group_id or 0

    if form.validate_on_submit():
        try:
            image_url = _save_uploaded_image(form.image.data, "events")
        except ValueError as exc:
            flash(str(exc), "warning")
            return render_template("admin/event_form.html", form=form, event=event)

        event.title = form.title.data.strip()
        event.description = (form.description.data or "").strip() or None
        event.event_date = form.event_date.data
        event.event_time = form.event_time.data
        event.venue = (form.venue.data or "").strip() or None
        if image_url:
            event.image_url = image_url
        event.district_id = _optional_fk(form.district_id.data)
        event.group_id = _optional_fk(form.group_id.data)
        event.is_featured = form.is_featured.data
        db.session.commit()
        flash("Event updated successfully.", "success")
        return redirect(url_for("admin.events_list"))
    return render_template("admin/event_form.html", form=form, event=event)


@bp.route("/events/<int:event_id>/delete", methods=["POST"])
@login_required
@editor_or_admin_required
def event_delete(event_id: int):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash("Event deleted successfully.", "success")
    return redirect(url_for("admin.events_list"))


@bp.route("/announcements")
@login_required
@roles_required("admin", "editor", "viewer")
def announcements_list():
    announcements = Announcement.query.order_by(Announcement.start_date.desc()).all()
    return render_template("admin/announcements_list.html", announcements=announcements)


@bp.route("/announcements/new", methods=["GET", "POST"])
@login_required
@editor_or_admin_required
def announcement_create():
    form = AnnouncementForm()
    form.district_id.choices = [(0, "Church-wide")] + [
        (d.id, d.name) for d in District.query.order_by(District.name.asc()).all()
    ]
    form.group_id.choices = [(0, "All groups")] + [
        (g.id, g.name) for g in ChurchGroup.query.order_by(ChurchGroup.name.asc()).all()
    ]
    if form.validate_on_submit():
        announcement = Announcement(
            title=form.title.data.strip(),
            body=form.body.data.strip(),
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            district_id=_optional_fk(form.district_id.data),
            group_id=_optional_fk(form.group_id.data),
            is_active=form.is_active.data,
        )
        db.session.add(announcement)
        db.session.commit()
        flash("Announcement created successfully.", "success")
        return redirect(url_for("admin.announcements_list"))
    return render_template("admin/announcement_form.html", form=form, announcement=None)


@bp.route("/announcements/<int:announcement_id>/edit", methods=["GET", "POST"])
@login_required
@editor_or_admin_required
def announcement_edit(announcement_id: int):
    announcement = Announcement.query.get_or_404(announcement_id)
    form = AnnouncementForm(obj=announcement)
    form.district_id.choices = [(0, "Church-wide")] + [
        (d.id, d.name) for d in District.query.order_by(District.name.asc()).all()
    ]
    form.group_id.choices = [(0, "All groups")] + [
        (g.id, g.name) for g in ChurchGroup.query.order_by(ChurchGroup.name.asc()).all()
    ]
    if request.method == "GET":
        form.district_id.data = announcement.district_id or 0
        form.group_id.data = announcement.group_id or 0

    if form.validate_on_submit():
        announcement.title = form.title.data.strip()
        announcement.body = form.body.data.strip()
        announcement.start_date = form.start_date.data
        announcement.end_date = form.end_date.data
        announcement.district_id = _optional_fk(form.district_id.data)
        announcement.group_id = _optional_fk(form.group_id.data)
        announcement.is_active = form.is_active.data
        db.session.commit()
        flash("Announcement updated successfully.", "success")
        return redirect(url_for("admin.announcements_list"))
    return render_template("admin/announcement_form.html", form=form, announcement=announcement)


@bp.route("/announcements/<int:announcement_id>/delete", methods=["POST"])
@login_required
@editor_or_admin_required
def announcement_delete(announcement_id: int):
    announcement = Announcement.query.get_or_404(announcement_id)
    announcement.is_active = False
    db.session.commit()
    flash("Announcement archived successfully.", "success")
    return redirect(url_for("admin.announcements_list"))


@bp.route("/members")
@login_required
@roles_required("admin", "editor", "viewer")
def members_list():
    members = Member.query.order_by(Member.full_name.asc()).all()
    return render_template("admin/members_list.html", members=members)


@bp.route("/members/new", methods=["GET", "POST"])
@login_required
@editor_or_admin_required
def member_create():
    form = MemberForm()
    form.district_id.choices = [
        (d.id, d.name) for d in District.query.filter_by(is_active=True).order_by(District.name.asc()).all()
    ]

    if form.validate_on_submit():
        member = Member(
            full_name=form.full_name.data.strip(),
            email=(form.email.data or "").strip().lower() or None,
            phone=(form.phone.data or "").strip() or None,
            district_id=form.district_id.data,
            is_active=form.is_active.data,
        )
        db.session.add(member)
        db.session.commit()
        flash("Member created successfully.", "success")
        return redirect(url_for("admin.members_list"))
    return render_template("admin/member_form.html", form=form, member=None)


@bp.route("/members/<int:member_id>/edit", methods=["GET", "POST"])
@login_required
@editor_or_admin_required
def member_edit(member_id: int):
    member = Member.query.get_or_404(member_id)
    form = MemberForm(obj=member)
    form.district_id.choices = [
        (d.id, d.name) for d in District.query.filter_by(is_active=True).order_by(District.name.asc()).all()
    ]
    if form.validate_on_submit():
        member.full_name = form.full_name.data.strip()
        member.email = (form.email.data or "").strip().lower() or None
        member.phone = (form.phone.data or "").strip() or None
        member.district_id = form.district_id.data
        member.is_active = form.is_active.data
        db.session.commit()
        flash("Member updated successfully.", "success")
        return redirect(url_for("admin.members_list"))
    return render_template("admin/member_form.html", form=form, member=member)


@bp.route("/members/<int:member_id>/delete", methods=["POST"])
@login_required
@editor_or_admin_required
def member_delete(member_id: int):
    member = Member.query.get_or_404(member_id)
    member.is_active = False
    db.session.commit()
    flash("Member deactivated successfully.", "success")
    return redirect(url_for("admin.members_list"))


@bp.route("/deacons")
@login_required
@roles_required("admin", "editor", "viewer")
def deacons_list():
    deacons = Deacon.query.order_by(Deacon.full_name.asc()).all()
    return render_template("admin/deacons_list.html", deacons=deacons)


@bp.route("/deacons/new", methods=["GET", "POST"])
@login_required
@editor_or_admin_required
def deacon_create():
    form = DeaconForm()
    form.district_id.choices = [
        (d.id, d.name) for d in District.query.filter_by(is_active=True).order_by(District.name.asc()).all()
    ]
    if form.validate_on_submit():
        try:
            photo_url = _save_uploaded_image(form.photo.data, "deacons")
        except ValueError as exc:
            flash(str(exc), "warning")
            return render_template("admin/deacon_form.html", form=form, deacon=None)

        deacon = Deacon(
            full_name=form.full_name.data.strip(),
            email=(form.email.data or "").strip().lower() or None,
            phone=(form.phone.data or "").strip() or None,
            zone=(form.zone.data or "").strip() or None,
            photo_url=photo_url,
            district_id=form.district_id.data,
            is_active=form.is_active.data,
        )
        db.session.add(deacon)
        db.session.commit()
        flash("Deacon created successfully.", "success")
        return redirect(url_for("admin.deacons_list"))
    return render_template("admin/deacon_form.html", form=form, deacon=None)


@bp.route("/deacons/<int:deacon_id>/edit", methods=["GET", "POST"])
@login_required
@editor_or_admin_required
def deacon_edit(deacon_id: int):
    deacon = Deacon.query.get_or_404(deacon_id)
    form = DeaconForm(obj=deacon)
    form.district_id.choices = [
        (d.id, d.name) for d in District.query.filter_by(is_active=True).order_by(District.name.asc()).all()
    ]
    if form.validate_on_submit():
        try:
            photo_url = _save_uploaded_image(form.photo.data, "deacons")
        except ValueError as exc:
            flash(str(exc), "warning")
            return render_template("admin/deacon_form.html", form=form, deacon=deacon)

        deacon.full_name = form.full_name.data.strip()
        deacon.email = (form.email.data or "").strip().lower() or None
        deacon.phone = (form.phone.data or "").strip() or None
        deacon.zone = (form.zone.data or "").strip() or None
        if photo_url:
            deacon.photo_url = photo_url
        deacon.district_id = form.district_id.data
        deacon.is_active = form.is_active.data
        db.session.commit()
        flash("Deacon updated successfully.", "success")
        return redirect(url_for("admin.deacons_list"))
    return render_template("admin/deacon_form.html", form=form, deacon=deacon)


@bp.route("/deacons/<int:deacon_id>/delete", methods=["POST"])
@login_required
@editor_or_admin_required
def deacon_delete(deacon_id: int):
    deacon = Deacon.query.get_or_404(deacon_id)
    deacon.is_active = False
    db.session.commit()
    flash("Deacon deactivated successfully.", "success")
    return redirect(url_for("admin.deacons_list"))


@bp.route("/groups")
@login_required
@roles_required("admin", "editor", "viewer")
def groups_list():
    groups = ChurchGroup.query.order_by(ChurchGroup.name.asc()).all()
    return render_template("admin/groups_list.html", groups=groups)


@bp.route("/groups/new", methods=["GET", "POST"])
@login_required
@editor_or_admin_required
def group_create():
    form = GroupForm()
    form.patron_elder_id.choices = [(0, "Unassigned")] + [
        (e.id, e.full_name)
        for e in Elder.query.filter_by(is_active=True).order_by(Elder.full_name.asc()).all()
    ]
    if form.validate_on_submit():
        try:
            image_url = _save_uploaded_image(form.image.data, "groups")
        except ValueError as exc:
            flash(str(exc), "warning")
            return render_template("admin/group_form.html", form=form, group=None)

        group = ChurchGroup(
            name=form.name.data.strip(),
            category=(form.category.data or "").strip() or None,
            description=(form.description.data or "").strip() or None,
            patron_elder_id=_optional_fk(form.patron_elder_id.data),
            image_url=image_url,
            is_active=form.is_active.data,
        )
        db.session.add(group)
        db.session.commit()
        flash("Group created successfully.", "success")
        return redirect(url_for("admin.groups_list"))
    return render_template("admin/group_form.html", form=form, group=None)


@bp.route("/groups/<int:group_id>/edit", methods=["GET", "POST"])
@login_required
@editor_or_admin_required
def group_edit(group_id: int):
    group = ChurchGroup.query.get_or_404(group_id)
    form = GroupForm(obj=group)
    form.patron_elder_id.choices = [(0, "Unassigned")] + [
        (e.id, e.full_name)
        for e in Elder.query.filter_by(is_active=True).order_by(Elder.full_name.asc()).all()
    ]
    if request.method == "GET":
        form.patron_elder_id.data = group.patron_elder_id or 0
    if form.validate_on_submit():
        try:
            image_url = _save_uploaded_image(form.image.data, "groups")
        except ValueError as exc:
            flash(str(exc), "warning")
            return render_template("admin/group_form.html", form=form, group=group)

        group.name = form.name.data.strip()
        group.category = (form.category.data or "").strip() or None
        group.description = (form.description.data or "").strip() or None
        group.patron_elder_id = _optional_fk(form.patron_elder_id.data)
        if image_url:
            group.image_url = image_url
        group.is_active = form.is_active.data
        db.session.commit()
        flash("Group updated successfully.", "success")
        return redirect(url_for("admin.groups_list"))
    return render_template("admin/group_form.html", form=form, group=group)


@bp.route("/groups/<int:group_id>/delete", methods=["POST"])
@login_required
@editor_or_admin_required
def group_delete(group_id: int):
    group = ChurchGroup.query.get_or_404(group_id)
    group.is_active = False
    db.session.commit()
    flash("Group deactivated successfully.", "success")
    return redirect(url_for("admin.groups_list"))


@bp.route("/groups/<int:group_id>/officers")
@login_required
@roles_required("admin", "editor", "viewer")
def group_officers_list(group_id: int):
    group = ChurchGroup.query.get_or_404(group_id)
    officers = GroupOfficer.query.filter_by(group_id=group.id).order_by(GroupOfficer.year.desc()).all()
    return render_template("admin/group_officers_list.html", group=group, officers=officers)


@bp.route("/groups/<int:group_id>/officers/new", methods=["GET", "POST"])
@login_required
@editor_or_admin_required
def group_officer_create(group_id: int):
    group = ChurchGroup.query.get_or_404(group_id)
    form = GroupOfficerForm()
    if form.validate_on_submit():
        officer = GroupOfficer(
            group_id=group.id,
            member_name=form.member_name.data.strip(),
            position=form.position.data.strip(),
            year=form.year.data,
            is_current=form.is_current.data,
        )
        db.session.add(officer)
        db.session.commit()
        flash("Group officer added successfully.", "success")
        return redirect(url_for("admin.group_officers_list", group_id=group.id))
    return render_template("admin/group_officer_form.html", form=form, group=group, officer=None)


@bp.route("/groups/<int:group_id>/officers/<int:officer_id>/edit", methods=["GET", "POST"])
@login_required
@editor_or_admin_required
def group_officer_edit(group_id: int, officer_id: int):
    group = ChurchGroup.query.get_or_404(group_id)
    officer = GroupOfficer.query.filter_by(id=officer_id, group_id=group.id).first_or_404()
    form = GroupOfficerForm(obj=officer)
    if form.validate_on_submit():
        officer.member_name = form.member_name.data.strip()
        officer.position = form.position.data.strip()
        officer.year = form.year.data
        officer.is_current = form.is_current.data
        db.session.commit()
        flash("Group officer updated successfully.", "success")
        return redirect(url_for("admin.group_officers_list", group_id=group.id))
    return render_template("admin/group_officer_form.html", form=form, group=group, officer=officer)


@bp.route("/groups/<int:group_id>/officers/<int:officer_id>/delete", methods=["POST"])
@login_required
@editor_or_admin_required
def group_officer_delete(group_id: int, officer_id: int):
    officer = GroupOfficer.query.filter_by(id=officer_id, group_id=group_id).first_or_404()
    db.session.delete(officer)
    db.session.commit()
    flash("Group officer removed successfully.", "success")
    return redirect(url_for("admin.group_officers_list", group_id=group_id))


@bp.route("/gallery")
@login_required
@roles_required("admin", "editor", "viewer")
def gallery_list():
    albums = Album.query.order_by(Album.event_date.desc()).all()
    items = GalleryItem.query.order_by(GalleryItem.created_at.desc()).all()
    return render_template("admin/gallery_list.html", albums=albums, items=items)


@bp.route("/gallery/albums/new", methods=["GET", "POST"])
@login_required
@editor_or_admin_required
def gallery_album_create():
    form = AlbumForm()
    if form.validate_on_submit():
        try:
            cover_image_url = _save_uploaded_image(form.cover_image.data, "gallery/albums")
        except ValueError as exc:
            flash(str(exc), "warning")
            return render_template("admin/album_form.html", form=form, album=None)

        album = Album(
            name=form.name.data.strip(),
            event_date=form.event_date.data,
            description=(form.description.data or "").strip() or None,
            cover_image_url=cover_image_url,
        )
        db.session.add(album)
        db.session.commit()
        flash("Album created successfully.", "success")
        return redirect(url_for("admin.gallery_list"))

    return render_template("admin/album_form.html", form=form, album=None)


@bp.route("/gallery/albums/<int:album_id>/edit", methods=["GET", "POST"])
@login_required
@editor_or_admin_required
def gallery_album_edit(album_id: int):
    album = Album.query.get_or_404(album_id)
    form = AlbumForm(obj=album)
    if form.validate_on_submit():
        try:
            cover_image_url = _save_uploaded_image(form.cover_image.data, "gallery/albums")
        except ValueError as exc:
            flash(str(exc), "warning")
            return render_template("admin/album_form.html", form=form, album=album)

        album.name = form.name.data.strip()
        album.event_date = form.event_date.data
        album.description = (form.description.data or "").strip() or None
        if cover_image_url:
            album.cover_image_url = cover_image_url
        db.session.commit()
        flash("Album updated successfully.", "success")
        return redirect(url_for("admin.gallery_list"))

    return render_template("admin/album_form.html", form=form, album=album)


@bp.route("/gallery/albums/<int:album_id>/delete", methods=["POST"])
@login_required
@editor_or_admin_required
def gallery_album_delete(album_id: int):
    album = Album.query.get_or_404(album_id)
    if album.items:
        flash("Cannot delete album with gallery items. Remove items first.", "warning")
        return redirect(url_for("admin.gallery_list"))

    db.session.delete(album)
    db.session.commit()
    flash("Album deleted successfully.", "success")
    return redirect(url_for("admin.gallery_list"))


@bp.route("/gallery/items/new", methods=["GET", "POST"])
@login_required
@editor_or_admin_required
def gallery_item_create():
    form = GalleryItemForm()
    form.album_id.choices = [(0, "No album")] + [
        (album.id, album.name) for album in Album.query.order_by(Album.event_date.desc()).all()
    ]

    if form.validate_on_submit():
        try:
            image_url = _save_uploaded_image(form.image.data, "gallery/items")
        except ValueError as exc:
            flash(str(exc), "warning")
            return render_template("admin/gallery_item_form.html", form=form, item=None)

        if not image_url:
            flash("Please upload an image for this gallery item.", "warning")
            return render_template("admin/gallery_item_form.html", form=form, item=None)

        item = GalleryItem(
            title=form.title.data.strip(),
            image_url=image_url,
            album_id=_optional_fk(form.album_id.data),
            description=(form.description.data or "").strip() or None,
        )
        db.session.add(item)
        db.session.commit()
        flash("Gallery item created successfully.", "success")
        return redirect(url_for("admin.gallery_list"))

    return render_template("admin/gallery_item_form.html", form=form, item=None)


@bp.route("/gallery/items/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
@editor_or_admin_required
def gallery_item_edit(item_id: int):
    item = GalleryItem.query.get_or_404(item_id)
    form = GalleryItemForm(obj=item)
    form.album_id.choices = [(0, "No album")] + [
        (album.id, album.name) for album in Album.query.order_by(Album.event_date.desc()).all()
    ]
    if request.method == "GET":
        form.album_id.data = item.album_id or 0

    if form.validate_on_submit():
        try:
            image_url = _save_uploaded_image(form.image.data, "gallery/items")
        except ValueError as exc:
            flash(str(exc), "warning")
            return render_template("admin/gallery_item_form.html", form=form, item=item)

        item.title = form.title.data.strip()
        item.album_id = _optional_fk(form.album_id.data)
        item.description = (form.description.data or "").strip() or None
        if image_url:
            item.image_url = image_url
        db.session.commit()
        flash("Gallery item updated successfully.", "success")
        return redirect(url_for("admin.gallery_list"))

    return render_template("admin/gallery_item_form.html", form=form, item=item)


@bp.route("/gallery/items/<int:item_id>/delete", methods=["POST"])
@login_required
@editor_or_admin_required
def gallery_item_delete(item_id: int):
    item = GalleryItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("Gallery item deleted successfully.", "success")
    return redirect(url_for("admin.gallery_list"))


@bp.route("/newsletter")
@login_required
@roles_required("admin", "editor", "viewer")
def newsletter_list():
    subscribers = NewsletterSubscriber.query.order_by(NewsletterSubscriber.subscribed_at.desc()).all()
    return render_template("admin/newsletter_list.html", subscribers=subscribers)


@bp.route("/settings")
@login_required
@roles_required("admin")
def settings():
    return render_template("admin/settings.html")


@bp.route("/donations")
@login_required
@roles_required("admin", "editor", "viewer")
def donations_list():
    donations = Donation.query.order_by(Donation.donated_on.desc()).all()
    return render_template("admin/donations_list.html", donations=donations)


@bp.route("/prayer-requests")
@login_required
@roles_required("admin", "editor", "viewer")
def prayer_requests_list():
    prayer_requests = PrayerRequest.query.order_by(PrayerRequest.submitted_at.desc()).all()
    return render_template("admin/prayer_requests_list.html", prayer_requests=prayer_requests)


@bp.route("/contact-messages")
@login_required
@roles_required("admin", "editor", "viewer")
def contact_messages_list():
    messages = ContactMessage.query.order_by(ContactMessage.submitted_at.desc()).all()
    return render_template("admin/contact_messages_list.html", messages=messages)
