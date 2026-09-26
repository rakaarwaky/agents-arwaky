# FRD — check


## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.


## System Overview

The check feature is the repository quality gate behind `aa check`: the
capability protocol declares one method per audit (`run(scope)` on
`ICheckProtocol`), and the aggregate (`check`, `check_docs`, `check_skill`,
`summary`) exposes each path to the CLI through its single
`execute(request) → response` entry point. Flow: root CLI → check aggregate
→ document-invariant audit and/or skill-pack audit (fixed order: docs, then
skill) → shared audit engines → findings collapsed into one exit code.
Either audit runs alone via its scope, every finding gates, and the process
exit equals the aggregate exit.


## Functional Requirements

### FR-CHECK-001: Audit document invariants

- **Description**: Audits the document chain (PRD, ROADMAP, FRD, BACKLOG,
  README, AGENTS) plus skill references against the add-docs invariant set
  and reports every violation as a finding.
- **Input**: repository tree anchored at the repo root; the docs scope also
  accepts an optional path argument, machine-readable output, and a
  subtree-inclusion flag on the CLI.
- **Output**: exit code 0 when clean, otherwise non-zero; each finding is
  printed as `code path: message`.
- **Business Rules**: the shared document-invariant engine is the single
  source of truth; the gate is strict-only — every finding, warning
  included, gates, with no advisory tier and no flag to disable it;
  `aa check docs` runs this audit alone, and `aa check docs [path]` scopes
  the same engine to one directory.
- **Edge Cases**: feature FRD without a sibling backlog → `spec-without-backlog`;
  FRD/BACKLOG under a shared kernel → `feature-doc-in-shared`; source-file
  name in PRD/FRD → `spec-source-path`; restated state vocabulary in a
  feature backlog → `state-vocab-restated`; a `Done` row without command +
  hash → `done-without-evidence`; dead markdown link → `dead-link` (always
  gating).
- **Error Handling**: read-only — the audit never mutates documents;
  unreadable paths surface as findings; any finding yields a non-zero exit.

### FR-CHECK-002: Audit skill pack loadability

- **Description**: Audits every skill in the pack against the harness
  loadability invariants: layout, name parity, description presence, name
  uniqueness, and the aggregate description budget.
- **Input**: pack root at `skills/` under the repo root.
- **Output**: exit code 0 when loadable, otherwise non-zero with one
  printed line per finding; the success line reports skill and category
  counts.
- **Business Rules**: the shared skill-pack audit is the single source of
  truth; invariants are layout exactly three path segments
  (category, skill, `SKILL.md`), frontmatter `name:` present and equal to
  the folder, non-empty `description:`, names unique pack-wide, aggregate
  description bytes within the budget, no empty category, and no skill
  folder missing `SKILL.md`; every finding is an error — loadability is
  binary.
- **Edge Cases**: empty or missing pack → `pack-missing`; a skill nested
  below the category/skill depth → `nested-layout` (the harness scans one
  level); duplicate `name:` across categories → `duplicate-name`;
  frontmatter name differing from the folder → `name-mismatch`.
- **Error Handling**: read-only; findings only; any finding yields a
  non-zero exit.

### FR-CHECK-003: Dispatch scope to the right audit path

- **Description**: Routes the requested scope (`all`, `docs`, `skill`) to
  the matching audit path or paths under one aggregate call.
- **Input**: scope token from the CLI — `all` (default) selects both
  audits, `docs` and `skill` select one each, and aliases are accepted —
  plus the docs-only path/output flags handled by the document audit.
- **Output**: one exit code for the run; one step line per selected audit;
  a final `PASSED` / `FAILED with N errors` line after the findings.
- **Business Rules**: selected audits run in fixed order (docs, then
  skill) with no shared mutable state; findings sum across selected audits
  into the single gate result; an unknown scope prints usage and exits
  non-zero without running any audit; capabilities signal through return
  codes, not exceptions — a capability that raises is a contract breach,
  not a caught error.
- **Edge Cases**: unknown scope token → usage + non-zero, zero audits run;
  empty selection for a known-but-unregistered key → non-zero; one audit
  failing while the other passes still fails the gate with the summed
  error count.
- **Error Handling**: unknown scope → non-zero with usage; audit failures
  collapse to exit 1 after the summary line; the process exit equals the
  aggregate exit code.


## API Contract

### Protocol API

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `run` | `scope` (`all\|docs\|skill`) | exit code | non-zero gate | — | one method per audit capability; one method covers the docs + skill audit |

### Aggregate API

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `check` | `scope` (`all\|docs\|skill`) | exit + findings | unknown scope or any finding → non-zero | banner; step lines; final `PASSED` / `FAILED with N errors` | Dispatch the scope to the selected audit path |
| `check_docs` | — | exit + findings | any document finding → non-zero | docs step + findings | Audit document invariants only |
| `check_skill` | — | exit + findings | any pack finding → non-zero | skill step + counts | Audit skill pack loadability only |
| `summary` | findings | summary line | — | — | Collapse findings into one digest line |

## Integration Points


| System | Direction | Purpose | Failure mode |
| -------- | --------- | --------- | ------------ |
| root CLI (`aa`) | in | routes `aa check [scope]`, including `aa check docs [path]`, to the aggregate | unknown scope → usage + non-zero |
| shared document-invariant engine | out | document invariant audit (FR-CHECK-001) | unanchored tree → non-zero |
| shared skill-pack audit engine | out | pack layout / loadability audit (FR-CHECK-002) | missing pack → `pack-missing` |
| shared check contracts | out | protocol + aggregate signatures this feature adopts | — |
| CI workflow | out | runs the same gate as the exit code CI trusts | non-zero → red build |


## Non-functional Requirements


| Metric | Target | Measurement method |
| -------- | -------- | --------- |
| Strict-only | every finding gates; no advisory tier and no flag to disable it | plant one warning-level finding → `aa check docs` exits non-zero |
| Determinism | identical tree → identical findings and exit code | run `aa check` twice; byte-identical output |
| Gate speed | full gate finishes in under 2 minutes on a warm host | time `aa check` on the tree |
| Read-only | the gate mutates nothing | `git status --porcelain` unchanged after `aa check` |
| Exit fidelity | process exit equals the aggregate exit code | `echo $?` after `aa check` |


## Test Scenarios

- `aa check docs` on a tree whose documents satisfy every invariant exits 0 and reports zero findings.
- A feature backlog `Done` row without a command and commit hash in its condition cell fails the gate with `done-without-evidence`.
- `aa check skill` on a loadable pack exits 0 and reports skill and category counts.
- A skill nested deeper than the category/skill depth fails the gate with `nested-layout`.
- `aa check docs` runs only the document audit and never enters the skill audit path.
- An unknown scope such as `aa check bogus` prints usage and exits non-zero without running any audit.


## Assumptions & Constraints

- Runs from a checkout that holds the tool manifest (repo-root anchor).
- Engines stay in the shared kernel; this feature wires the audit paths
  and owns the exit-code contract.
- The removed runners (json, python, shell) are out of scope — delegated
  to CI and the architecture linter.
- Strict-only is permanent: there is no advisory tier to reintroduce as a
  flag.


## Glossary

- **gate**: the `aa check` exit code that CI and operators treat as the
  pass/fail signal.
- **finding**: one invariant violation reported as `code path: message`.
- **scope**: the token (`all`, `docs`, `skill`) selecting which audit path
  runs.
- **strict**: the gate's only mode — every finding, warning included, is a
  failure; the CLI exposes no flag to turn it off.
- **pack**: the `skills/` tree a harness scans one level below each
  registered root.
