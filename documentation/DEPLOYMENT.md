# Deployment and migration

Supported boundary: one Python server process, trusted administrators and private
local storage. Use Waitress on loopback and a same-origin HTTPS reverse proxy remotely.
Multiple workers, separate UI/API origins and public registration are unsupported.

Set `HFG_TRUSTED_HOSTS` to the public hostname (no scheme/port), `HFG_HTTPS=1` and
configure a trusted proxy to preserve Host and correctly report the HTTPS scheme.
The app does not blindly trust forwarded headers or enable ProxyFix. Browser Origin
and reconstructed server origin must match. Keep port 5000 private. Use a persistent
32+ character `HFG_SECRET_KEY` or the private persistent `session.key`.

## Existing installations

Stop every old server/worker before upgrading. Back up privately:

- `backend/app/residents.db` and any WAL/SHM files; copy only while stopped.
- `backend/dataset/faces`, `models` and `snapshots`.

Default locations are preserved. SQLite adds an `auth_sessions` table on startup.
Existing accounts remain: review/remove untrusted accounts created via old public
registration and review weak passwords. LocalStorage no longer grants API access.

Legacy `labels.pkl` is never deserialized. Use authenticated `POST /api/train` to
rebuild; old model/labels are removed first. A training error leaves recognition
unavailable. Only folders matching registered resident names are trained. Review old
name normalization collisions and orphan folders before retraining.

To consolidate with `HFG_DATA_DIR`, while stopped:

1. Create a private absolute directory accessible only to the service account.
2. Copy `residents.db` into it and copy `faces`, `models`, `snapshots` subdirectories.
3. Set `HFG_DATA_DIR` before importing the app and start a single process.
4. Verify intended accounts/data and retrain. A wrong/empty path creates a new empty
   installation; there is no automatic migration.
5. After verification, remove obsolete copies and manage backup expiry separately.

Never upload runtime data to GitHub. New POSIX directories use 0700 and key/database
files 0600 where supported; Windows chmod is not an ACL. Secure old files and parent
directories, set Windows account-specific ACLs, and use encrypted storage/backups as
needed. The app itself does not encrypt biometric data.

Cleanup runs on startup and about every five minutes of activity. Schedule
`python cleanup_snapshots.py` from `backend/` when offline. Training serializes with
prediction and may delay frames. Interrupted/partial enrollment needs operator review.
Deleting rows/files is not secure erasure; see `../PRIVACY.md` for retention limits.
