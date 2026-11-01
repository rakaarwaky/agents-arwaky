# Feature Backlog: harness

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-10-26

## Progress Overview

The harness feature wires the tool ecosystem into AI coding harnesses (Hermes, OpenCode, Grok Build) via per-seam protocols for connect/disconnect/skill-provisioning and stateless provider-leaf adapters (hermes, opencode, grok-build). Router wiring to local OmniRoute/9router gateways is a clause of connect/disconnect. Gate: `./.venv/bin/python -m pytest modules/harness -q` → 45 passed and Ruff is clean at `767b18672a0c0abd92f7225f267478db8271c334`.

## Backlog Status

### FR-HARNESS-001: Connect a harness (MCP, env, router, skills)

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `capabilities_harness_connector.py` connects all three registered providers with MCP config + skill-pack provisioning; `test_supported_harnesses_connect_disconnect_and_skills_roundtrip` covers every canonical id; 45 harness tests pass at `767b186`. |
| In Progress  | None                                                         |
| Risk         | Live host router check remains operator-specific             |
| Updated      | 2026-10-26                                                   |

### FR-HARNESS-002: Disconnect a harness cleanly

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `capabilities_harness_disconnector.py` removes generated config/links/idempotently and treats untouched providers as no-ops; asserted before connection in the matrix test; 45 harness tests pass at `767b186`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### FR-HARNESS-003: Provision the skill pack into a harness

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `capabilities_harness_skills.py` provisions/re-provisions/copies the pack per canonical provider; re-provisioning asserts no damage to harness config; 45 harness tests pass at `767b186`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### FR-HARNESS-004: Resolve id, alias, or `--all` to canonical targets

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | Target resolution backed by `taxonomy_harness_constant.py` and the aggregate; aliases map through the taxonomy alias table; `--all` expands to every supported id; 45 harness tests pass at `767b186`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | Business goals and scope                   | [PRD.md](../../PRD.md) |
| FRD          | Functional requirements specification       | [FRD.md](FRD.md) |
| Roadmap      | Timeline, phasing, and dependencies        | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](../../ARCHITECTURE.md) |
