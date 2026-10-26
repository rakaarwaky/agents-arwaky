# Feature Backlog: harness

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-10-26

## Current Condition

- Done: the feature uses per-seam protocols for connect, disconnect, skill
  provisioning, and provider operations. The registry currently defines
  three canonical providers — `hermes`, `opencode`, and `grok-build` — and
  the integration matrix exercises each without requiring live credentials.
  `./.venv/bin/python -m pytest modules/harness -q` → 45 passed and Ruff is
  clean at `767b18672a0c0abd92f7225f267478db8271c334`.
- In Progress: none.
- Blocked: none for implementation or automated verification.
- Next Action: none.

## Backlog

| ID | FRD Ref | Priority | State | Dependencies | Next Action | Updated | Actual Condition |
|---|---|---|---|---|---|---|---|
| HRS-01 | FR-HARNESS-001, FR-HARNESS-002, FR-HARNESS-003 | P1 | Done | HRS-06 | none | 2026-10-26 | `modules/harness/tests/integration_harness_matrix.py::test_supported_harnesses_connect_disconnect_and_skills_roundtrip` tests every registered canonical id; registry count is three (`hermes`, `opencode`, `grok-build`); `./.venv/bin/python -m pytest modules/harness -q` → 45 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| HRS-02 | — | P1 | Deferred | None | none | 2026-10-26 | No acceptance description, functional requirement, or scenario is assigned to this row; retain Deferred until its scope is specified. |
| HRS-03 | FR-HARNESS-001 | P1 | Done | None | none | 2026-10-26 | Connector capability and MCP/env/router wiring pass the harness `./.venv/bin/python -m pytest modules/harness -q` → 45 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| HRS-04 | FR-HARNESS-004 | P1 | Done | HRS-03 | none | 2026-10-26 | Canonical ids, aliases, and all-target resolution are covered by the harness unit/integration suite; `./.venv/bin/python -m pytest modules/harness -q` → 45 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| HRS-05 | FR-HARNESS-002 | P2 | Done | HRS-04 | none | 2026-10-26 | Idempotent disconnect is asserted before connection in `test_supported_harnesses_connect_disconnect_and_skills_roundtrip`; `./.venv/bin/python -m pytest modules/harness -q` → 45 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| HRS-06 | FR-HARNESS-001 | P1 | Done | HRS-04 | none | 2026-10-26 | Connect capability and aggregate behavior are exercised by the all-provider matrix; `./.venv/bin/python -m pytest modules/harness -q` → 45 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| HRS-07 | FR-HARNESS-003 | P1 | Done | HRS-04 | none | 2026-10-26 | Skills link provisioning, re-provisioning, and cleanup are asserted by the all-provider matrix; `./.venv/bin/python -m pytest modules/harness -q` → 45 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| FR-HARNESS-001 | FR-HARNESS-001 | P1 | Done | HRS-01 | none | 2026-10-26 | `capabilities_harness_connector.py` connects all three registered providers; matrix test and `./.venv/bin/python -m pytest modules/harness -q` → 45 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| FR-HARNESS-002 | FR-HARNESS-002 | P1 | Done | HRS-05 | none | 2026-10-26 | `capabilities_harness_disconnector.py` cleans generated config/links and treats untouched providers idempotently; matrix test and `./.venv/bin/python -m pytest modules/harness -q` → 45 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| FR-HARNESS-003 | FR-HARNESS-003 | P1 | Done | HRS-07 | none | 2026-10-26 | `capabilities_harness_skills.py` provisions/re-provisions the pack for each canonical provider; matrix test and `./.venv/bin/python -m pytest modules/harness -q` → 45 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| FR-HARNESS-004 | FR-HARNESS-004 | P1 | Done | HRS-04 | none | 2026-10-26 | Target resolution is backed by `taxonomy_harness_constant.py` and the aggregate; `./.venv/bin/python -m pytest modules/harness -q` → 45 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| Connecting each registered harness writes its MCP config and provisions the shared skill pack. | Automated | `modules/harness/tests/integration_harness_matrix.py` | `test_supported_harnesses_connect_disconnect_and_skills_roundtrip` | `767b186` |
| Router support follows the provider's declared capability. | Gap | — | provider-specific live router check remains separate | not yet |
| `disconnect --dry-run` reports planned changes without writing. | Manual | — | `aa disconnect --opencode --dry-run` | `f87a775` |
| Disconnecting an untouched harness is an idempotent no-op. | Automated | `modules/harness/tests/integration_harness_matrix.py` | `test_supported_harnesses_connect_disconnect_and_skills_roundtrip` | `767b186` |
| Skills provisioning can be rerun without damaging the harness config. | Automated | `modules/harness/tests/integration_harness_matrix.py` | `test_supported_harnesses_connect_disconnect_and_skills_roundtrip` | `767b186` |
| A harness lacking a skill directory reports a skip while other targets continue. | Gap | — | missing-skill-dir multi-target case not asserted | not yet |
| `connect --all` covers every supported canonical id. | Automated | `modules/harness/tests/integration_harness_matrix.py` | `test_supported_harnesses_connect_disconnect_and_skills_roundtrip` | `767b186` |
| An unknown harness token names the supported set and exits non-zero. | Manual | — | root CLI unknown-id check | `f87a775` |

Kind values: Automated, Proxy, Manual, Gap.

## Blockers

None for code or automated tests. The source registry contains three supported
providers; the earlier five-provider target is not present in the FRD or
registry and has not been expanded with unsupported adapters.

## Dependencies

Skill provisioning depends on the readable `skills/` pack. Router wiring
uses the OmniRoute endpoint resolver.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | Done | `./.venv/bin/python -m pytest modules/harness -q` → 45 passed at `767b18672a0c0abd92f7225f267478db8271c334` |
| Scenario evidence | QA | Connect/disconnect/skills behavior is automated for all three registered providers; two unrelated manual/gap cases remain explicit |
| Docs | Done | FR-HARNESS-001 through FR-HARNESS-004 each have an explicit backlog row |

## Deferred

- HRS-02 remains deferred because its task has no description or FRD/scenario mapping. A host-specific router check also remains outside the mock-backed matrix.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-26 | Per-seam protocol structure and 36-test evidence recorded. | @raka |
| 2026-10-26 | Added the all-provider matrix, mapped the three registered canonical ids, documented HRS-02 scope, and added explicit FR rows with evidence; 45 tests pass at `767b186`. | @raka |
