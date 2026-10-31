"""Delete expired private data; safe to run while the single server is active."""

import time
from app import face_engine
from app.database import get_db_connection


def cleanup_snapshots(days=2):
    if not isinstance(days, int) or not 1 <= days <= 365:
        raise ValueError("Snapshot retention must be 1-365 days")
    cutoff, deleted = time.time() - days * 86400, 0
    for path in face_engine.SNAPSHOTS_DIR.glob("*.jpg"):
        if path.is_symlink() or not path.is_file():
            continue
        if path.stat().st_mtime < cutoff:
            path.unlink()
            deleted += 1
    return deleted


def cleanup_private_data():
    with face_engine.STATE_LOCK:
        deleted = cleanup_snapshots(
            face_engine.get_env_int("SNAPSHOT_RETENTION_DAYS", 2)
        )
        days = face_engine.get_env_int("EVENT_RETENTION_DAYS", 7)
        if not 1 <= days <= 365:
            raise ValueError("Event retention must be 1-365 days")
        conn = get_db_connection()
        try:
            conn.execute(
                "DELETE FROM events WHERE timestamp < datetime('now', ?)",
                (f"-{days} days",),
            )
            conn.execute(
                "DELETE FROM auth_sessions WHERE expires_at <= ?", (time.time(),)
            )
            conn.commit()
        finally:
            conn.close()
        return deleted


if __name__ == "__main__":
    from app.database import init_db

    face_engine.ensure_dirs()
    init_db()
    print(
        f"Removed {cleanup_private_data()} expired snapshots; expired events also purged"
    )
