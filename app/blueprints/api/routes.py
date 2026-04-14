from flask import Blueprint, jsonify, request

from ...models import Announcement, District, Event, Sermon

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/health")
def health():
    return jsonify({"status": "ok", "api": "v1"}), 200


@bp.route("/sermons")
def sermons():
    limit = request.args.get("limit", 20, type=int)
    records = Sermon.query.order_by(Sermon.preached_on.desc()).limit(limit).all()
    return jsonify(
        [
            {
                "id": sermon.id,
                "title": sermon.title,
                "preacher": sermon.minister.full_name if sermon.minister else None,
                "date": sermon.preached_on.isoformat(),
                "scripture": sermon.scripture,
                "series": sermon.sermon_series,
                "audio_url": sermon.audio_url,
                "video_url": sermon.video_url,
            }
            for sermon in records
        ]
    )


@bp.route("/events")
def events():
    limit = request.args.get("limit", 20, type=int)
    records = Event.query.order_by(Event.event_date.asc()).limit(limit).all()
    return jsonify(
        [
            {
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "date": event.event_date.isoformat(),
                "time": event.event_time.isoformat() if event.event_time else None,
                "venue": event.venue,
                "district": event.district.name if event.district else None,
                "group": event.group.name if event.group else None,
                "is_featured": event.is_featured,
            }
            for event in records
        ]
    )


@bp.route("/announcements")
def announcements():
    records = Announcement.query.filter_by(is_active=True).order_by(Announcement.start_date.desc()).all()
    return jsonify(
        [
            {
                "id": announcement.id,
                "title": announcement.title,
                "body": announcement.body,
                "start_date": announcement.start_date.isoformat(),
                "end_date": announcement.end_date.isoformat() if announcement.end_date else None,
                "district": announcement.district.name if announcement.district else None,
                "group": announcement.group.name if announcement.group else None,
            }
            for announcement in records
        ]
    )


@bp.route("/districts")
def districts():
    records = District.query.filter_by(is_active=True).order_by(District.name.asc()).all()
    return jsonify(
        [
            {
                "id": district.id,
                "name": district.name,
                "description": district.description,
                "elder": district.elder.full_name if district.elder else None,
                "member_count": len(district.members),
            }
            for district in records
        ]
    )
