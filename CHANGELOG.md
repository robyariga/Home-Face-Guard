# Changelog

## Unreleased — security and maintainability review

- Serve the actual UI with the API; correct installation and deployment docs.
- Enforce administrator sessions with revocation, same-origin protection, trusted
  hosts, login throttling and loopback/non-debug launchers.
- Remove public admin registration, request-controlled camera URLs, executable pickle
  labels, remote UI assets and unused dummy FastAPI training routes.
- Validate uploads, reject ambiguous enrollment and calculate actual sample counts.
- Protect opt-in snapshots and expire snapshots/event records.
- Invalidate old models on mutations; require current resident membership, consistent
  threshold 60 and Unknown precedence in mixed frames.
- Add tests, CI, contribution guidance, audit and release preparation.

Not a published release. Licensing, camera evaluation and review remain release gates.
No accuracy or adoption claim is made.
