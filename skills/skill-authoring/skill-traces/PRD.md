# PRD — skill-traces

## Project Overview

skill-traces is the trace-learning skill that curates one trace-learning run across three dispositions at once: create new skills from repeated instructions and open gaps (`--learn`), fix stale lines in loaded skills (`--evolve`), and retire skills the window shows as never used (`--unlearn`). The trace pipeline runs session scanning, skills-only usage reporting, repeated-phrase mining, and artifact materialization, then writes `usage.json` and `phrases.json` into the run dir before `learn-traces` launches. Each mode applies only the action kinds it owns, and one trace-state decide line is recorded per applied action.

## Goals

- Learn new skills from repeated hand-typed instructions and open gaps (`--learn`).
- Evolve stale lines in loaded skills (`--evolve`).
- Unlearn unused skills, deleting or retiring them (`--unlearn`).

## Non-Goals

- Recounting usage or phrases by hand (the trace pipeline materializes them).
- Running any agent other than the trace-learning workflow.
- Touching any file outside `skills/skill-authoring/skill-traces/`.

## Target Users

| Persona     | Need                                         | Current Pain                            | Desired Outcome                        |
|-------------|----------------------------------------------|-----------------------------------------|----------------------------------------|
| Skill author| Create new skills from repeated instructions | No signal on which skills are needed    | `actions.json` with `create` actions   |
| Skill owner | Fix stale skill lines                        | Skills drift out of sync with reality   | `actions.json` with `edit` actions     |
| Pack maintainer | Retire unused skills                      | Unused skills clutter the tree          | `actions.json` with `delete` actions   |

## Scope

### In Scope

- The three invocation modes `--learn`, `--evolve`, `--unlearn` (at least one required).
- Read-only pipeline ops: `collect`, `usage`, `phrases`.
- Materialization op: `materialize`.
- Lifecycle state machine ops: `state get|set|clear|trash|restrict|decide|wait`.
- Exit-code contract for `state wait`: 0 ready / 1 phase-stall / 3 report-stall / 2 deadline.
- Deterministic material: `usage.json` and `phrases.json` written by the trace pipeline.
- Record: one trace-state decide line per applied action (`--kind skill`, `--decision applied|rejected|deferred`).

### Out of Scope

- Writing `usage.json`/`phrases.json` by hand (owned by the trace pipeline).
- Any runtime agent execution of trace content.

---

## Project Requirements

### PR-SKILLTRACES-001: trace-learning lifecycle across three dispositions
<!-- Tier P0: entry -001 is always P0. -->

#### User Stories

| As a | I want | So that | Priority |
|------|--------|---------|----------|
| Skill author | Learn skills from repeated instructions | I don't author skills by hand | `actions.json` carries `create` actions |

#### Proposed Solution

The `--learn` path owns report sections 1 (Repeated phrases → skills) and 4 (Gaps), applies action kinds `create`, `propose`, `ask`, and records one decide line per action under the `--kind skill` flag.

#### Main User Flow

1. User invokes `stc traces --learn [--evolve] [--unlearn]`.
2. The trace pipeline scans sessions and materializes `usage.json`/`phrases.json`.
3. `learn-traces` launches and blocks on trace-state wait.
4. Each mode applies its action kinds; one decide line is recorded per action.

### PR-SKILLTRACES-002: trace-learning state protocol
<!-- Tier P1: the first P1 entry. -->

#### User Stories

| As a | I want | So that | Priority |
|------|--------|---------|----------|
| Pack maintainer | Drive the state machine via `stc traces state` | I can wait for report readiness | Exit codes surface wait outcome |

#### Proposed Solution

`stc traces state wait` blocks until the run dir holds `report.md` + `actions.json`, then exits 0 ready / 1 phase-stall / 3 report-stall / 2 deadline per the exit-code contract.

#### Main User Flow

1. User invokes `stc traces state wait`.
2. The state capability polls for `report.md` + `actions.json`.
3. On readiness it exits 0; on stall/deadline it exits 1 / 3 / 2.

### PR-SKILLTRACES-003: trace-learning artifact materialization
<!-- Tier P2: the first P2 entry. -->

#### User Stories

| As a | I want | So that | Priority |
|------|--------|---------|----------|
| Skill author | Inspect `usage.json` and `phrases.json` | I can verify what the trace pipeline recorded | `usage.json`/`phrases.json` exist in run dir |

#### Proposed Solution

The trace pipeline materializes `usage.json` and `phrases.json` into the run dir before `learn-traces` launches, with one decide line per applied action recorded under `--kind skill`.

#### Main User Flow

1. Trace pipeline scans sessions and runs usage/phrase extraction.
2. Pipeline writes `usage.json` and `phrases.json` into the run dir.
3. `learn-traces` launches and the decide line is recorded per action.

## Reference

| Artifact     | Purpose                                          | Link |
|--------------|--------------------------------------------------|------|
| PRD          | Business goals and scope                         | [PRD.md](PRD.md) |
| Backlog      | What is true now, with evidence                  | [BACKLOG.md](modules/skills_traces/BACKLOG.md) |
| Roadmap      | Timeline, phasing, and dependencies              | [ROADMAP.md](ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra         | [ARCHITECTURE.md](ARCHITECTURE.md) |
