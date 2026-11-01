# Step 0: Setup

Prepare the environment, shared file paths, orchestrator state, and personas before spawning any subagent.

## Host Setup

Run all host commands through `run_terminal_command` (bash on Linux; standard utilities allowed). Resolve `HOST_PY` as `<skill_dir>/scripts/host.py`, where `<skill_dir>` is the directory containing `SKILL.md`. Then run:

```bash
python3 <HOST_PY> setup
```

Parse the JSON on stdout and store:

- `python` as `PYTHON`
- `run_id` as `DESIGN_ID` (validate: exactly 8 hex characters)
- `scratch_dir` as the artifact base directory. `host.py` is the single source of truth for this location: `~/.grok/plans/<repo-slug>/`, where `<repo-slug>` is the lowercased git repository name normalized to `[a-z0-9-]`. It also creates the directory. If setup fails (e.g. not inside a git repository), stop and report.

Always use expanded absolute paths (for example `/home/<user>/.grok/plans/<repo-slug>/grok-design-doc-<DESIGN_ID>.md`), including in subagent prompts.

## Shared File Paths

Fixed for the entire run; derive each from `scratch_dir`:

- `design_doc_file`: `<scratch_dir>/grok-design-doc-<DESIGN_ID>.md`
- `summary_file`: `<scratch_dir>/grok-design-summary-<DESIGN_ID>.md`
- `review_file`: `<scratch_dir>/grok-design-review-<DESIGN_ID>.md`

Never regenerate `DESIGN_ID` or these paths during review/revise iterations.

## Orchestrator State

- `round_count`: `0`. Increment each time a review completes — after Step 2 and after every Step 5 re-review.
- `total_issues_by_severity`: `{}`. Map from severity (`bug`, `suggestion`, `nit`) to cumulative count; updated at Step 3.
- `previous_review_snapshot`: `""`. Previous `review_file` contents, used for stalemate detection; updated at Step 3.

## Persona Injection

Load the writer and reviewer personas from `~/.grok/personas/<name>.toml`, extracting the full `instructions` field into:

- `writer_persona_instructions`
- `reviewer_persona_instructions`

Injection timing follows the **Personas** rule in SKILL.md Global Rules (SSOT) — prepend on initial launch, never on resume.

## Invocation Input

The user ran `/design <description>`. Treat `<description>` as the design task: feature design, system architecture, migration plan, technical spec, or another design deliverable. Capture any file paths, links, constraints, or extra context the user provided — Step 1 must include all of it in the writer prompt.