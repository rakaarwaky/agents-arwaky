# FRD — check

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature;
  this file is specification only.

## System Overview

`aa check` is the repository quality gate: two independent runners fan out
under one orchestrator, then collapse to a single exit code for CI and
operators.

```
aa check [--strict]
  → root_cli_entry.cmd_check
  → create_check_feature()  (CheckContainer)
  → CheckOrchestrator.check(strict)
       [1/2] DocsCheckRunner   → utility_doc_pack.audit_docs
       [2/2] SkillsCheckRunner → taxonomy_common_vo.audit_pack
  → 0 = All verifications PASSED · non-zero = FAILED
```

Surface: `aa check` (aggregate gate) and `aa docs check` (docs findings only,
with `--strict` / `--json`). Engine lives in `modules/shared`; this feature
wires the runners and owns the exit-code contract.

## Functional Requirements

### FR-001: Aggregate independent check runners into one gate

- **Description**: `CheckOrchestrator.check(strict)` runs every registered
  `ICheckRunner` in stable order and returns one exit code.
- **Input**: `strict: bool` (False = warnings tolerated, True = warnings
  escalate to failures via `as_strict` on the docs side).
- **Output**: `CheckExitCode` — 0 if every runner returns 0; 1 if the summed
  error count is non-zero.
- **Business Rules**: runners share no mutable state; order is the
  container's list (`DocsCheckRunner`, then `SkillsCheckRunner`); each runner
  logs its own `[n/2]` progress line; the orchestrator prints the banner and
  the final `PASSED` / `FAILED with N errors` line.
- **Edge Cases**: zero runners → vacuous pass; a runner that raises → not
  caught here (contract: runners return codes, not exceptions); `--strict`
  is a single flag on the surface, forwarded to every runner.
- **Error Handling**: non-zero aggregate exit; per-runner findings already
  printed by each runner before the orchestrator summary.

### FR-002: Document invariant audit

- **Description**: `DocsCheckRunner.run(strict)` audits the doc chain
  (PRD / ROADMAP / FRD / BACKLOG / README / AGENTS) plus skill references
  against the add-docs invariant set.
- **Input**: repo tree anchored at `repo_root()`; optional
  `include_subtrees` on the audit helper.
- **Output**: count of error-level findings (0 = clean); each finding is
  `code path: message`.
- **Business Rules**: engine is `utility_doc_pack.audit_docs`; errors always
  gate; under `strict`, warnings become errors (`as_strict`); warnings under
  `skills/` are counted but not printed in the gate (upstream pack shape);
  `aa docs check` exposes the same engine with `--strict`, `--json`,
  `--include-subtrees`.
- **Edge Cases**: feature spec without backlog → `spec-without-backlog`;
  restated state vocab in a feature backlog → `state-vocab-restated`;
  `Done` row without command + commit → `done-without-evidence`; dead
  markdown link → `dead-link` (always gating).
- **Error Handling**: read-only; never mutates documents; findings only.

### FR-003: Skill-pack loadability audit

- **Description**: `SkillsCheckRunner.run(strict)` audits every
  `skills/<category>/<skill>/SKILL.md` against the harness loadability
  invariants.
- **Input**: pack root `<repo>/skills`.
- **Output**: count of pack findings (0 = loadable); success line reports
  skill count + category count.
- **Business Rules**: engine is `taxonomy_common_vo.audit_pack`; invariants
  are layout exactly three path segments, frontmatter `name` present and
  equal to the folder, non-empty `description`, names unique pack-wide,
  aggregate description bytes ≤ `DESCRIPTION_BUDGET_BYTES`, no empty
  category, no skill folder missing `SKILL.md`.
- **Edge Cases**: empty pack → `pack-missing`; nested skill deeper than
  `<category>/<skill>/SKILL.md` → `nested-layout` (harness scans one level);
  duplicate `name:` across categories → `duplicate-name`.
- **Error Handling**: read-only; every finding is an error for the gate
  (loadability is binary — a skill either loads or it does not).

