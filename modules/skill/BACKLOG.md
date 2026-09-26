# Feature Backlog: skill

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-26

## Current Condition

- Done: `ISkillProtocol` split into two seam ABCs — `ISkillProvisionProtocol`
  (`provision` / `prune` / `audit`) and `ISkillRegistryProtocol`
  (`list` / `check` / `show` / `install` / `uninstall` / `sync`). The
  aggregate still exposes a single `execute(request)` entry point so
  surface/CLI call sites are unchanged; only the internal seam shape changed.
  Gate: `lint-arwaky-cli scan modules/skill` → 0 violations;
  `python3 -m pytest modules/skill -q` → 68 passed at `6df9f21`.
- In Progress: none.
- Blocked: none.
- Next Action: SKL-01 prune round-trip (stale provenance entry removed from
  a nested target; layout + path of the prune walk still outstanding).

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| SKL-01 | FR-SKILL-001 | Provision + prune skills with provenance | P1 | QA | Install + provenance verified on a scratch target at `f87a775`; prune round-trip still outstanding (stale entry not yet removed). | @raka | None | 2026-09-23 |
| SKL-02 | FR-SKILL-002 | Pack loadability audit (layout/name/description/budget) | P1 | Done | `python3 -m modules.root_cli_entry skill check` → Loadability: clean, 13 tools / 92 skills at `f87a775`. | @raka | None | 2026-09-23 |
| SKL-03 | FR-SKILL-001, FR-SKILL-002, FR-SKILL-003, FR-SKILL-004, FR-SKILL-005 | FRD + BACKLOG pair authoring for skill | P1 | Done | `python3 -m modules.root_cli_entry check docs modules/skill` → 0 findings at `f87a775`. | @raka | None | 2026-09-23 |
| SKL-04 | FR-SKILL-003 | Query skills (list / show) | P1 | Done | `python3 -m modules.root_cli_entry skill list` → tool table at `f87a775`; `skill show` unknown name → exit non-zero at `f87a775`. | @raka | None | 2026-09-23 |
| SKL-05 | FR-SKILL-004 | Install / uninstall through the CLI surface | P1 | Done | `python3 -m modules.root_cli_entry skill install testing-suite --target …` then `skill uninstall testing-suite --target …` → provisioned then removed, pack intact at `f87a775`. | @raka | SKL-01 | 2026-09-23 |
| SKL-06 | FR-SKILL-005 | Re-sync the pack (install all / sync) | P2 | Done | `python3 -m modules.root_cli_entry skill sync --target …` → all 92 pack skills provisioned at `f87a775`. | @raka | SKL-05 | 2026-09-23 |
| SKL-07 | FR-SKILL-001, FR-SKILL-002, FR-SKILL-003, FR-SKILL-004, FR-SKILL-005 | Split protocol into per-seam `ISkillProvisionProtocol` + `ISkillRegistryProtocol`; aggregate retains single `execute` entry | P1 | Done | `python3 -m compileall -q modules/skill modules/shared` clean + `lint-arwaky-cli scan modules/skill` → 0 violations + `python3 -m modules.root_cli_entry check docs modules/skill` → 0 findings at `6df9f21`; 68 tests pass. | @raka | None | 2026-09-26 |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `aa skill install` for a named skill into a target copies it with a provenance marker. | Proxy | manual | `python3 -m modules.root_cli_entry skill install testing-suite --target …` then inspect `.arwaky-skill.json` | `f87a775` |
| Installing the whole pack for a tool or for `all` copies every pack skill into the target workspace. | Proxy | manual | `python3 -m modules.root_cli_entry skill install all --target …` → 92 SKILL.md | `f87a775` |
| `aa skill check` reports layout, name-parity, description, uniqueness, and budget findings across the pack. | Proxy | manual | `python3 -m modules.root_cli_entry skill check` → Loadability: clean | `f87a775` |
| `aa skill install --prune --target .` removes provisioned copies the pack no longer provides, leaving hand-written skills in place. | Gap | — | — | not yet (prune walk still outstanding) |
| `aa skill list` enumerates every manifest tool with the shared pack size and exits 0. | Proxy | manual | `python3 -m modules.root_cli_entry skill list` → tool table, exit 0 | `f87a775` |
| `aa skill list` filtered to one tool prints that tool's skill rows and exits 0. | Proxy | manual | `python3 -m modules.root_cli_entry skill list lint` → filtered table, exit 0 | `f87a775` |
| `aa skill show` for a known skill prints its SKILL.md body and exits 0. | Proxy | manual | `python3 -m modules.root_cli_entry skill show lint-arwaky` → skill body, exit 0 | `f87a775` |
| `aa skill show` for an unknown name prints a not-found message and exits non-zero. | Proxy | manual | `python3 -m modules.root_cli_entry skill show definitely-not-a-skill-xyz` → exit 1 | `f87a775` |
| `aa skill uninstall` removes a provisioned skill directory while leaving the pack source intact. | Proxy | manual | `skill uninstall testing-suite --target …` → dir gone, pack 92 → 92 | `f87a775` |
| `aa skill sync` re-provisions the full pack for every tool into the target workspace. | Proxy | manual | `python3 -m modules.root_cli_entry skill sync --target …` → 92 SKILL.md | `f87a775` |

Kind values: Automated, Proxy, Manual, Gap.

## Blockers

None.

## Dependencies

None.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | Done | `python3 -m compileall -q modules/skill modules/shared` clean + `lint-arwaky-cli scan modules/skill` → 0 violations at `f87a775` |
| Scenario evidence | Done | 10 of 10 scenarios mapped (9 Proxy, 1 Gap) |
| Docs | Done | `python3 -m modules.root_cli_entry check docs modules/skill` → 0 findings at `f87a775` |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
| 2026-09-26 | `ISkillProtocol` split into `ISkillProvisionProtocol` (provision/prune/audit) + `ISkillRegistryProtocol` (list/check/show/install/uninstall/sync); aggregate keeps one `execute` entry point so surface/CLI unchanged. 68 tests, 0 violations at `6df9f21`. | @raka |
| 2026-09-23 | Realigned pair to approved skill plan: 5 FRs, single-row `execute` protocol, 6-row aggregate rename, 10 scenarios / 10 evidence rows; code collapsed the protocol to one method and renamed the aggregate methods. | @raka |
