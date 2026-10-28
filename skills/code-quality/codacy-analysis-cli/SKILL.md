---
name: codacy-analysis-cli
description: "Runs Codacy Analysis CLI (`codacy-analysis`) for local static analysis: installation, init, dependency management, dry-runs, and analysis with JSON output. Use when the user asks to analyze code locally, run static analysis, scan for bugs or security issues, lint files, check code quality without pushing to Codacy, run tools like ESLint, Ruff, Semgrep, or RuboCop, analyze staged/diff/PR changes, or set up local Codacy analysis. Also covers CLI command usage patterns and external lint tool integration."
when-to-use: "Local static analysis on a repo or specific files; install/init, run tools (ESLint, Ruff, Semgrep, RuboCop, etc.) with JSON output; scan staged/diff/PR changes or a whole repo; external lint tool configuration and CLI command reference."
argument-hint: "[--init | --analyze [--staged | --diff | --pr | --tool <id> | --files <paths>] --output-format json [--fail-if-missing | --install-dependencies] [--config-file <path>]] [init --remote gh|gl|bb <org> <repo>]"
license: MIT
metadata:
  author: Codacy
  version: 1.5.0
---

# Codacy Analysis CLI

> **Glossary:** See [glossary.md](references/glossary.md) for shared definitions of Codacy concepts (issues, findings, severity, coverage, tools, patterns, etc.).

The Codacy Analysis CLI (`codacy-analysis`) runs static analysis locally on a repository. It detects languages, selects tools, and reports issues — without pushing code to Codacy. This is a different tool from the Codacy Cloud CLI (`codacy`), which queries remote Codacy data.

Always use `--output-format json` for structured output in agentic workflows.

