# README — skill-design

## Project Overview

skill-design is the skill-authoring skill that keeps the skill tree clean, correct, and consolidated. It reads agent `SKILL.md` skill directories and runs one of three modes per invocation: `--create` builds a publishable `SKILL.md` plus its `references/` from a described job, `--improve` audits an existing skill against the shared lint standard and applies the repair edit recipe, and `--prune` collapses duplicate or same-purpose skills into one folder and archives the dropped duplicates. Every fact in a skill lives once, in a single authoritative home; every flag and mode term stays in lockstep across `SKILL.md` and its reference files.

## Prerequisites

- The skill-design pack at `skills/skill-authoring/skill-design/`
- `uv` (Python package manager)
- `sdc` launcher on `PATH` (`sdc help` lists every command)

## Quick Start

| Step | Action | Command |
|------|--------|---------|
| 1 | Inspect the skill tree | `sdc lint` |
| 2 | Create a new skill from a described job | `sdc --create <category>/<skill> [--dry-run]` |
| 3 | Audit + repair an existing skill | `sdc --improve <category>/<skill> [--dry-run]` |
| 4 | Collapse overlapping skill folders | `sdc --prune <category> [--dry-run]` |
| 5 | Dry-run (report only, no changes) | Append `--dry-run` to any command |

Every command is a plain `sdc <noun> <action>` subcommand; run `sdc help` for the full table.

## Reference

| Artifact | Purpose | Link |
|----------|---------|------|
| AGENTS.md | Agent operational guide (runtime, structure, commands) | [AGENTS.md](AGENTS.md) |
| PRD.md | What the product does and why | [PRD.md](PRD.md) |
| ROADMAP.md | What ships next, in order | [ROADMAP.md](ROADMAP.md) |
| ARCHITECTURE.md | Layer contract and linter rule catalog | [ARCHITECTURE.md](ARCHITECTURE.md) |
