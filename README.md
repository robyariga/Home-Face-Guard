# HomeFace Guard

A local-first face recognition prototype for resident enrollment and activity review.
Flask, SQLite, OpenCV Haar detection and LBPH recognition, with an Indonesian dashboard.
**Experimental: not a door lock or production security system. No liveness detection.**

[Instalasi Indonesia](documentation/INSTALL_ID.md) · [Privacy](PRIVACY.md) ·
[Security](SECURITY.md) · [Contributing](CONTRIBUTING.md) · [Audit](documentation/AUDIT.md)

## Install

Use **Python 3.13**, the locally verified version, and Git. Do not install another
OpenCV distribution in the same environment. Node.js is only needed to rebuild styles.

```sh
git clone https://github.com/robyariga/Home-Face-Guard.git
cd Home-Face-Guard
python -m venv .venv
```

Activate on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or Linux/macOS:

```sh
. .venv/bin/activate
```

Then, from the repository root:

```sh
python -m pip install -r backend/requirements.txt
cd backend
python -m flask --app app.main:create_app create-admin
python run.py
```

The administrator command prompts for name, email and password (12–128 characters).
Public registration is disabled. Open [the login page](http://127.0.0.1:5000/login.html).
The actual UI is in `docs/`, served by Flask; no separate frontend server is needed.

Add a resident and upload consenting face samples, or open Scan and activate its camera.
Each enrollment image must contain exactly one detected face. Scan collects 50 frames;
sample count does not establish accuracy. Training uses up to 200 samples per registered
resident. Review training warnings: metadata may be saved even when training fails.
Without a usable model, recognition refuses known identity.

## Features and limits

- Administrator login with HttpOnly sessions, server-side revocation and login throttling.
- Resident CRUD, JPEG/PNG uploads and optional browser enrollment capture.
- Haar detection and LBPH training; distance at/above the threshold is Unknown.
- Unknown precedence in frames containing both known and unknown faces.
- Authenticated logs and opt-in authenticated snapshots, disabled by default.
- Snapshot/event expiry (2/7 days), local assets and explicit camera activation.

Limits: 16 MiB/request, 8 MiB and 4 megapixels/image, 50 uploads/request,
1,000 retained images/resident. Uploads can partially succeed before an error; inspect
retained counts and delete unwanted samples. Counts are computed by the server.

## Deployment

From `backend/`, after creating an administrator:

```sh
waitress-serve --host=127.0.0.1 --port=5000 --call app.main:create_app
```

Use **one server process**. Camera ownership, locks, debounce and rate limits are
process-local. Multiple workers/replicas are unsupported. For remote use, configure a
same-origin HTTPS reverse proxy, restrict access, set `HFG_HTTPS=1`, and allow the
hostname with `HFG_TRUSTED_HOSTS`. See [deployment/migration](documentation/DEPLOYMENT.md).
The old separately hosted UI/API arrangement is no longer supported.

## Configuration

Set variables before startup; `.env` files are not loaded automatically.
See [the reference configuration](backend/.env.example).

| Variable | Default | Meaning |
| --- | --- | --- |
| `HFG_DATA_DIR` | legacy locations | Absolute private data directory; read migration guide |
| `HFG_SECRET_KEY` | persistent private `session.key` | Optional secret, at least 32 characters |
| `HFG_HTTPS` | `0` | Set `1` behind HTTPS for Secure cookies/HSTS |
| `HFG_TRUSTED_HOSTS` | `localhost,127.0.0.1,[::1]` | Hosts without scheme/port |
| `HFG_SAVE_SNAPSHOTS` | `0` | Set `1` to retain unknown full-frame photos |
| `SNAPSHOT_RETENTION_DAYS` | `2` | Snapshot expiry; 1–365 days |
| `EVENT_RETENTION_DAYS` | `7` | Event expiry; 1–365 days |
| `LBPH_THRESHOLD` | `60` | Lower is stricter; not an accuracy percentage |
| `MAX_TRAIN_IMAGES_PER_PERSON` | `200` | Training sample cap |
| `MIN_LOG_INTERVAL_SECONDS` | `3` | Repeated same-identity event interval |
| `CAMERA_SOURCE` | `0` | Server-configured camera index/RTSP URL |
| `HOST`, `PORT` | `127.0.0.1`, `5000` | Local launcher binding |

Cleanup runs at startup and during activity about every five minutes. Expired snapshots
are refused immediately. Offline cleanup: `python cleanup_snapshots.py` from `backend/`.
Backups and exported copies require separate deletion.

## API

All `/api/` data/camera endpoints require login. Mutations, including login, must send
`X-HFG-Request: 1`. Nonmatching Origin is refused and CORS is disabled. Keep the login
response cookie; the UI handles this automatically.

| Method | Route | Purpose |
| --- | --- | --- |
| POST | `/api/auth/login`, `/api/auth/logout` | Start/revoke administrator session |
| GET | `/api/auth/me` | Current identity |
| GET/POST | `/api/residents` | List/create metadata |
| GET/PUT/PATCH/DELETE | `/api/residents/<id>` | Read/update/delete resident and faces |
| DELETE | `/api/residents/dataset/<name>` | Delete samples/rebuild model; keep metadata/history |
| POST | `/api/upload/faces` | Multipart `name` and `faces` files |
| POST | `/api/train` | Rebuild registered datasets; optional `max_images_per_person` |
| GET | `/api/model/status` | Model availability/configuration |
| POST | `/api/recognition/frame` | Multipart `frame` or JSON `image` data URL |
| GET | `/api/logs`, `/api/events/<id>` | Activity records |
| POST | `/api/recognition/start`, `/api/recognition/stop` | Server camera control; start body `{}` |
| GET | `/api/recognition/status` | Worker health without camera credentials |

## Development

From the root with the environment active:

```sh
python -m pip install -r backend/requirements-dev.txt
python -m pytest -q
python -m ruff check backend tests
npm ci
npm test
npm run build:css
```

Synthetic checks are not a biometric benchmark. See [validation](documentation/VALIDATION.md).
No measured real-world error rate, adoption or security certification is claimed.

## License and release status

**No project-wide license is granted yet.** Existing credits name Wikky Fawwaz Al Maki,
Roby Ariga Siagian and Diertri Wira Satya. Archive provenance and authorization from all
relevant rights holders need confirmation. Public visibility is not a license.
See [licensing](LICENSING.md) and [third-party notices](THIRD_PARTY_NOTICES.md).
A licensed open-source/stable release remains pending those decisions and a consented
camera evaluation. This change prepares review; it does not publish a release or
establish eligibility for an external program.
