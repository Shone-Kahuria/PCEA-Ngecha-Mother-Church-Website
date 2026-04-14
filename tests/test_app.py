from datetime import date

import pytest

from app import create_app
from app.extensions import db
from app.models import Announcement, ChurchGroup, District, Event, Minister, Sermon


@pytest.fixture
def app_instance():
    app = create_app("testing")

    with app.app_context():
        db.create_all()

        district = District()
        district.name = "Judea"
        district.is_active = True

        group = ChurchGroup()
        group.name = "Youth Fellowship"
        group.is_active = True

        minister = Minister()
        minister.full_name = "Rev. John Example"
        minister.title = "Parish Minister"
        minister.is_active = True

        db.session.add(district)
        db.session.add(group)
        db.session.add(minister)
        db.session.flush()

        sermon = Sermon()
        sermon.title = "Faith and Obedience"
        sermon.minister_id = minister.id
        sermon.preached_on = date.today()

        event = Event()
        event.title = "Youth Worship Night"
        event.event_date = date.today()
        event.district_id = district.id
        event.group_id = group.id

        announcement = Announcement()
        announcement.title = "Sunday Combined Service"
        announcement.body = "All districts to gather at 9:00 AM"
        announcement.start_date = date.today()
        announcement.is_active = True

        db.session.add(sermon)
        db.session.add(event)
        db.session.add(announcement)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_public_pages_load(client):
    expected_ok = [
        "/",
        "/about",
        "/our-team",
        "/sermons",
        "/events",
        "/districts",
        "/groups",
        "/gallery",
        "/give",
        "/contact",
        "/prayer",
        "/announcements",
    ]

    for route in expected_ok:
        response = client.get(route)
        assert response.status_code == 200


def test_api_endpoints_return_success(client):
    endpoints = [
        "/api/health",
        "/api/sermons",
        "/api/events",
        "/api/announcements",
        "/api/districts",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 200


def test_admin_requires_authentication(client):
    response = client.get("/admin/dashboard")
    assert response.status_code in (302, 401)
