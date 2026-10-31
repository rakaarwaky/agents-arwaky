---
description: Skill-authoring skills — create, validate, and improve SKILL.md files, plus discover, inspect, migrate, and prune skill trees. Also learn from your own session traces: create skills for repeated instructions, edit skills that no longer match reality, and retire surfaces you never use.
---

## ROUTING — which skill do I use

| Goal | Skill | Entry point |
|---|---|---|
| Author / validate / audit a `SKILL.md` | `skill-design` | `aa skills validate | show | list` |
| Find / catalog / repair / weed skills | `skill-library` | `aa skills catalog --check | discover | weed` |
| Prune / consolidate / merge skill trees | `skill-lifecycle` | `aa skills repair | move | archive | new-category | merge-plan` |
| Create skills for things you keep typing out | `skill-learning` | shared trace pipeline (`_trace-pipeline/scripts/collect_sessions.py`) |
| Edit skills to adapt to conditions and demand | `skill-evolving` | shared trace pipeline |
| Remove skills and surfaces you never use | `skill-unlearn` | shared trace pipeline |
| Orchestrate autonomous self-evolution | `skill-orchestrator` | shared trace pipeline + `aa skills` gates |

The three trace-learning skills (`skill-learning`, `skill-evolving`, `skill-unlearn`) share the deterministic pipeline under `_trace-pipeline/` (not a skill: no `SKILL.md` at its root). See `README.md` for pack routing and `CATALOG.md` for the master index.
