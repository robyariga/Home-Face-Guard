"""One local, same-origin application for the UI and protected API."""

import os
import time
from datetime import timedelta
from pathlib import Path
import click
from flask import Flask, jsonify, request, send_from_directory, g
from werkzeug.exceptions import HTTPException
from werkzeug.security import generate_password_hash
from . import face_engine
from .database import init_db, add_user
from .security import limiter, load_secret, protect_api, security_headers
from .routes.uploads import upload_bp
from .routes.residents import residents_bp
from .routes.events import events_bp
from .routes.model import model_bp
from .routes.recognition import recognition_bp
from .routes.auth import auth_bp

UI_DIR = Path(__file__).resolve().parents[2] / "docs"
PAGES = {"index", "login", "register", "akun", "edit", "scan", "log", "log_detail"}


def create_app(test_config=None):
    face_engine.ensure_dirs()
    app = Flask(__name__, static_folder=None)
    app.config.update(
        SECRET_KEY=load_secret(face_engine.DATASET_DIR),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
        MAX_FORM_MEMORY_SIZE=256 * 1024,
        MAX_FORM_PARTS=128,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Strict",
        SESSION_COOKIE_SECURE=os.getenv("HFG_HTTPS", "0") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        TRUSTED_HOSTS=os.getenv("HFG_TRUSTED_HOSTS", "localhost,127.0.0.1,[::1]").split(
            ","
        ),
        RATELIMIT_STORAGE_URI="memory://",
    )
    if test_config:
        app.config.update(test_config)
    limiter.init_app(app)
    app.before_request(protect_api)
    app.after_request(security_headers)

    last_cleanup = [0.0]

    @app.before_request
    def serialize_state():
        # One process owns the camera/model. Serialize mutation and prediction.
        if request.path.startswith("/api/"):
            face_engine.STATE_LOCK.acquire()
            g.state_locked = True
            if time.monotonic() - last_cleanup[0] >= 300:
                from cleanup_snapshots import cleanup_private_data

                cleanup_private_data()
                last_cleanup[0] = time.monotonic()

    @app.teardown_request
    def release_state(error):
        if g.pop("state_locked", False):
            face_engine.STATE_LOCK.release()

    for bp in (upload_bp, residents_bp, events_bp, model_bp, recognition_bp, auth_bp):
        app.register_blueprint(bp, url_prefix="/api")

    @app.route("/")
    def index():
        return send_from_directory(UI_DIR, "index.html")

    @app.route("/assets/<path:filename>")
    def assets(filename):
        return send_from_directory(UI_DIR / "assets", filename)

    @app.route("/<page>")
    def page(page):
        from flask import abort

        name = page.removesuffix(".html")
        if name not in PAGES:
            abort(404)
        return send_from_directory(UI_DIR, name + ".html")

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(message=error.description, error=error.name), error.code

    @app.errorhandler(ValueError)
    def invalid_input(error):
        return jsonify(message=str(error)), 400

    @app.cli.command("create-admin")
    @click.option("--name", prompt=True)
    @click.option("--email", prompt=True)
    @click.password_option()
    def create_admin(name, email, password):
        """Create an administrator locally. Public registration is disabled."""
        if not name.strip() or "@" not in email or not 12 <= len(password) <= 128:
            raise click.ClickException(
                "Name/email required; password must be 12-128 characters"
            )
        if not add_user(name.strip(), email.strip(), generate_password_hash(password)):
            raise click.ClickException("Account already exists or could not be created")
        click.echo("Administrator created")

    with app.app_context():
        init_db()
        from cleanup_snapshots import cleanup_private_data

        cleanup_private_data()
    return app
