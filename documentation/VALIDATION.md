# Validation record

Local environment: Windows, Python 3.13.1, OpenCV 4.13.0.92, NumPy 2.5.4.

Completed before the maintainer requested stopping additional testing:

- 60 backend tests passed in 16.12 seconds; measured app statement coverage 72%.
- 5 Node browser-logic/asset tests passed. These are VM checks, not real browser E2E.
- Python compilation, Ruff checks on backend/tests, and JS syntax checks completed.
- Generated local Tailwind CSS successfully; npm audit reported zero vulnerabilities.
- Dependency consistency checks passed. The initial Python dependency audit reported
  no known vulnerabilities for the then-installed OpenCV 5 set; OpenCV was subsequently
  pinned to 4.13.0.92 after discovering version 5 lacked the required Haar data.
  A fresh final-version vulnerability audit was not run after the stop-testing request.

Backend coverage includes unauthenticated API denial, sessions/logout, CSRF/Origin and
host checks, login throttling, input limits, retention, unsafe names, actual synthetic
LBPH train/load/delete, legacy-pickle refusal, mismatched model metadata, mixed-face
Unknown precedence, missing-model refusal and upload/training integration. Real Haar
detection was exercised on a blank image, not on a consented face dataset.

Known test limitations: background worker paths have low coverage, real camera/RTSP
capture and real browser workflows are not exercised; no liveness, FAR/FRR, throughput,
Linux deployment or production migration evidence exists. Synthetic LBPH data verifies
mechanics, not recognition quality. Documentation/packaging edits after the completed
run, plus an edit-page guard requiring name changes to be saved before face updates,
were not followed by another test run, at the maintainer's request.

GitHub Actions is prepared for Windows/Linux Python 3.13 and Node 22. It is manual-only
during this review so pushing the PR does not start additional tests against the
maintainer's latest instruction. Enable push/PR triggers when testing resumes.
No additional local tests are being run after the maintainer requested stopping.
