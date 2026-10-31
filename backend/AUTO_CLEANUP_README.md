# Retention maintenance

The normal app performs cleanup at startup and about every five minutes of API or
recognition activity. The compatibility cleanup launcher delegates to the same app;
there is no separate daily scheduler thread.

Snapshots are off by default. When enabled, they expire after 2 days; events expire
after 7 days. Set SNAPSHOT_RETENTION_DAYS and EVENT_RETENTION_DAYS to 1-365.
From backend/, run `python cleanup_snapshots.py` for offline cleanup. An OS scheduler
can invoke it using the same environment and HFG_DATA_DIR as the server.
No Task Scheduler XML is provided. Failures are visible rather than silently ignored.
See ../PRIVACY.md and ../documentation/DEPLOYMENT.md for deletion/backup limits.
