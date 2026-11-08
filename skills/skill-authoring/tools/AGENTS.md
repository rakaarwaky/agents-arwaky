---
trigger: always
description: "AGENTS.md operational guide for skill-design pack."
---

# AGENTS — skill-design

## Agent Overview

skill-design is the skill-authoring skill that keeps the skill tree clean, correct, and consolidated. It runs one of three modes per invocation: `--create` builds a publishable `SKILL.md` plus its `references/` from a described job, `--improve` audits an existing skill against the shared lint standard and applies the repair edit recipe, and `--prune` collapses duplicate or same-purpose skills into one folder and archives the dropped duplicates. Agents generating code, docs, or suggestions must only edit files under `skills/skill-authoring/skill-design/` and must keep every flag and mode term in lockstep across `SKILL.md` and its reference files.

## Runtime

| Aspect          | Detail                                          |
|-----------------|-------------------------------------------------|
| Language        | Python                                          |
| Environment     | `uv` (Python package manager)                   |
| Artifacts       | `SKILL.md`, `references/`, `scripts/`           |
| Package Manager | uv                                              |
| Version Probe   | `uv --version`                                  |
| Setup           | `uv sync`                                       |
| Activation      | `source .venv/bin/activate`                     |

## Project Structure

```text
.
├── PRD.md                      # What the skill does and why
├── ROADMAP.md                  # What ships next, in order
├── README.md                   # How to use/run
├── AGENTS.md                   # This file — how to work here safely
├── CONTRIBUTING.md             # Branch, commit, and PR conventions
├── ARCHITECTURE.md             # Layer contract and linter rule catalog
├── SKILL.md                    # Skill frontmatter + routing table
├── lint_arwaky.config.yaml     # Lint gate configuration
├── template/                   # Canonical SKILL.md and reference templates
├── scripts/                    # Non-trivial logic referenced by SKILL.md
└── modules/skills_design/      # AES layer implementation
    ├── src/                    # agent + capability layers
    ├── shared/src/skills_design/  # shared kernel (contract, taxonomy, utility)
    └── tests/                  # unit / integration / e2e / smoke tests
```

## Commands

| Category    | Command                              | Scope      | CI Gate              |
|-------------|--------------------------------------|------------|----------------------|
| Test (all)  | `uv run pytest skills/skill-authoring/skill-design/modules/skills_design/tests -q` | All | ci.yml: Module tests |
| Test (unit) | `uv run pytest skills/skill-authoring/skill-design/modules/skills_design/tests -q -m "not dogfood"` | One unit | ci.yml: Skills and shared tests |
| Test (file) | `uv run pytest <path-to-test-file> -q` | One file | ci.yml: Module tests |
| Lint        | `sac lint`                           | All        | ci.yml: Skill pack lint |
| Type Check  | `uv run mypy skills/skill-authoring/skill-design/modules/skills_design` | All | ci.yml: Python compile check |
| Arch Scan   | `lint-arwaky scan skills/skill-authoring/skill-design` | All | ci.yml: Architecture scan |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| README       | What the tool does, every command, install | [README.md](README.md) |
| CONTRIBUTING | Branch, commit, and PR conventions         | [CONTRIBUTING.md](CONTRIBUTING.md) |
| PRD          | What the product does and why              | [PRD.md](PRD.md) |
| ROADMAP      | What ships next, in order                  | [ROADMAP.md](ROADMAP.md) |
| ARCHITECTURE | Layer contract for every crate             | [ARCHITECTURE.md](ARCHITECTURE.md) |
