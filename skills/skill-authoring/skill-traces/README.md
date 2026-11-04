# README — skill-traces

## Project Overview

skill-traces is the trace-learning skill that curates one trace-learning run across three dispositions: learn new skills from repeated instructions and open gaps (`--learn`), fix stale lines in loaded skills (`--evolve`), and retire skills the window shows as never used (`--unlearn`). The trace pipeline reads session traces from `$GROK_HOME/sessions` and the `skills/` pack, then writes run-dir artifacts (`manifest.json`, `sessions/*.json`, `usage.json`, `phrases.json`) plus lifecycle state under `$GROK_HOME/learn`.

## Prerequisites

- The skill-traces pack at `skills/skill-authoring/skill-traces/`
- `uv` (Python package manager)
- `stc` launcher on `PATH` (`stc help` lists every command)

## Quick Start

| Step | Action | Command |
|------|--------|---------|
| 1 | Run trace learning (all three dispositions) | `stc traces --learn --evolve --unlearn` |
| 2 | Learn only | `stc traces --learn` |
| 3 | Evolve only | `stc traces --evolve` |
| 4 | Wait for report readiness | `stc traces state wait` |
| 5 | Exit code contract | 0 ready / 1 phase-stall / 3 report-stall / 2 deadline |

Every command is a plain `stc <noun> <action>` subcommand; run `stc help` for the full table.

## Reference

| Artifact | Purpose | Link |
|----------|---------|------|
| AGENTS.md | Agent operational guide (runtime, structure, commands) | [AGENTS.md](AGENTS.md) |
| PRD.md | What the product does and why | [PRD.md](PRD.md) |
| ROADMAP.md | What ships next, in order | [ROADMAP.md](ROADMAP.md) |
| ARCHITECTURE.md | Layer contract and linter rule catalog | [ARCHITECTURE.md](ARCHITECTURE.md) |
