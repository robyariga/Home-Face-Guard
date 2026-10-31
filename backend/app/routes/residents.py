"""Resident metadata and biometric lifecycle, serialized by the app lock."""

import shutil
from flask import Blueprint, jsonify, request
from .. import face_engine as engine
from ..database import (
    add_resident,
    get_all_residents,
    get_resident_by_id,
    update_resident,
    delete_resident,
    get_db_connection,
)

residents_bp = Blueprint("residents", __name__)


def validate_name(name, exclude=None):
    safe = engine.make_safe_name(name)
    for resident in get_all_residents():
        if (
            resident["id"] != exclude
            and engine.make_safe_name(resident["name"]).casefold() == safe.casefold()
        ):
            raise ValueError("Name conflicts with an existing resident's dataset")
    return name.strip()


def payload():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("JSON object required")
    role = data.get("role", "Penghuni")
    if not isinstance(role, str) or len(role) > 80:
        raise ValueError("Invalid role")
    return data, role


def delete_face_dataset(name):
    directory = engine.FACES_DIR / engine.make_safe_name(name)
    if directory.is_symlink():
        raise ValueError("Symlink datasets are not supported")
    engine.invalidate_model()
    if directory.exists():
        shutil.rmtree(directory)


def retrain():
    engine.invalidate_model()
    try:
        engine.train_lbph_model(engine.get_env_int("MAX_TRAIN_IMAGES_PER_PERSON", 200))
        return None
    except ValueError:
        return "Model unavailable until at least one registered resident has valid face samples"
    except Exception:
        return "Model unavailable; run training and inspect server diagnostics"


@residents_bp.get("/residents")
def list_residents():
    return jsonify(get_all_residents())


@residents_bp.get("/residents/<int:resident_id>")
def get_resident(resident_id):
    resident = get_resident_by_id(resident_id)
    return (
        (jsonify(resident), 200)
        if resident
        else (jsonify(message="Penghuni tidak ditemukan"), 404)
    )


@residents_bp.post("/residents")
def create_resident():
    data, role = payload()
    name = validate_name(data.get("name"))
    count = engine.count_faces(name)
    resident_id = add_resident(name, role, count)
    if resident_id is None:
        return jsonify(message="Nama sudah terdaftar"), 409
    warning = retrain()
    return jsonify(
        id=resident_id, name=name, face_count=count, training_warning=warning
    ), 201


@residents_bp.route("/residents/<int:resident_id>", methods=["PUT", "PATCH"])
def update_resident_data(resident_id):
    resident = get_resident_by_id(resident_id)
    if resident is None:
        return jsonify(message="Penghuni tidak ditemukan"), 404
    data, role = payload()
    name = validate_name(data.get("name", resident["name"]), resident_id)
    old_dir = engine.FACES_DIR / engine.make_safe_name(resident["name"])
    new_dir = engine.FACES_DIR / engine.make_safe_name(name)
    if old_dir.is_symlink() or new_dir.is_symlink():
        raise ValueError("Symlink datasets are not supported")
    if old_dir != new_dir and new_dir.exists():
        return jsonify(
            message="Target dataset already exists; resolve enrollment before renaming"
        ), 409
    engine.invalidate_model()
    renamed = old_dir != new_dir and old_dir.exists()
    if renamed:
        old_dir.rename(new_dir)
    try:
        count = engine.count_faces(name)
        if not update_resident(
            resident_id, name, data.get("role", resident["role"]), count
        ):
            raise ValueError("Could not update resident")
    except Exception:
        if renamed:
            new_dir.rename(old_dir)
        raise
    if name != resident["name"]:
        conn = get_db_connection()
        try:
            conn.execute(
                "UPDATE events SET name = ? WHERE name = ?", (name, resident["name"])
            )
            conn.commit()
        finally:
            conn.close()
    warning = retrain()
    return jsonify(
        id=resident_id, name=name, face_count=count, training_warning=warning
    )


@residents_bp.delete("/residents/<int:resident_id>")
def delete_resident_data(resident_id):
    resident = get_resident_by_id(resident_id)
    if resident is None:
        return jsonify(message="Penghuni tidak ditemukan"), 404
    # Fail visibly if files cannot be removed; never claim deletion succeeded.
    delete_face_dataset(resident["name"])
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM events WHERE name = ?", (resident["name"],))
        conn.commit()
    finally:
        conn.close()
    if not delete_resident(resident_id):
        return jsonify(message="Could not delete metadata"), 500
    return jsonify(
        message="Penghuni dan data wajah dihapus", training_warning=retrain()
    )


@residents_bp.delete("/residents/dataset/<name>")
def delete_resident_dataset_only(name):
    engine.make_safe_name(name)
    delete_face_dataset(name)
    for resident in get_all_residents():
        if resident["name"] == name:
            update_resident(resident["id"], name, resident["role"], 0)
    return jsonify(name=name, face_count=0, training_warning=retrain())


@residents_bp.get("/check_dataset/<name>")
def check_dataset(name):
    count = engine.count_faces(name)
    return jsonify(name=name, exists=count > 0, face_count=count)