For gating runs (pre-commit, PR review, CI), also pass `--fail-if-missing` — see [Strict mode](#strict-mode).

## Setup

```bash
# Install
npm i -g @codacy/analysis-cli

# Verify
codacy-analysis --help
```

### Authentication (optional)

Authentication is only required for `init --remote` (fetching config from a Codacy repository). Local analysis works without authentication.

```bash
# Option 1: Interactive login
codacy-analysis login

# Option 2: Token flag
codacy-analysis login --token <your-api-token>

# Option 3: Environment variable
export CODACY_API_TOKEN=<your-api-token>

# Obtain tokens: Codacy > My Account > Access Management
# Remove credentials
codacy-analysis logout
```

**Shared session:** The Analysis CLI and the Cloud CLI (`codacy`) share the same credentials at `~/.codacy/credentials`. Logging in or out with either CLI applies to both — there is no need to authenticate separately.

## Getting help

```bash
codacy-analysis --help
codacy-analysis <command> --help
# e.g. codacy-analysis analyze --help
```

## Filesystem conventions

The CLI uses two managed locations:

| Location | Scope | Contents |
|----------|-------|----------|
| `.codacy/` (in repo root) | Per-project | `codacy.config.json`, `generated/` (tool configs), `.gitignore` (auto-created) |
| `~/.codacy/` (home dir) | Machine-wide | Runtimes, tool binaries, caches, logs, credentials |

The analyzed repository is **never modified outside of `.codacy/`**. The `.codacy/.gitignore` is auto-created to exclude `generated/`, logs, and other transient files.

### Key files

- `.codacy/codacy.config.json` — Main configuration: tools, patterns, excludes, metadata. See [references/config-format.md](references/config-format.md) for the full schema
- `.codacy/generated/<ToolId>/` — Materialized tool-specific configs (gitignored)
- `~/.codacy/credentials` — Stored API token
- `~/.codacy/logs/` — Structured logs (JSON lines, rotated at 10 MB)

## Provider values

Used with `init --remote`. See the [Provider section in the glossary](references/glossary.md#provider) for the full table of CLI values (`gh`, `gl`, `bb`).

## Analysis workflow

The end-to-end local analysis workflow (init → dry-run inspect → install dependencies → run → interpret results) lives in [references/analysis-workflow.md](references/analysis-workflow.md), split out to keep this SKILL.md under ~200 lines. Follow it step by step; all commands use `--output-format json`.

## Common workflows## Common workflows

### Quick scan of a repository not in Codacy

```bash
codacy-analysis init
codacy-analysis analyze --install-dependencies --output-format json
```

### Scan only changed files (e.g., before a commit)

Gate checks, so include `--fail-if-missing`:

```bash
# Staged files only (pre-commit check)
codacy-analysis analyze --staged --fail-if-missing --output-format json

# All changes on the current branch
codacy-analysis analyze --diff --fail-if-missing --output-format json

# Changes in a pull request
codacy-analysis analyze --pr --fail-if-missing --output-format json
```

Exit `2` means the check didn't run, not that the code is clean: install the missing tools (`--install-dependencies`, a separate run) and retry. Omit `--fail-if-missing` only for exploratory scans.

### Reproduce Codacy remote analysis locally

```bash
codacy-analysis login --token <token>
codacy-analysis init --remote gh my-org my-repo
codacy-analysis analyze --install-dependencies --output-format json
```

### Check a single file for issues

```bash
codacy-analysis analyze ./src/main.py --output-format json
```

### Re-scan after configuration changes

```bash
codacy-analysis update-config
codacy-analysis analyze --output-format json
```

### Test two configurations side by side

```bash
# Baseline config (default location) plus an experimental, broader config
codacy-analysis init
codacy-analysis init --auto AllCritical,AllSecurity --config-file .codacy/experimental.json

# Run each independently and compare the results
codacy-analysis analyze --output-format json --output baseline-results.json
codacy-analysis analyze --config-file .codacy/experimental.json --output-format json --output experimental-results.json

# Promote the extra tools/patterns from the experiment into the baseline
codacy-analysis config --merge --source .codacy/experimental.json --dest .codacy/codacy.config.json
```

### Run only security-focused tools

```bash
codacy-analysis analyze --tool Bandit --tool Brakeman --tool Trivy --tool Semgrep --tool Checkov --output-format json
```

### Analyze a Ruby project

```bash
codacy-analysis analyze --tool RuboCop --tool Reek --tool Brakeman --output-format json
```

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `Tool X not found` / tool in `unavailable` | Tool binary not installed | Run with `--install-dependencies`; if that fails, install the tool manually |
| Analysis produces no results | No tools enabled or no matching files | Re-run `codacy-analysis init` or check `.codacy/codacy.config.json` has tools configured |
| Wrong tools detected | Language detection missed files | Use `--tool <id>` to force specific tools |
| Tool timeout | Analysis takes too long on large codebase | Increase `--tool-timeout <ms>` (default 600000) |
| Config outdated after adding new languages | Init was run before new files existed | Run `codacy-analysis update-config` |
| `Config already exists` on init | `.codacy/codacy.config.json` already present | Use `update-config` instead, or delete `.codacy/codacy.config.json` first |
| Remote init fails with auth error | Missing or invalid API token | Run `codacy-analysis login` or set `CODACY_API_TOKEN` |
| Permission errors on `~/.codacy/` | Directory ownership mismatch | Check permissions: `ls -la ~/.codacy/` |
| Inspect shows tool as `bundled` but it fails | Bundled library tool has dependency issue | Check `--log-level debug` output; may need `npm rebuild` |
| Different results than Codacy Cloud | Different tool versions or pattern config | Use `init --remote` to sync config; check tool versions in inspect output |
| Exit `2`, `errors[].kind == "UnavailableTools"` | Strict mode and a tool can't run | Run `--install-dependencies`, or scope with `--tool <id>` |
| Clean result but nothing scanned | No tools enabled for the changed files | Check `toolResults` is non-empty; re-run `init` |

### Reading logs

Logs are written to `~/.codacy/logs/` in JSON lines format:

```bash
# View latest log
cat ~/.codacy/logs/*.log | jq .

# Filter for errors
cat ~/.codacy/logs/*.log | jq 'select(.level == "error")'
```

Use `--log-level debug` for the most verbose output when troubleshooting tool issues.
