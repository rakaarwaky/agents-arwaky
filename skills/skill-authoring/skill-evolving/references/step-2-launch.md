# Step 2 — Launch

Run the `learn-traces` workflow from [`workflows/learn-traces.rhai`](../../../workflows/learn-traces.rhai).

Pass `args` as an object (not a JSON string):

- `run_dir` — the collector run dir (holds `manifest.json` and `sessions/*.json`)
- `count` — `sessions_kept` from `manifest.json` (an integer; `0` pauses the run)
- `skill_dir` — this skill's own directory: `skills/skill-authoring/skill-evolving`
  (its `references/` dir holds `signals.md` and `report-format.md`)

Optional: `batch` (default 10), `fan` (default 10), `today`, `user_label`, `focus`.

Block on `aa skills trace-state wait --run-dir <RUN>`. It waits until `report.md` and `actions.json` both exist in the run dir, then returns.

`report.md` is for the user. `actions.json` is for the apply step. Every action in `actions.json` must appear in `report.md`; every claim in sections 1–3 of `report.md` must be backed by a verifier's Kept list.
