# Step 0: Setup

Prepare the Linux environment, hardcoded output location, orchestrator state, and persona instructions before spawning any subagent.

## Host Setup

Use `run_terminal_command` for all host commands. Commands run in bash on Linux. Standard Linux utilities are allowed.

Resolve `HOST_PY` as `<skill_dir>/scripts/host.py`, where `<skill_dir>` is the directory containing this `SKILL.md`.

Use `python3`. Run:

```bash
python3 <HOST_PY> setup
```

Parse the JSON on stdout and store:

- `python` as `PYTHON`
- `run_id` as `DESIGN_ID`; validate that it is exactly 8 hexadecimal characters

If the host helper returns a different `scratch_dir`, ignore it for artifact storage. The artifact output location is hardcoded below.

## Hardcoded Output Location

All design artifacts must be stored under this hardcoded base directory:

```text
~/.grok/plans/<projectreponame>/
```

Where &lt;projectreponame&gt; is:

- the lowercased basename of `git rev-parse --show-toplevel`, normalized to `[a-z0-9-]`, when inside a git repository

Create the directory if it does not exist:

```bash
mkdir -p ~/.grok/plans/<repo-slug>
```

When passing paths to subagents or tools, use the expanded absolute path, for example:

```text
/home/<user>/.grok/plans/<repo-slug>/grok-design-doc-<DESIGN_ID>.md
```

## Shared File Paths

Keep these paths fixed for the entire run. Substitute `<repo-slug>` and `<DESIGN_ID>` with their actual values.

- `design_doc_file`: `~/.grok/plans/<repo-slug>/grok-design-doc-<DESIGN_ID>.md`
- `summary_file`: `~/.grok/plans/<repo-slug>/grok-design-summary-<DESIGN_ID>.md`
- `review_file`: `~/.grok/plans/<repo-slug>/grok-design-review-<DESIGN_ID>.md`

Never regenerate `DESIGN_ID` or these file paths between review/revise iterations.

## Orchestrator State

Initialize these state variables:

- `round_count`: `0`  
  Increment each time a review completes.

- `total_issues_by_severity`: `{}`  
  Map from severity (`bug`, `suggestion`, `nit`) to cumulative count.

- `previous_review_snapshot`: `""`  
  Store the previous `review_file` contents here for stalemate detection. This value is updated during the review-check step.

## Persona Injection

Load the writer and reviewer personas from TOML files.

User store: `~/.grok/personas/<name>.toml`

Extract the `instructions` field and preserve its full text. Store the results as:

- `writer_persona_instructions`
- `reviewer_persona_instructions`

On initial subagent launch, prepend the matching persona instructions to the subagent prompt. Do **not** pass a `persona` parameter to `spawn_subagent`.

Prefix the subagent description with `[writer]` or `[reviewer]`. On `resume_from` follow-ups, keep the same description tag, but do not re-inject the persona instructions.

## Invocation Input

Step 0 receives the argument from:

```text
/design <description>
```

Treat `<description>` as the design task: feature design, system architecture, migration plan, technical spec, or another design deliverable.

If the user provides file paths, links, constraints, or additional context, include all of that context in the writer prompt.



&nbsp;