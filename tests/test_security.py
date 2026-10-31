import io
import os
import time
import pytest
from app import face_engine as engine, database
from app.security import limiter
from cleanup_snapshots import cleanup_private_data

HEADERS = {"X-HFG-Request": "1"}


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/api/residents"),
        ("POST", "/api/residents"),
        ("DELETE", "/api/residents/1"),
        ("PATCH", "/api/residents/1"),
        ("GET", "/api/logs"),
        ("GET", "/api/events/1"),
        ("GET", "/api/snapshots/test.jpg"),
        ("POST", "/api/train"),
        ("GET", "/api/model/status"),
        ("POST", "/api/upload/faces"),
        ("POST", "/api/recognition/frame"),
        ("POST", "/api/recognition/start"),
        ("POST", "/api/recognition/stop"),
        ("GET", "/api/recognition/status"),
        ("GET", "/api/check_dataset/Alice"),
        ("DELETE", "/api/residents/dataset/Alice"),
        ("GET", "/api/auth/me"),
    ],
)
def test_anonymous_denied(client, method, path):
    assert client.open(path, method=method, headers=HEADERS).status_code == 401


def test_sessions_and_logout(admin):
    assert admin.get("/api/auth/me").json["user"]["email"] == "admin@example.test"
    assert admin.post("/api/auth/logout", headers=HEADERS).status_code == 200
    assert admin.get("/api/residents").status_code == 401


def test_cookie_and_security_headers(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@example.test", "password": "test password 1234"},
        headers=HEADERS,
    )
    cookie = res.headers["Set-Cookie"]
    assert "HttpOnly" in cookie and "SameSite=Strict" in cookie
    assert res.headers["Cache-Control"] == "no-store"
    assert "script-src 'self'" in res.headers["Content-Security-Policy"]
    assert res.headers["X-Content-Type-Options"] == "nosniff"


def test_csrf_cors_and_host(admin):
    assert admin.post("/api/residents", json={"name": "Alice"}).status_code == 403
    res = admin.post(
        "/api/residents",
        json={"name": "Alice"},
        headers={**HEADERS, "Origin": "https://evil.test"},
    )
    assert res.status_code == 403 and "Access-Control-Allow-Origin" not in res.headers
    assert admin.get("/api/residents", headers={"Host": "evil.test"}).status_code == 400
    assert admin.post("/api/auth/register", json={}, headers=HEADERS).status_code == 403


def test_login_rate_limit(app, client):
    app.config["RATELIMIT_ENABLED"] = True
    limiter.enabled = True
    with app.app_context():
        limiter.reset()
    try:
        results = [
            client.post(
                "/api/auth/login",
                json={"email": "no@example.test", "password": "wrong"},
                headers=HEADERS,
            ).status_code
            for _ in range(6)
        ]
        assert results == [401] * 5 + [429]
    finally:
        with app.app_context():
            limiter.reset()


@pytest.mark.parametrize(
    "data",
    [[], None, {"email": 3, "password": []}, {"email": "a", "password": "a" * 129}],
)
def test_bad_login_input(client, data):
    assert client.post("/api/auth/login", json=data, headers=HEADERS).status_code == 400


@pytest.mark.parametrize("name", ["", "...", "未知", "Unknown", None, 3, "A" * 121])
def test_unsafe_resident_names(admin, name):
    assert (
        admin.post("/api/residents", json={"name": name}, headers=HEADERS).status_code
        == 400
    )


def test_name_collision_and_server_face_count(admin):
    first = admin.post(
        "/api/residents",
        json={"name": "Alice Smith", "face_count": 9000},
        headers=HEADERS,
    )
    assert first.status_code == 201 and first.json["face_count"] == 0
    assert (
        admin.post(
            "/api/residents", json={"name": "Alice_Smith"}, headers=HEADERS
        ).status_code
        == 400
    )
    assert admin.post("/api/residents", json=[], headers=HEADERS).status_code == 400


def test_payload_and_decode_limits(admin, image_bytes):
    assert (
        admin.post(
            "/api/recognition/frame",
            data=b"x" * (16 * 1024 * 1024 + 1),
            headers=HEADERS,
        ).status_code
        == 413
    )
    assert (
        admin.post(
            "/api/recognition/frame",
            json={"image": "data:image/jpeg;base64,%%%"},
            headers=HEADERS,
        ).status_code
        == 400
    )
    assert (
        admin.post(
            "/api/upload/faces",
            data={"name": "Alice", "faces": (io.BytesIO(b"not-an-image"), "bad.jpg")},
            headers=HEADERS,
        ).status_code
        == 400
    )
    assert (
        admin.post(
            "/api/recognition/start",
            json={"source": "http://127.0.0.1/private"},
            headers=HEADERS,
        ).status_code
        == 400
    )


def test_snapshot_opt_in_and_retention(admin, monkeypatch, image_bytes):
    frame = engine.decode_image(image_bytes)
    assert engine.save_snapshot(frame, "Unknown") is None
    monkeypatch.setenv("HFG_SAVE_SNAPSHOTS", "1")
    path = engine.save_snapshot(frame, "Unknown")
    name = os.path.basename(path)
    database.add_event("Unknown", "DITOLAK", 99, path)
    res = admin.get("/api/logs")
    assert "snapshot_path" not in res.json[0]
    assert admin.get("/api/snapshots/" + name).status_code == 200
    old = time.time() - 3 * 86400
    os.utime(path, (old, old))
    assert admin.get("/api/snapshots/" + name).status_code == 404
    assert cleanup_private_data() == 1
    assert not os.path.exists(path)
    conn = database.get_db_connection()
    conn.execute(
        "INSERT INTO events(name,status,timestamp) VALUES ('Old','DITOLAK',datetime('now','-8 days'))"
    )
    conn.commit()
    conn.close()
    cleanup_private_data()
    assert all(e["name"] != "Old" for e in database.get_all_events())


def test_snapshot_traversal_denied(admin):
    assert admin.get("/api/snapshots/../session.key").status_code == 404


def test_deleted_account_revokes_session(admin):
    conn = database.get_db_connection()
    conn.execute("DELETE FROM users")
    conn.commit()
    conn.close()
    assert admin.get("/api/residents").status_code == 401


def test_cli_account_creation(app):
    result = app.test_cli_runner().invoke(
        args=[
            "create-admin",
            "--name",
            "Second",
            "--email",
            "second@example.test",
            "--password",
            "a strong test password",
        ]
    )
    assert result.exit_code == 0
    assert database.get_user_by_email("second@example.test")


def test_same_origin_pages_and_private_files(client):
    for page in [
        "/",
        "/index.html",
        "/login",
        "/akun",
        "/edit",
        "/scan",
        "/log",
        "/log_detail",
        "/register",
    ]:
        assert client.get(page).status_code == 200
    assert client.get("/assets/js/app.js").status_code == 200
    for path in [
        "/dataset/faces/test.jpg",
        "/backend/app/residents.db",
        "/README.md",
        "/assets/../../backend/app/main.py",
    ]:
        assert client.get(path).status_code == 404
