import io
import numpy as np
import pytest
from PIL import Image
from werkzeug.security import generate_password_hash
from app import face_engine as engine, database
from app.main import create_app
from app.routes import recognition


@pytest.fixture
def app(tmp_path, monkeypatch):
    for key, value in {
        "DATASET_DIR": tmp_path,
        "FACES_DIR": tmp_path / "faces",
        "MODELS_DIR": tmp_path / "models",
        "SNAPSHOTS_DIR": tmp_path / "snapshots",
        "MODEL_PATH": tmp_path / "models/lbph_model.yml",
        "LABELS_PATH": tmp_path / "models/labels.json",
    }.items():
        monkeypatch.setattr(engine, key, value)
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "residents.db"))
    monkeypatch.delenv("HFG_SAVE_SNAPSHOTS", raising=False)
    monkeypatch.setenv("HFG_SECRET_KEY", "a-test-only-secret-which-is-long-enough")
    monkeypatch.setattr(recognition, "_last_label", None)
    monkeypatch.setattr(recognition, "_last_log_ts", 0.0)
    application = create_app({"TESTING": True, "RATELIMIT_ENABLED": True})
    database.add_user(
        "Test administrator",
        "admin@example.test",
        generate_password_hash("test password 1234"),
    )
    return application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.test", "password": "test password 1234"},
        headers={"X-HFG-Request": "1"},
    )
    assert response.status_code == 200
    return client


@pytest.fixture
def image_bytes():
    out = io.BytesIO()
    Image.fromarray(np.zeros((200, 200, 3), dtype=np.uint8)).save(out, format="JPEG")
    return out.getvalue()


@pytest.fixture
def enrolled():
    def enroll(name="Alice"):
        resident_id = database.add_resident(name, "Penghuni", 1)
        folder = engine.FACES_DIR / engine.make_safe_name(name)
        folder.mkdir(exist_ok=True)
        rng = np.random.default_rng(17)
        face = rng.integers(0, 256, (200, 200), dtype=np.uint8)
        assert engine.cv2.imwrite(str(folder / "sample.jpeg"), face)
        return resident_id, face

    return enroll
