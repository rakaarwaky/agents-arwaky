# ROADMAP — skill-design

## Progress Overview

The skill-design pack ships three invocation modes — `--create`, `--improve`, `--prune` — each with its own reference set and completion criteria. All three are wired through the shared AES layer tree under `modules/skills_design`. The capability files (`capabilities_skills_lister/reader/linter/catalog/discover/creator/mover/archiver`), the agent orchestrator, and the root composition root are in place; the `sac lint` gate is the mechanical check every mode runs before declaring done. Nothing is blocked; the open work is extending the validator rule catalog to cover new body-shape edge cases as they are discovered.

## Roadmap Status

### PR-SKILLDESIGN-001: `--create` builds a publishable SKILL.md + references

| Aspect       | Detail                                                        |
|--------------|---------------------------------------------------------------|
| Priority     | P0                                                            |
| State        | Done                                                          |
| Backlog      | [BACKLOG.md](modules/skills_design/BACKLOG.md)               |

### PR-SKILLDESIGN-002: `--improve` audits then repairs an existing skill

| Aspect       | Detail                                                        |
|--------------|---------------------------------------------------------------|
| Priority     | P1                                                            |
| State        | Done                                                          |
| Backlog      | [BACKLOG.md](modules/skills_design/BACKLOG.md)               |

### PR-SKILLDESIGN-003: `--prune` collapses overlapping skills

| Aspect       | Detail                                                        |
|--------------|---------------------------------------------------------------|
| Priority     | P2                                                            |
| State        | Done                                                          |
| Backlog      | [BACKLOG.md](modules/skills_design/BACKLOG.md)               |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | Business goals, user stories, and scope    | [PRD.md](PRD.md) |
| Architecture | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](ARCHITECTURE.md) |
