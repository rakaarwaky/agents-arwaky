# Step 2: Launch

Launch the `learn-traces` workflow from [`workflows/learn-traces.rhai`](../../../../workflows/learn-traces.rhai).

Pass `args` as an object (not a JSON string):

- `run_dir` — the collector run dir (holds `manifest.json`, `usage.json`, `phrases.json`, and `sessions/*.json`)
- `count` — `sessions_kept` from `manifest.json` (an integer; `0` pauses the run)
- `skill_dir` — this skill's own directory: `skills/skill-authoring/skill-traces`
  (its `references/` dir holds `step-1-collect.md` § Signal definitions and `step-3-read-report.md` § Report and actions shapes)

The workflow always produces report sections 1-4 in one run; the mode flags (`--learn`/`--evolve`/`--unlearn`) decide which of those sections this skill applies. Optional: `batch` (default 10), `fan` (default 10), `today`, `user_label`, `focus`.

The repo's `workflows/learn-traces.rhai` embeds prompts that name the skill's reference files by path. Grep the workflow for `references/` names after any reference-file rename or merge, and sync the strings — the launched workflow reads exactly the paths it was written with, and a stale name sends the map/reduce agents to a file that no longer exists. The bundled copy (`~/.grok/bundled/workflows/learn-traces.rhai`) is a separate snapshot; the repo copy is what the `learn-traces` launch consumes.

Block on `stc traces state wait --run-dir <RUN>` until `report.md` and `actions.json` both exist.
