# Step 2 — Launch

Launch the `learn-traces` workflow from [`workflows/learn-traces.rhai`](../../../workflows/learn-traces.rhai).

Pass `args` as an object (not a JSON string):

- `run_dir` — the collector run dir (holds `manifest.json` and `sessions/*.json`)
- `count` — `sessions_kept` from `manifest.json` (an integer; `0` pauses the run)
- `skill_dir` — this skill's own directory: `skills/skill-authoring/skill-learning`
  (its `references/` dir holds `step-1-signals.md` and `step-3-report-format.md`)

Optional: `batch` (default 10), `fan` (default 10), `today`, `user_label`, `focus`.

Block on `aa skills trace-state wait --run-dir <RUN>` until `report.md` and `actions.json` both exist.
