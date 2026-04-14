import click
from flask.cli import with_appcontext

from .extensions import db
from .models import ChurchGroup, District, User

DEFAULT_DISTRICTS = [
    "Judea",
    "Jerusalem",
    "Zion",
    "Samaria",
    "Jordan",
    "Canaan",
    "Jericho",
    "Bethsaida",
    "Bethlehem",
    "Israel",
    "Nazareth",
    "Galilee",
    "Macedonia",
]

DEFAULT_GROUPS = [
    "Women's Guild (PWG)",
    "Presbyterian Men's Fellowship (PCMF)",
    "Youth Fellowship",
    "Church School (Sunday School)",
    "Boys Brigade",
    "Girls Brigade",
    "Church Choir",
    "Evangelism Committee",
    "Health Board",
    "JPRC",
    "Christian Education Committee",
    "Development Committee",
]


@click.command("init-db")
@with_appcontext
def init_db_command():
    db.create_all()
    click.echo("Database tables created.")


@click.command("seed")
@click.option("--admin-email", default="admin@pceangecha.co.ke", show_default=True)
@click.option("--admin-password", default="ChangeMe123!", show_default=True)
@with_appcontext
def seed_command(admin_email: str, admin_password: str):
    for district_name in DEFAULT_DISTRICTS:
        exists = District.query.filter_by(name=district_name).first()
        if not exists:
            district = District()
            district.name = district_name
            district.is_active = True
            db.session.add(district)

    for group_name in DEFAULT_GROUPS:
        exists = ChurchGroup.query.filter_by(name=group_name).first()
        if not exists:
            church_group = ChurchGroup()
            church_group.name = group_name
            church_group.is_active = True
            db.session.add(church_group)

    admin_user = User.query.filter_by(email=admin_email.lower()).first()
    if not admin_user:
        admin_user = User()
        admin_user.name = "System Administrator"
        admin_user.email = admin_email.lower()
        admin_user.role = "admin"
        admin_user.set_password(admin_password)
        db.session.add(admin_user)

    db.session.commit()
    click.echo("Seed data created or refreshed successfully.")


def register_commands(app):
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_command)
