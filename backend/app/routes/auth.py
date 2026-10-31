"""Administrator sessions. Accounts are provisioned with the local CLI."""

from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from ..database import (
    get_user_by_email,
    get_user_by_id,
    new_auth_session,
    revoke_auth_session,
)
from ..security import limiter

auth_bp = Blueprint("auth", __name__)
_DUMMY_HASH = generate_password_hash("not-an-account-password")


def public_user(user):
    return {key: user[key] for key in ("id", "name", "email", "role")}


@auth_bp.post("/auth/register")
def register():
    return jsonify(
        message="Registrasi publik dinonaktifkan. Hubungi pengelola untuk membuat akun."
    ), 403


@auth_bp.post("/auth/login")
@limiter.limit("5 per minute")
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(message="JSON object required"), 400
    email, password = data.get("email"), data.get("password")
    if (
        not isinstance(email, str)
        or not isinstance(password, str)
        or len(password) > 128
    ):
        return jsonify(message="Email dan password tidak valid"), 400
    user = get_user_by_email(email)
    valid = check_password_hash(
        user["password_hash"] if user else _DUMMY_HASH, password
    )
    if not user or not valid:
        return jsonify(message="Email atau password salah"), 401
    revoke_auth_session(session.get("auth_token"))
    session.clear()
    session["auth_token"] = new_auth_session(user["id"])
    session["user_id"] = user["id"]
    session.permanent = True
    return jsonify(message="Login berhasil", user=public_user(user))


@auth_bp.get("/auth/me")
def me():
    return jsonify(user=public_user(get_user_by_id(session["user_id"])))


@auth_bp.post("/auth/logout")
def logout():
    revoke_auth_session(session.get("auth_token"))
    session.clear()
    return jsonify(message="Logged out")
