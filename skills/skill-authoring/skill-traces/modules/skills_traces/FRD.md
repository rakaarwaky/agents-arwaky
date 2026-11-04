# FRD — skills_traces

> Functional Requirements Document. Describes HOW the trace/learning
> pipeline feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Feature Overview

The skills-traces feature implements the agent trace/learning pipeline:
session scanning, skills-only usage reporting, repeated-phrase mining,
artifact materialization, and the trace-learning lifecycle state machine
(status, trash, decisions, wait). It is a sibling of
`skills/skill-authoring/skill-design/modules/skills_design`; both share the `modules/shared/src/skills`
contract and taxonomy layers.

The pipeline reads session traces from `$GROK_HOME/sessions` and the
`skills/` pack, and writes run-dir artifacts (`manifest.json`,
`sessions/*.json`, `usage.json`, `phrases.json`) plus lifecycle
state under `$GROK_HOME/learn`. The composition root wires
`SkillsTraces` (this module's capability) into the shared agent, so
`SkillsOp.TRACES` is dispatched end-to-end through one aggregate
entry point.

Read-only pipeline ops: `collect`, `usage`, `phrases`.
Materialization op: ``materialize``. Lifecycle state machine ops:
`state get|set|clear|trash|restrict|decide|wait`. The exit-code
contract for ``state wait`` is 0 ready / 1 phase-stall / 3
report-stall / 2 deadline.

## Functional Requirements

### FR-SkillsTraces-009: Trace Learning Lifecycle

**Description:** Scan sessions, build skills-only usage, mine repeated phrases, materialize on-disk artifacts, and drive the trace-learning state machine (status, trash, decisions, wait).

#### Business Logic

- `traces` is a fully functional CLI surface verb — `stc traces <action>` routes to the traces surface command
- `collect` scans sessions and builds the usage report
- `usage` reads the last run's usage report
- `phrases` mines repeated prompts and instruction lines
- `materialize --run-dir DIR` writes `usage.json` + `phrases.json` into the run dir
- `state <get|set|clear|trash|restrict|decide|wait>` drives the lifecycle state machine
- `state get` exits 3 while a run is pending (domain signal that a trace run is in progress)

#### Edge Cases

- Missing run dir for `materialize` is a usage error (exit 2)
- `state wait` blocks until `report.md` + `actions.json` exist; phase-stall exits 1, report-stall exits 3, deadline exits 2
- `stc traces` with no sub-action prints usage and exits 2
- `stc traces <unknown>` exits 2 with an unknown-action error

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | action sub-command; optional flags per action |
| **Output** | scan results, usage reports, phrase reports, state transitions |
| **Protocol** | ISkillsTraceScanProtocol (FR-SkillsTraces-009), ISkillsTraceStateProtocol (FR-SkillsTraces-010) |
| **Method** | scan_sessions / build_usage / build_phrases / set_status / get_status / trash / decide / wait / dispatch |
| **Event** | — |
| **Error** | unknown action → usage error (exit 2); missing run dir → usage error (exit 2) |

### FR-SkillsTraces-010: Trace Learning State Protocol

**Description:** Drive the trace-learning lifecycle state machine (status, trash, decisions, wait, restrict, dispatch).

#### Business Logic

- `state <get|set|clear|trash|restrict|decide|wait>` drives the lifecycle state machine
- `state get` exits 3 while a run is pending (domain signal that a trace run is in progress)
- `set_status` records the pending run's status; `done` stamps last_completed
- `trash` moves validated paths into `learn/trash/<run_name>`
- `decide` appends one decision line to `learn/decisions.jsonl`
- `wait` blocks until `report.md` + `actions.json` exist under the run dir

#### Edge Cases

- `state wait` blocks until `report.md` + `actions.json` exist; phase-stall exits 1, report-stall exits 3, deadline exits 2
- Trash refuses any path that is not a `skills/<name>` directory, `workflows/*.rhai` file, or `hooks/*` file under GROK_HOME / `~/.agents` / project `.grok`

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | state sub-action; optional flags per sub-action |
| **Output** | state transitions, trash/restrict/decide output lines |
| **Protocol** | ISkillsTraceStateProtocol |
| **Method** | set_status / get_status / trash / restrict / decide / wait / dispatch |
| **Event** | — |
| **Error** | unknown action → usage error (exit 2) |

#### Test

| Context         | When Action                                | Then Observable Result                    |
|-----------------|--------------------------------------------|-------------------------------------------|
| CLI access      | `stc traces <action>`               | routes to `cmd_traces`, executes action   |
| CLI no action   | `stc traces`                        | usage help printed, exit 2                |
| CLI unknown     | `stc traces frobnicate`             | unknown-action error, exit 2              |
| Collect         | agent op `traces` action=collect           | sessions scanned, usage built, exit 0     |
| Wait ready      | agent op `traces` state=wait, files present | exit 0                                    |
| Phase stall     | agent op `traces` state=wait, phase stall | exit 1                                    |
| Report stall    | agent op `traces` state=wait, report stall| exit 3                                    |
| Deadline        | agent op `traces` state=wait, deadline    | exit 2                                    |

#### Metric

| Target Metric      | Value                                              |
|--------------------|----------------------------------------------------|
| Exit-code contract | 0 ready / 1 phase-stall / 3 report-stall / 2 deadline |

## Public Interface

| Aspect    | Detail             |
|-----------|--------------------|
| Agent     | Skills Agent (design-side, shared aggregate contract) |
| Aggregate | ISkillsAggregate (shared contract) |
| Method    | execute(request)   |
| Request   | SkillsRequest      |
| Response  | SkillsResult       |

## Reference

| Artifact     | Purpose                                           | Link                                     |
|--------------|---------------------------------------------------|------------------------------------------|
| PRD          | Business goals, user stories, and scope           | [PRD.md](../../../../../PRD.md)                   |
| Backlog      | Task tracking, epics, and implementation status   | [BACKLOG.md](BACKLOG.md)                 |
| ROADMAP      | Timeline, phasing, and dependencies               | [ROADMAP.md](../../../../../ROADMAP.md)           |
| ARCHITECTURE | System boundaries, tech stack, and infrastructure | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |
