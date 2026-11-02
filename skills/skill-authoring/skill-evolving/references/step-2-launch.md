# Step 2 — Launch

Run the `learn-traces` workflow from [`workflows/learn-traces.rhai`](../../../workflows/learn-traces.rhai).

Block on `aa skills trace-state wait --run-dir <RUN>`. It waits until `report.md` and `actions.json` both exist in the run dir, then returns.

`report.md` is for the user. `actions.json` is for the apply step. Every action in `actions.json` must appear in `report.md`; every claim in sections 1–3 of `report.md` must be backed by a verifier's Kept list.
