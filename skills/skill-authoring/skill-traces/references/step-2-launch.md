# Step 2 — Launch

Before launching, materialize the deterministic run-dir files the workflow reads:

    aa skills trace-materialize --run-dir <RUN>

This writes `usage.json` (per-skill `count`, `sessions`, `in_slash_mru`, `unused_loaded`) and `phrases.json` (`exact_prompts`, `prompt_stems_12_words`, `repeated_instruction_lines`) into the run dir. The workflow does not recount these by hand; every map/reduce/verify/report agent reads them from disk.

Then launch the `learn-traces` workflow from [`workflows/learn-traces.rhai`](../../../../workflows/learn-traces.rhai).

Pass `args` as an object (not a JSON string):

- `run_dir` — the collector run dir (holds `manifest.json`, `usage.json`, `phrases.json`, and `sessions/*.json`)
- `count` — `sessions_kept` from `manifest.json` (an integer; `0` pauses the run)
- `skill_dir` — this skill's own directory: `skills/skill-authoring/skill-traces`
  (its `references/` dir holds `step-1-signals.md` and `step-3-report-format.md`)

The workflow always produces report sections 1-4 in one run; the mode flags (`--learn`/`--evolve`/`--unlearn`) decide which of those sections this skill applies. Optional: `batch` (default 10), `fan` (default 10), `today`, `user_label`, `focus`.

Block on `aa skills trace-state wait --run-dir <RUN>` until `report.md` and `actions.json` both exist.

`report.md` is for the user. `actions.json` is for the apply step. Every action in `actions.json` must appear in `report.md`; every claim in sections 1-3 of `report.md` must be backed by a verifier's Kept list.
