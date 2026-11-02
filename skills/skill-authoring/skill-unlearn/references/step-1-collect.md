# Step 1 — Collect

Run `aa skills trace-collect` into a run dir. The collector writes `manifest.json` and `sessions/*.json`.

Then materialize the deterministic zero counts the workflow reads:

    aa skills trace-materialize --run-dir <RUN>

This writes `usage.json` (per-skill `count`, `unused_loaded`) and `phrases.json` into the run dir. Section 3 of the report is derived from `usage.json` — never recounted by an agent.
