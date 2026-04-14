from flask import Flask, render_template

from config import get_config

from .extensions import csrf, db, login_manager, mail, migrate


def create_app(config_name: str | None = None):
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    from . import models  # noqa: F401
    from .blueprints.api.routes import bp as api_bp
    from .blueprints.admin.routes import bp as admin_bp
    from .blueprints.auth.routes import bp as auth_bp
    from .blueprints.main.routes import bp as main_bp
    from .commands import register_commands

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    register_commands(app)

    @app.route("/health")
    def health_check():
        return {"status": "ok", "service": "pcea-ngecha"}, 200

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_error):
        return render_template("errors/500.html"), 500

    return app
