# FRD — check

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.

## System Overview

The check feature is the `aa check` quality gate: a fan-out of independent
verification runners aggregated into one exit code. `CheckOrchestrator`
(`agent_check_orchestrator.py`, implementing `ICheckAggregate` from
`contract_check_aggregate.py`) takes a list of `ICheckRunner` capabilities
(`contract_check_protocol.py`) and runs each; the aggregate is non-strict by
default and becomes strict (warnings fail the gate) via `check(strict=True)`.
Capability modules: JSON validation, Python compile, shell check, doc-pack
invariant audit, and skill-pack audit.

Flow: CLI surface → `CheckOrchestrator.check(strict)` → for each runner
`run(strict)` → any non-zero (or warning-in-strict) fails the gate.

## Functional Requirements

### FR-001: Aggregate independent check runners into one gate

- **Description**: `check(strict)` runs every registered runner and returns a
  single exit code.
- **Input**: `strict: bool` (False = warnings tolerated, True = warnings fail).
- **Output**: `int` exit code (0 = pass, non-zero = fail).
- **Business Rules**: runners are independent (no shared mutable state); the
  aggregate fails if any runner returns non-zero, or returns a warning under
  `strict=True`. Runner order is stable and deterministic.
- **Edge Cases**: zero runners → immediate pass (vacuous gate); a runner that
  raises → treated as a failure with the exception captured, not a crash.
- **Error Handling**: non-zero exit code; per-runner results are logged for the
  operator to see which check failed.

### FR-002: Doc-pack invariant audit

- **Description**: the docs runner audits the doc chain (PRD/FRD/BACKLOG/README/
  AGENTS) against the invariant set.
- **Input**: the repo tree (anchored at the resolved repo root).
- **Output**: exit code 0 (no errors) or non-zero; findings by file/line.
- **Business Rules**: findings carry a stable code (`done-without-evidence`,
  `dead-link`, `prd-section-missing`, …). In strict mode warnings escalate to
  failures. A `Done` row must cite a backtick command span and a commit hash.
- **Edge Cases**: a feature spec with no backlog row → `spec-without-backlog`
  finding; a restated state-vocab table in a feature backlog →
  `state-vocab-restated`.
- **Error Handling**: audit never mutates docs; read-only, report-only.

## API Contract

| Operation | Input | Output | Error Shape | impl / intended |
|-----------|-------|--------|-------------|------------------------------|
| `ICheckAggregate.check` | `strict: bool` | `int` exit code | non-zero + logged runner results | impl |
| `ICheckRunner.run` | `strict: bool` | `int` | non-zero + findings | impl |
| `CheckOrchestrator.__init__` | `list[ICheckRunner]` | — | — | impl |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| `modules/shared` (manifest_reader, paths, doc_pack) | out | anchor root, read manifest, audit docs | repo-root/anchor error |
| host toolchain (ruff, shellcheck, python compileall) | out | per-domain verification | missing tool → runner reports skip/fail |
| `modules/cli` surface | in | `aa check [strict]` | none — pass-through |

## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| Determinism | identical tree → identical findings + exit code | run `aa check` twice; byte-identical output |
| Read-only | the gate mutates nothing | `git status --porcelain` unchanged after `aa check` |
| Gate speed | full gate under 2 minutes on a warm host | time `aa check` on the tree |

## Test Scenarios

- `aa check` on a clean tree exits 0 and reports all verifications PASSED.
- `aa check` under `strict` fails when a warning-level finding exists.
- A `Done` row without a commit hash is reported by `done-without-evidence`.
- The gate is read-only: no working-tree changes after it runs.

## Assumptions & Constraints

- Runs from a checkout that has `config/manifest.json` (repo-root anchor).
- External linters (ruff, shellcheck) may be absent on a minimal host; a missing
  tool is reported as skip/fail per the runner, not a crash.

## Glossary

- **gate**: the `aa check` exit code that CI and operators use as the pass/fail signal.
- **finding**: one invariant violation reported as `code file:line message`.
