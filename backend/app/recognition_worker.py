"""Optional single-process camera worker. Camera sources are server-configured."""

import os
import threading
import time
from . import face_engine as engine
from .database import add_event


class RecognitionWorker:
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = None
        self.running = False
        self.last_error = None

    def start(self, source=None):
        if self._thread and self._thread.is_alive():
            return False
        self.last_error = None
        self._stop_event.clear()
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        if not self.running:
            return False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
        # A blocking camera read can outlive the join; do not permit duplicate starts.
        self.running = bool(self._thread and self._thread.is_alive())
        return True

    def status(self):
        return {
            "running": self.running,
            "stopping": self.running and self._stop_event.is_set(),
            "source": "server-configured",
            "last_error": self.last_error,
        }

    def _run(self):
        cap = None
        last_label, last_ts = None, 0.0
        last_cleanup = 0.0
        try:
            source = os.getenv("CAMERA_SOURCE", "0")
            source = int(source) if source.isdigit() else source
            cap = engine.cv2.VideoCapture(source)
            if not cap.isOpened():
                raise RuntimeError("Camera unavailable")
            while not self._stop_event.is_set():
                ok, frame = cap.read()
                if not ok:
                    self._stop_event.wait(0.1)
                    continue
                if not engine.STATE_LOCK.acquire(timeout=0.2):
                    continue
                try:
                    faces = engine.detect_faces_gray(frame)
                    if not faces:
                        continue
                    try:
                        model = engine.load_lbph_model(
                            engine.get_env_float("LBPH_THRESHOLD", 60.0)
                        )
                    except Exception:
                        self.last_error = "Model unavailable; training required"
                        continue
                    self.last_error = None
                    results = [
                        engine.resolve_identity(label, unknown) + (conf,)
                        for label, conf, unknown in (
                            engine.predict_face(face, model) for face, _ in faces
                        )
                    ]
                    # Unknown always takes precedence, consistently with browser mode.
                    name, status, conf = next(
                        (r for r in results if r[1] == "DITOLAK"), results[0]
                    )
                    now = time.monotonic()
                    if now - last_cleanup >= 300:
                        from cleanup_snapshots import cleanup_private_data

                        cleanup_private_data()
                        last_cleanup = now
                    if name != last_label or now - last_ts >= engine.get_env_float(
                        "MIN_LOG_INTERVAL_SECONDS", 3
                    ):
                        snapshot = (
                            engine.save_snapshot(frame, "Unknown")
                            if status == "DITOLAK"
                            else None
                        )
                        add_event(name, status, conf, snapshot)
                        last_label, last_ts = name, now
                finally:
                    engine.STATE_LOCK.release()
                self._stop_event.wait(0.05)
        except Exception:
            # Never expose camera URLs, credentials or local paths through the API.
            self.last_error = (
                "Recognition worker failed; check camera and model configuration"
            )
        finally:
            if cap is not None:
                cap.release()
            self.running = False
