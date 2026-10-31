# Security policy

Experimental single-process application, not certified physical access control. This
hardening branch is under review; no supported stable release or response SLA is claimed.

Use the repository Security tab's private reporting option **if enabled**. Otherwise
ask the owner for a private reporting channel without publishing vulnerability details.
Never post faces, credentials, camera URLs, models or databases. No separate verified
security contact address is established here.

Protections include administrator sessions with server-side revocation, same-origin
mutation headers/Origin checks, trusted hosts, login throttling, upload/dimension
limits, local UI assets/CSP, protected opt-in snapshots, expiry and JSON labels
replacing executable pickle deserialization.

Limitations: no liveness/anti-spoofing, MFA, at-rest encryption, granular administrator
roles, distributed locks/rate limiting, or external security audit. All administrators
access all residents/camera controls. These protections do not replace HTTPS and a
restricted network. LBPH must not automatically unlock doors.

Use one server process. Existing deployments must be upgraded and account/data access
reviewed; this PR does not change running deployments. See `documentation/DEPLOYMENT.md`.
