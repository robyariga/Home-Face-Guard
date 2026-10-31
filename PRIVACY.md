# Privacy and biometric data

The operator must obtain informed permission before enrollment/capture, explain the
purpose/retention and offer withdrawal. Camera activation and UI confirmations do not
record consent or prove permission from every person in view. Do not use for covert
monitoring or unauthorized remote identification.

The browser sends photos/activated frames to this same-origin server. It stores
200×200 grayscale enrollment crops, LBPH histograms/JSON labels, and SQLite events
(time, name/Unknown, decision, distance). Upload originals are not deliberately retained;
input frames are decoded in memory. The server sees frames: use HTTPS beyond loopback.
No cloud face API, analytics or notification integration is configured. UI assets are
local. Remote deployment still transmits frames to that server.

- Enrollment crops remain until resident/dataset deletion; review active enrollments.
- Models/labels are biometric derivatives. Mutations invalidate old files before a
  rebuild; a failed rebuild leaves recognition unavailable.
- Unknown snapshots are off by default. Opt-in saves full frames that may include
  known people/surroundings. Default expiry is 2 days.
- Events expire after 7 days. Cleanup runs at startup and during activity about every
  five minutes. Schedule the cleanup command for offline installations.
- Full resident deletion removes samples, named events and old model before rebuild.
  Dataset-only deletion keeps metadata/history. Anonymous Unknown frames cannot reliably
  be matched to individuals; remove separately or use retention.
- Filesystem/SQLite deletion is not secure erasure. Backups, exports, browser caches and
  downloaded images need separate deletion/encryption policies.
- Logout revokes the server-side session; sessions expire after eight hours.

Defaults preserve `backend/app/residents.db` and `backend/dataset/`. `HFG_DATA_DIR`
consolidates data/key in a private directory. Never use a web root/public sync folder.
New POSIX directories use restrictive mode bits; Windows needs an account-specific ACL.
**The app does not encrypt data at rest.** Secure accounts, parent directories, old
files and backups; use encrypted disks where needed. See `documentation/DEPLOYMENT.md`.
