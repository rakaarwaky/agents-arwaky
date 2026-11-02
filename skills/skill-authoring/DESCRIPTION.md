---
description: Skill-authoring skills — create, validate, and improve SKILL.md files, plus discover, inspect, migrate, and prune skill trees. Also learn from your own session traces in one pass: create skills for repeated instructions, edit skills that no longer match reality, and retire skills you never use.
---

## ROUTING — which skill do I use

| Goal | Skill | Entry point |
|---|---|---|
| Author / validate / audit a `SKILL.md` | `skill-design` | `aa skills validate | show | list` |
| Find / catalog / move / organize skills | `skill-library` | `aa skills catalog --check | discover | move | new-category` |
| Prune / consolidate / merge / weed / archive skill trees | `skill-lifecycle` | `aa skills weed | archive | merge-plan` |
| Create skills for things you keep typing out | `skill-learning` | `aa skills trace-collect | trace-usage | trace-phrases | trace-state` |
| Edit skills to adapt to conditions and demand | `skill-evolving` | `aa skills trace-collect | trace-usage | trace-phrases | trace-state` |
| Remove skills and surfaces you never use | `skill-unlearn` | `aa skills trace-collect | trace-usage | trace-phrases | trace-state` |
| Learn, evolve, and unlearn skills from session traces (one pass) | `skill-traces` | `/skill-traces --learn [--evolve --unlearn]` → `aa skills trace-collect | trace-materialize | trace-state` |

The trace-learning skill (`skill-traces`, modes `--learn` / `--evolve` / `--unlearn`) is driven by the `aa skills` trace verbs (`trace-collect`, `trace-materialize`, `trace-state`) backed by `capabilities_skills_traces` and `capabilities_skills_state`. See `README.md` for pack routing and `CATALOG.md` for the master index.
