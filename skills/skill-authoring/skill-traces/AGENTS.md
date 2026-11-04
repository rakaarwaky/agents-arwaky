---
trigger: always
description: "AGENTS.md operational guide for skill-traces pack."
---

# AGENTS — skill-traces

## Agent Overview

skill-traces is the trace-learning skill that curates one trace-learning run across three dispositions: learn new skills from repeated instructions and open gaps (`--learn`), fix stale lines in loaded skills (`--evolve`), and retire skills the window shows as never used (`--unlearn`). Agents generating code, docs, or suggestions must only edit files under `skills/skill-authoring/skill-traces/` and must keep the trace pipeline's deterministic material (`usage.json`, `phrases.json`) and decide-line record intact.

## Runtime

| Aspect          | Detail                                          |
|-----------------|-------------------------------------------------|
| Language        | Python                                          |
| Environment     | `uv` (Python package manager)                   |
| Artifacts       | `usage.json`, `phrases.json`, `actions.json`, `report.md` |
| Package Manager | uv                                              |
| Version Probe   | `uv --version`                                  |
| Setup           | `uv sync`                                       |
| Activation      | `source .venv/bin/activate`                     |

## Project Structure

```text
skills/skill-authoring/skill-traces/
├── PRD.md                      # What the skill does and why
├── ROADMAP.md                  # What ships next, in order
├── README.md                   # How to use/run
├── AGENTS.md                   # This file — how to work here safely
├── ARCHITECTURE.md             # Layer contract and linter rule catalog
├── SKILL.md                    # Skill frontmatter + routing table
├── lint_arwaky.config.yaml     # Lint gate configuration
├── references/                 # Step-by-step workflow references
├── scripts/                    # Non-trivial logic referenced by SKILL.md
└── modules/skills_traces/      # AES layer implementation
    ├── src/                    # agent + capability layers
    ├── shared/src/skills_traces/  # shared kernel (contract, taxonomy, utility)
    ├── cli/                    # stc surface (DESIGN + BACKLOG)
    └── tests/                  # unit / integration / e2e / smoke tests
```

## Commands

| Category    | Command                              | Scope      | CI Gate              |
|-------------|--------------------------------------|------------|----------------------|
| Test (all)  | `uv run pytest skills/skill-authoring/skill-traces/modules/skills_traces/tests -q` | All | ci.yml: Module tests |
| Test (unit) | `uv run pytest skills/skill-authoring/skill-traces/modules/skills_traces/tests -q -m "not dogfood"` | One unit | ci.yml: Skills and shared tests |
| Test (file) | `uv run pytest <path-to-test-file> -q` | One file | ci.yml: Module tests |
| Lint        | `stc lint`                           | All        | ci.yml: Skill pack lint |
| Type Check  | `uv run mypy skills/skill-authoring/skill-traces/modules/skills_traces` | All | ci.yml: Python compile check |
| Arch Scan   | `lint-arwaky scan skills/skill-authoring/skill-traces` | All | ci.yml: Architecture scan |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| README       | What the tool does, every command, install | [README.md](README.md) |
| PRD          | What the product does and why              | [PRD.md](PRD.md) |
| ROADMAP      | What ships next, in order                  | [ROADMAP.md](ROADMAP.md) |
| ARCHITECTURE | Layer contract for every crate             | [ARCHITECTURE.md](ARCHITECTURE.md) |