## API Contract

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `cmd_check` (surface) | `args: list[str]`, `orch: ICheckAggregate` | `int` (0 = pass, 1 = fail) | Propagates `orch.check()` failure as exit 1; no throw of its own | none | Parse `--strict`, delegate |
| `ICheckAggregate.check` | `strict: bool` | `CheckExitCode` (0 \| 1) | Runner count > 0 → return `CheckExitCode(1)`; a runner exception is not caught (bubbles to CLI) | none | Fan-out gate |
| `CheckOrchestrator.__init__` | `runners: list[ICheckRunner]` | `None` (stores list) | Non-`ICheckRunner` element → `AttributeError` on first `.run()` (caller contract violation) | none | Capability injection |
| `ICheckRunner.run` | `strict: bool` | `CheckExitCode` (error count ≥ 0) | Non-zero return signals findings; uncaught exception aborts the aggregate | none | One capability |
| `DocsCheckRunner.audit` | `strict: bool`, `include_subtrees: bool` | `list[DocFinding]` (empty = clean) | Read failure on a file → empty body, no raise (`_read` swallows `OSError`) | none | Doc engine call |
| `DocsCheckRunner.run` | `strict: bool` | `CheckExitCode(len(problems))` | Doc errors → non-zero count; `--strict` escalates warnings into `problems` | none | Docs runner |
| `SkillsCheckRunner.run` | `strict: bool` | `CheckExitCode(len(findings))` | Any pack finding → non-zero; empty pack → `pack-missing` (always fatal) | none | Skills runner |
| `create_check_feature` | — | `ICheckAggregate` (`CheckOrchestrator`) | None (pure wiring; no I/O) | none | Wire 2 runners + orchestrator |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| `modules/root_cli_entry.py` | in | routes `aa check` / `aa docs check` | none — pass-through |
| `modules/shared` `utility_doc_pack` | out | doc invariant engine | repo-root/anchor error |
| `modules/shared` `taxonomy_common_vo` | out | skill-pack `audit_pack` / `iter_skill_files` | pack-missing if no SKILL.md |
| `modules/shared` `contract_check_*` | out | `ICheckRunner` / `ICheckAggregate` protocols | — |
| `modules/shared` `utility_paths` / `utility_logging_setup` | out | `repo_root()`, banner/err/ok/warn | unanchored tree |
| CI (`.github/workflows/ci.yml`) | out | runs the same gate as the exit code CI trusts | red build on non-zero |

## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| Determinism | identical tree → identical findings + exit code | run `aa check` twice; byte-identical output |
| Read-only | the gate mutates nothing | `git status --porcelain` unchanged after `aa check` |
| Gate speed | full gate under 2 minutes on a warm host | time `aa check` on the tree |
| Exit fidelity | process exit == orchestrator `CheckExitCode` | `echo $?` after `aa check` |

## Test Scenarios

- `aa check` on a clean tree exits 0 and reports all verifications PASSED.
- `aa check` under `strict` fails when a warning-level finding exists.
- A `Done` row without a commit hash is reported by `done-without-evidence`.
- The gate is read-only: no working-tree changes after it runs.
- `aa check` runs docs as `[1/2]` then skills as `[2/2]` before the summary.
- A skill at the wrong nesting depth is reported by `nested-layout` and
  fails the gate.
- A skill whose frontmatter `name` differs from its folder is reported by
  `name-mismatch` and fails the gate.
- `aa docs check --json` emits machine-readable `errors` / `warnings` arrays
  without the human banner.

## Assumptions & Constraints

- Runs from a checkout that has `config/manifest.json` (repo-root anchor).
- Engines (`utility_doc_pack`, `audit_pack`) stay in `modules/shared`; this
  feature only wires runners and owns the exit-code contract.
- Removed runners (json / python / shell) are out of scope — delegated to CI
  and `lint-arwaky`.

## Glossary

- **gate**: the `aa check` exit code that CI and operators use as the
  pass/fail signal.
- **finding**: one invariant violation reported as `code path: message`.
- **runner**: one `ICheckRunner` capability (docs or skills) under the
  orchestrator.
- **strict**: flag that escalates warning-level findings to failures.
- **pack**: the `skills/` tree a harness scans one level below each
  registered root.
