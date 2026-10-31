# Trace pipeline (shared)

Shared infrastructure for the three trace-learning skills in this pack —
`skill-learning` (create skills from repeated phrases and gaps),
`skill-evolving` (edit skills that no longer match reality), and
`skill-unlearn` (retire unused surfaces). One pipeline produces all three
signals — phrases, usage counts, stale lines — in a single pass, so the
pipeline is shared rather than copied.

Files:

- `scripts/collect_sessions.py` — deterministic collector: walks
  `$GROK_HOME/sessions/`, writes a run directory with `manifest.json`,
  `sessions/*.json`, `surfaces.json`, `usage.json`, `phrases.json`,
  `decisions.jsonl` copy. Flags: `--estimate`, `--days`, `--since-last`,
  `--limit`, `--include-headless`, `--cwd`, `--drop-pattern`, `--batch`.
  Retires stale user workflow copies and prunes runs older than 30 days.
- `scripts/state.py` — run state machine and helpers: `get` / `set` /
  `clear` / `trash` / `restrict` / `decide` / `wait`. `trash` moves
  deleted skill directories, workflow files, and hook files into
  `$GROK_HOME/learn/trash/<run name>/` (never the OS temp dir);
  `restrict` makes a carved-out config file owner-only; `decide` appends
  to `$GROK_HOME/learn/decisions.jsonl`; `wait` blocks until
  `report.md` and `actions.json` exist (exit 0), 2 on timeout, 3 on
  report stall, 4 on phase stall.
- `learn-traces.rhai` — the map-reduce workflow: Map (one agent per batch
  of sessions), Reduce (fan-in until one synthesis), Verify (three
  skeptics: phrases, stale, deletes), Report (`report.md` +
  `actions.json`). Registers as workflow `learn-traces`.
- `references/signals.md` — what the mappers extract, ordered by blast
  radius: §1 instructions typed by hand, §2 friction, §3 stale skill
  lines, §4 unused surfaces (deterministic counts), §5 gaps.
- `references/report-format.md` — the shape of `report.md` (sections 1–4,
  Unverified claims, Dropped claims, Coverage) and `actions.json`
  (field list and emission rules).

## Interpreter probing

The two Python helpers do all filesystem work; host commands must work
in bash **and** PowerShell. Once per session, probe for an interpreter by
running `scripts/state.py get` with `python`, then `py -3`, then
`python3`; the first that prints JSON (exit 0, or 3 when a run is
pending) is the one to use. Its `python` field is the interpreter's
absolute path and its `grok_home` field is the resolved home; use those
two values as `<PYTHON>` and `<GROK_HOME>` in every later command and in
the workflow `args`, always double-quoted. If none of the three runs,
tell the user to install Python 3 and stop.

## Launching the workflow

Check the available workflows list. If `learn-traces` is listed, launch
with `source = {type: "name", name: "learn-traces"}`. A user-level copy of
the workflow (any `.rhai` under `$GROK_HOME/workflows` whose meta names
`learn-traces`) shadows the bundled one on older clients; the collector
already retired any stale copy to `$GROK_HOME/learn/trash/` and reports
it as `stale_workflow_copy` in its last stdout line — if that field is
non-null, tell the user in one line what was retired (`moved`) and, for a
`project_copies` entry, that a copy in their repo's `.grok/workflows`
should be deleted by hand (the collector does not touch repo files).
Never launch through such a copy by `script_path` while the named
workflow is available.

If `learn-traces` is not listed (older clients do not install bundled
workflows), read `learn-traces.rhai` with the file tools, write it to
`$GROK_HOME/workflows/learn-traces.rhai` (the `workflow` tool trusts only
that directory), and launch with
`source = {type: "script_path", script_path: "<GROK_HOME>/workflows/learn-traces.rhai"}`;
refresh that copy from this folder on every launch, not reuse it. If
`learn-traces.rhai` is missing here, or `scripts/collect_sessions.py` is
missing, stop and tell the user the install did not receive the full
skill and to update; do not reconstruct the workflow from memory, the
web, or the binary.

The workflow's `args`:
`{run_dir: <RUN>, count: manifest.sessions_kept, skill_dir: <this folder>, grok_home: <GROK_HOME>, python: <PYTHON>, batch: 10, fan: 10, today: "<YYYY-MM-DD>", user_label: "<name or 'the user'>"}`.
The script computes the agents it needs, logs the number, and pauses if
`agent_budget` is short; per-trace runs over ~110 sessions need a budget
above the default 128.

## Failure handling

**Launch, then block.** Immediately after the `workflow` call, run
`state.py wait --run-dir <RUN> --timeout-min <estimate high + 30>` as a
background command and block on it. If the `workflow` call itself fails or
pauses before any phase ran (`args reached the workflow as string`), the
args were sent as a JSON string: kill `wait`, relaunch with `args` as a
JSON object, and restart `wait`. `wait` exit codes: 0 done, 2 timeout
(present partial `map*.md` / `reduce` / `verify` output, mark unverified),
3 report stall (present the synthesis, offer one `resume` of the report
step only — a run the host reports complete cannot be resumed), 4 phase
stall (check the host run list; if running, stop + `resume` once). If the
host reports an "infra" pause, end the turn with: "Your usage balance ran
out N minutes into the run; nothing more was spent and the N finished
steps are saved. When your balance is back, reply **resume the learn run**
here and I will continue from where it stopped — no re-run needed. (Run
id <run id>.)" On that reply, `resume` via the `workflow` tool. If the
overview starts with `report_stalled:`, a hook refused the report worker's
writes — name the hook and do not retry until it is adjusted. Never write
`report.md` yourself from the synthesis: a report the verifiers did not
gate must not feed the apply step.

## Rules

- Nothing is retired, edited, or trashed before `wait` has returned
  `report_ready` and the report is on screen. `state.py trash` before a
  report is a bug, whoever asked.
- Zero hits is evidence, not proof, and only in a wide window
  (`manifest.json` → `disuse_evidence.sufficient`).
- Never print secrets: tokens, headers, env values, API keys, auth files.
  Inventory is names and paths only.
- If the user disputes a count, re-run the collector; do not guess.

### Consent rules (identical in every mode)

- An action is applied only when the user picked its id, or in `auto`
  mode when it is reversible and not `requires_confirmation`.
- A free-text answer ("Other", "just go") is not consent; re-ask with
  the literal reading as options.
- Unpicked options are recorded `deferred`, not `rejected`; only an
  explicit refusal is `rejected`.
- One group's answer never authorizes another skill's group.

### By mode

- **step** — one question over the group's action ids (`multi_select`,
  quoted evidence per option, at most eight options — split larger
  groups; label the per-skill action type as such), apply the picks,
  record `deferred` for the unpicked.
- **auto** — apply every action with `requires_confirmation: false`,
  then one question for the rest.
- **report** — stop after presenting; record nothing.

### State machine

`collected → running → report_ready → curating → done`. Record every
decision with `state.py decide` (per-skill `--action`/`--kind` enums).
Set `state.py set --status curating` when the group opens; `done` only
when every consuming skill has closed its group (a shared run is closed
by the last curator).

### Unattended runs

Use report mode (the curation-time choice; `--mode` is not a `collect_sessions.py` flag) with `--since-last`, skip the setup question, still print the price and coverage, block on `state.py wait`.
