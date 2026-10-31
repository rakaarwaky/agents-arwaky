# Step 0 Setup

Everything the run needs before any subagent can spawn: host helpers, shared file paths, orchestrator state, and persona loading.

## Host Setup

Host commands must work in bash **and** PowerShell. Do not run `python3`, `umask`, `id -u`, `/proc`, or write to `/tmp` directly — the host helper resolves the per-repo plans dir. Use `run_terminal_command`.

Resolve `HOST_PY` as `<dirname of this SKILL.md>/scripts/host.py`. Find Python 3 (`python`, `py -3`, `python3`; reject `WindowsApps`). Run `<python> <HOST_PY> setup` and parse JSON stdout → `python` (PYTHON), `scratch_dir`, `run_id` (DESIGN_ID, validate 8 hex chars).

`scratch_dir` is the per-repo plans home `~/.grok/plans/<repo-slug>/` (repo slug = `git rev-parse --show-toplevel` basename, lowercased `[a-z0-9-]`; `general` outside a git work tree). The helper creates the dir. Design deliverables live here so they survive reboots and group by repo.

Inline absolute `scratch_dir` and `PYTHON` into every later command and subagent prompt.

## Shared File Paths

All paths live under `scratch_dir` and stay the same for the entire run — never regenerate between iterations.

- `design_doc_file`: `${scratch_dir}/grok-design-doc-${DESIGN_ID}.md`
- `summary_file`: `${scratch_dir}/grok-design-summary-${DESIGN_ID}.md`
- `review_file`: `${scratch_dir}/grok-design-review-${DESIGN_ID}.md`

## Orchestrator State

Initialize these state variables:

- `round_count`: `0` — incremented each time a review completes.
- `total_issues_by_severity`: `{}` — a map from severity (bug, suggestion, nit) to cumulative count.
- `previous_review_snapshot`: `""` — after each review check, store a copy of the `review_file` contents for stalemate detection.

## Persona Injection

Personas come from `personas/*.toml` (user store `~/.grok/personas/<name>.toml` first, then repo fallback `<dirname of this SKILL.md>/../../../../personas/<name>.toml`). Extract the `instructions` field (`""" ... """` body). Store as `writer_persona_instructions` and `reviewer_persona_instructions`.

Prepend the appropriate persona to the subagent prompt on initial launch. Do NOT pass a `persona` parameter to `spawn_subagent`. Prefix `description` with `[writer]` or `[reviewer]`. Keep the tag on `resume_from` follow-ups; do not re-inject persona on resume.

## Invocation

The user runs:
```
/design <description>
```

The `<description>` is the design task — feature design, system architecture, migration plan, technical spec, or any design document. If the user provides file paths, links, or additional context, include all of that context in the writer prompt.
