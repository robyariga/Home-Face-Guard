import base64
import io
import json
from types import SimpleNamespace
from unittest.mock import Mock
import numpy as np
import pytest
from PIL import Image
from app import face_engine as engine, database
from app.routes import recognition

HEADERS = {"X-HFG-Request": "1"}


@pytest.mark.parametrize(
    "pred_id,distance,threshold,unknown",
    [
        (0, 59.9, 60, False),
        (0, 60, 60, True),
        (0, 60.1, 60, True),
        (-1, 1, 60, True),
        (99, 1, 60, True),
        (0, float("nan"), 60, True),
        (0, float("inf"), 60, True),
        (0, -1, 60, True),
        (0, 1, float("nan"), True),
        (0, 1, -1, True),
    ],
)
def test_unknown_boundary_and_invalid_scores(pred_id, distance, threshold, unknown):
    model = engine.LoadedLBPHModel(
        SimpleNamespace(predict=lambda face: (pred_id, distance)),
        {0: "Alice"},
        threshold,
    )
    label, score, is_unknown = engine.predict_face(
        np.zeros((200, 200), dtype=np.uint8), model
    )
    assert is_unknown == unknown
    assert label == ("Unknown" if unknown else "Alice")
    assert np.isfinite(score)


def test_actual_lbph_train_load_and_delete(admin, enrolled):
    resident_id, face = enrolled()
    summary = engine.train_lbph_model()
    assert summary["num_samples"] == 1
    model = engine.load_lbph_model()
    label, distance, unknown = engine.predict_face(face, model)
    assert label == "Alice" and distance < 60 and not unknown
    database.add_event("Alice", "MASUK", 0)
    response = admin.delete(f"/api/residents/{resident_id}", headers=HEADERS)
    assert response.status_code == 200
    assert not (engine.FACES_DIR / "Alice").exists()
    assert not engine.MODEL_PATH.exists() and not engine.LABELS_PATH.exists()
    assert engine.resolve_identity("Alice", False) == ("Unknown", "DITOLAK")
    assert database.get_all_events() == []
    with pytest.raises(ValueError):
        engine.train_lbph_model()


def test_legacy_pickle_never_loaded(app, enrolled):
    enrolled()
    (engine.MODELS_DIR / "labels.pkl").write_bytes(b"not a safe pickle")
    engine.MODEL_PATH.write_text("legacy model")
    with pytest.raises(FileNotFoundError):
        engine.load_lbph_model()
    engine.train_lbph_model()
    assert not (engine.MODELS_DIR / "labels.pkl").exists()
    assert engine.LABELS_PATH.suffix == ".json"


def test_mismatched_json_model_rejected(app, enrolled):
    enrolled()
    engine.train_lbph_model()
    metadata = json.loads(engine.LABELS_PATH.read_text())
    metadata["model_sha256"] = "invalid"
    engine.LABELS_PATH.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="do not match"):
        engine.load_lbph_model()


def test_unknown_overrides_larger_known_face(admin, enrolled, monkeypatch, image_bytes):
    enrolled()
    face = np.zeros((200, 200), dtype=np.uint8)
    monkeypatch.setattr(
        engine,
        "detect_faces_gray",
        lambda frame: [(face, (0, 0, 200, 200)), (face, (300, 0, 70, 70))],
    )
    monkeypatch.setattr(recognition, "_get_or_load_model", lambda: (object(), 60))
    monkeypatch.setattr(
        engine,
        "predict_face",
        Mock(side_effect=[("Alice", 10, False), ("Unknown", 90, True)]),
    )
    result = admin.post(
        "/api/recognition/frame",
        json={
            "image": "data:image/jpeg;base64," + base64.b64encode(image_bytes).decode()
        },
        headers=HEADERS,
    )
    assert result.status_code == 200
    assert result.json["name"] == "Unknown" and result.json["status"] == "DITOLAK"
    assert [f["known"] for f in result.json["faces"]] == [True, False]
    assert database.get_all_events()[0]["name"] == "Unknown"


def test_missing_model_rejects_and_no_face_is_not_unknown(
    admin, monkeypatch, image_bytes
):
    data = {"image": "data:image/jpeg;base64," + base64.b64encode(image_bytes).decode()}
    monkeypatch.setattr(engine, "detect_faces_gray", lambda frame: [])
    assert (
        admin.post("/api/recognition/frame", json=data, headers=HEADERS).json[
            "detected"
        ]
        is False
    )
    monkeypatch.setattr(
        engine,
        "detect_faces_gray",
        lambda frame: [(np.zeros((200, 200), dtype=np.uint8), (0, 0, 200, 200))],
    )
    result = admin.post("/api/recognition/frame", json=data, headers=HEADERS).json
    assert (
        result["name"] == "Unknown"
        and result["model_ready"] is False
        and result["status"] == "DITOLAK"
    )


def test_dataset_only_delete_and_model_failure(admin, enrolled, monkeypatch):
    resident_id, _ = enrolled()
    engine.train_lbph_model()
    monkeypatch.setattr(
        engine, "train_lbph_model", Mock(side_effect=RuntimeError("failure"))
    )
    response = admin.delete("/api/residents/dataset/Alice", headers=HEADERS)
    assert response.status_code == 200 and response.json["training_warning"]
    assert database.get_resident_by_id(resident_id)["face_count"] == 0
    assert not engine.MODEL_PATH.exists()


def test_rename_collision_does_not_move_data(admin, enrolled):
    resident_id, _ = enrolled("Alice")
    enrolled("Bob")
    response = admin.patch(
        f"/api/residents/{resident_id}", json={"name": "Bob"}, headers=HEADERS
    )
    assert response.status_code == 400
    assert (engine.FACES_DIR / "Alice/sample.jpeg").exists()
    assert database.get_resident_by_id(resident_id)["name"] == "Alice"


def test_enrollment_rejects_multiple_faces(admin, monkeypatch, image_bytes):
    face = np.zeros((200, 200), dtype=np.uint8)
    monkeypatch.setattr(
        engine,
        "detect_faces_gray",
        lambda frame: [(face, (0, 0, 60, 60)), (face, (100, 0, 60, 60))],
    )
    res = admin.post(
        "/api/upload/faces",
        data={"name": "Alice", "faces": (io.BytesIO(image_bytes), "test.jpg")},
        headers=HEADERS,
    )
    assert res.status_code == 422 and engine.count_faces("Alice") == 0


def test_image_dimensions_before_decode():
    out = io.BytesIO()
    Image.new("RGB", (2001, 2000)).save(out, format="PNG")
    with pytest.raises(ValueError, match="megapixels"):
        engine.decode_image(out.getvalue())


def test_actual_detector_blank_image(app, image_bytes):
    assert engine.detect_faces_gray(engine.decode_image(image_bytes)) == []


def test_registered_upload_training_round_trip(admin, monkeypatch, image_bytes):
    res = admin.post("/api/residents", json={"name": "Alice"}, headers=HEADERS)
    assert res.status_code == 201
    face = np.random.default_rng(44).integers(0, 256, (200, 200), dtype=np.uint8)
    monkeypatch.setattr(
        engine, "detect_faces_gray", lambda frame: [(face, (0, 0, 200, 200))]
    )
    res = admin.post(
        "/api/upload/faces",
        data={"name": "Alice", "faces": (io.BytesIO(image_bytes), "test.jpg")},
        headers=HEADERS,
    )
    assert res.status_code == 201 and res.json["training_error"] is None
    assert database.get_all_residents()[0]["face_count"] == 1
    assert engine.predict_face(face, engine.load_lbph_model())[0] == "Alice"
