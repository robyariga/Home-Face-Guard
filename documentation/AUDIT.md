# Repository audit and remediation

Audited 2026-10-31 against base commit `2c4d954` (66 commits). Scope: every tracked
Python module/launcher, requirements, cleanup documents, HTML page, JS/CSS asset,
README and ignore configuration. This is a source review, not a penetration test or
legal opinion. No running deployment, production database or consented face corpus
was provided. Existing history credits and archive references were inspected.

| Finding | Result in this branch |
| --- | --- |
| Login returned user JSON without protecting APIs | Enforced sessions plus revocable server-side records across data/camera endpoints |
| Anyone could register as administrator | Public registration disabled; local CLI provisioning |
| Debug server bound all interfaces | Loopback, debug/reloader off; single-process Waitress instructions |
| Hardcoded hosted API and mismatched frontend instructions | Same-origin Flask-served `docs/` UI and corrected English/Indonesian install |
| Public face snapshots and exposed paths | Authenticated delivery, expiry/path restrictions, no-store and path redaction in log responses |
| Unbounded/default-on biometric collection | Explicit camera activation, opt-in snapshots, finite image/request/dataset limits and retention |
| Executable pickle labels | JSON labels and matching model digest; never load legacy pickle |
| Deletion/retraining could preserve old identity model | Invalidate before mutation/rebuild; require current registered identity at prediction |
| Worker used threshold 65 vs browser 60 | Both default to 60; invalid distances/thresholds reject |
| Largest known face masked a smaller unknown | Unknown takes precedence in both modes |
| Ambiguous enrollment and normalized name collisions | Require one detected face and reject conflicting resident names |
| Request-supplied camera source could access internal resources | Camera source configured only through server environment; status redacts it |
| Stored name/role HTML interpolation | Escaped rendering; no names in executable event handlers; CSP |
| Remote executable UI assets | Local generated styles/system fonts; self-only scripts/connections |
| Unused FastAPI route wrote dummy model | Removed unregistered placeholder; real Flask LBPH training retained |
| Missing contribution/release processes | Community documents, issue/PR templates, CI and source-archive preparation |
| Unestablished rights/license | Credits preserved; licensing withheld pending specific rights-holder confirmation |

Residual limits: no liveness protection, measured real-world error rates, encryption at
rest, granular administrator roles, distributed runtime support, independent security
audit or field deployment verification. Existing installations need account review,
retraining and private backup/migration management. Retained Unknown full frames can
contain several people; deletion does not erase backups or recoverable storage.

All changes are proposed for review. Running deployments and repository description/
topics are not automatically changed. No release is published and no adoption evidence
is fabricated. Full release gates are in `RELEASE.md`.
