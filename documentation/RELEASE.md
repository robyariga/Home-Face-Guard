# Release preparation

Status: Unreleased review branch, not a stable version.

Before a stable release:

- Resolve `LICENSING.md` with rights holders; add the agreed license/notices.
- Review this PR/audit and ensure the tree/history contains no private data/secrets.
- Review CI for the exact candidate commit. Local checks alone are not hosted CI.
- Conduct an informed-consent camera evaluation: strangers, lighting, glasses/pose,
  multiple faces and photo replay. Record false acceptance/rejection rates and limits.
- Verify clean install, account migration, deletion/retraining, HTTPS and retention
  in the intended deployment.
- Agree on version/date and document breaking changes: sessions, same-origin UI,
  CLI accounts and retraining legacy pickle models.
- Prepare a reviewed tag and draft/prerelease; publish only with maintainer approval.

The optional manual `prepare-source` workflow archives tracked source. It does not
create a tag, release or deployment. Never include runtime biometric data or secrets.

Repository About description applied during this maintenance:
`Local-first face recognition prototype with resident enrollment, Unknown detection and a Flask dashboard.`

Topics applied: `python`, `flask`, `opencv`, `face-recognition`, `privacy`, `prototype`.
These describe implementation, not certification. No user, star, download or adoption
statistics are invented. State licensing/release readiness accurately in applications
to any external program; acceptance is not established by this work.
