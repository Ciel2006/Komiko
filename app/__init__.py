import os
from flask import Flask, g, redirect, url_for, request, session
from config import config
from app.models import db, User, ServerConfig


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    @app.template_filter("basename")
    def basename_filter(path):
        return os.path.basename(path)

    os.makedirs(app.config["DATA_DIR"], exist_ok=True)
    os.makedirs(app.config["COVER_DIR"], exist_ok=True)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    from app.routes.pages import pages_bp
    from app.routes.api import api_bp
    from app.routes.libraries import libraries_bp
    from app.routes.auth import auth_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(libraries_bp, url_prefix="/api/libraries")
    app.register_blueprint(auth_bp, url_prefix="/auth")

    @app.before_request
    def load_user():
        user_id = session.get("user_id")
        g.user = User.query.get(user_id) if user_id else None
        g.server_name = ServerConfig.get("server_name", "Komiko")
        g.is_setup = ServerConfig.is_setup_done()

    @app.context_processor
    def inject_globals():
        return {
            "server_name": getattr(g, "server_name", "Komiko"),
            "is_setup": getattr(g, "is_setup", False),
            "current_user": getattr(g, "user", None),
        }

    @app.before_request
    def require_setup_or_login():
        if request.endpoint == "auth.reset":
            return

        if not ServerConfig.is_setup_done():
            allowed = ("auth.setup", "auth.validate_path", "static")
            if request.endpoint and request.endpoint not in allowed:
                return redirect(url_for("auth.setup"))
            return

        if session.get("setup_in_progress"):
            allowed = ("auth.setup", "auth.validate_path", "static")
            if request.endpoint and request.endpoint not in allowed:
                return redirect(url_for("auth.setup"))
            return

        if not session.get("user_id"):
            allowed = ("auth.login", "auth.setup", "static")
            if request.endpoint and request.endpoint not in allowed:
                return redirect(url_for("auth.login"))

    return app