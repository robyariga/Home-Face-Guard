"""Session authentication and same-origin request protection."""

import os
import secrets
from pathlib import Path
from flask import current_app, jsonify, request, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=[])


def load_secret(data_dir: Path) -> str:
    configured = os.getenv("HFG_SECRET_KEY")
    if configured:
        if len(configured) < 32:
            raise ValueError("HFG_SECRET_KEY must contain at least 32 characters")
        return configured
    key_path = data_dir / "session.key"
    try:
        with key_path.open("x", encoding="utf-8") as handle:
            os.chmod(key_path, 0o600)
            handle.write(secrets.token_hex(32))
    except FileExistsError:
        pass
    secret = key_path.read_text(encoding="utf-8").strip()
    if len(secret) < 32:
        raise ValueError(
            "Invalid session.key; restore or rotate it with the server stopped"
        )
    return secret


def protect_api():
    if not request.path.startswith("/api/"):
        return None
    if request.routing_exception is not None:
        raise request.routing_exception
    request.host  # Force trusted-host validation before authentication.
    origin = request.headers.get("Origin")
    if origin and origin != request.host_url.rstrip("/"):
        return jsonify(message="Cross-origin API requests are disabled"), 403
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        if request.headers.get("X-HFG-Request") != "1":
            return jsonify(message="X-HFG-Request: 1 is required"), 403
    if request.path not in {"/api/auth/login", "/api/auth/register"}:
        if not session.get("user_id"):
            return jsonify(message="Login required"), 401
        from .database import get_user_by_id, valid_auth_session

        if not get_user_by_id(session["user_id"]) or not valid_auth_session(
            session["user_id"], session.get("auth_token")
        ):
            session.clear()
            return jsonify(message="Login required"), 401
    return None


def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self'; "
        "frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'"
    )
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(self), microphone=()"
    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    if current_app.config["SESSION_COOKIE_SECURE"]:
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
