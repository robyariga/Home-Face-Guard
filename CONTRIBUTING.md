# Contributing

Start with a reproducible issue or small PR explaining the problem, resulting behavior
and verification performed. Use synthetic examples; never attach real faces, biometric
models, databases, login secrets or camera credentials.

Read `LICENSING.md` first. Project-wide licensing and inbound contribution terms remain
unresolved. Public visibility does not imply reuse rights. Do not contribute copied
work without permission/notices. Broader terms will follow rights-holder agreement.

Follow README setup, use a dedicated environment and one server process. Keep changes
on a branch, add relevant regression coverage for behavior changes, and disclose what
you could not verify. Synthetic tests cannot establish biometric accuracy.

UI styles are generated: `npm ci`, edit HTML/JS or `styles/input.css`, then
`npm run build:css`. Commit generated CSS and dependency lockfile changes.
Runtime installations need neither npm nor a stylesheet CDN.

Follow `CODE_OF_CONDUCT.md`. Report security findings using `SECURITY.md`. Maintainers
review privacy, provenance, deletion and release gates before merging; automatic merge
or release publication is not configured.
