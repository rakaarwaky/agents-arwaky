# FRD — check


## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md)


## System Overview

`aa check` is the repository quality gate: two independent runners fan out
under one orchestrator, then collapse to a single exit code for CI and
operators. Either runner can be selected alone via a standard scope.

Surface scopes: `aa check`, `aa check docs [path]`, `aa check skill`
(the docs scope also accepts `--json` and `--include-subtrees`;
every finding gates — there is no `--strict` flag or advisory tier).
Two independent runners fan out under one
orchestrator: a document-invariant runner and a skill-pack runner.
Selected runners run in fixed order (docs, then skill), share no mutable
state, each run strict (the CLI's only mode), and collapse the summed error count
to a single 0 / 1 exit after the banner and final
`PASSED` / `FAILED with N errors` line. Runners return codes, not
exceptions; a runner that raises is not caught (contract).


## Functional Requirements

### FR-CHECK-001: Document invariant audit

- **Description**: `DocsCheckRunner.run()` audits the doc chain
(PRD / ROADMAP / FRD / BACKLOG / README / AGENTS) plus skill references
against the add-docs invariant set.
- **Input**: repo tree anchored at `repo_root()`; optional
`include_subtrees` on the audit helper.
- **Output**: count of error-level findings (0 = clean); each finding is
`code path: message`.
- **Business Rules**: engine is the shared document-invariant audit; the
CLI is strict-only — every finding gates (`as_strict` at engine exit),
there is no `--strict` flag and no advisory tier, and `skills/` findings
gate like any other;
`aa check docs` runs this runner alone; `aa check docs [path]` exposes the
same engine with `--json`, `--include-subtrees`, and a path argument.
- **Edge Cases**: feature spec without backlog → `spec-without-backlog`;
FRD/BACKLOG under `shared/` → `feature-doc-in-shared`;
source-file name in PRD/FRD → `spec-source-path`;
restated state vocab in a feature backlog → `state-vocab-restated`;
`Done` row without command + commit → `done-without-evidence`; dead
markdown link → `dead-link` (always gating).
- **Error Handling**: read-only; never mutates documents; findings only.

### FR-CHECK-002: Skill-pack loadability audit

- **Description**: `SkillsCheckRunner.run()` audits every
`skills/<category>/<skill>/SKILL.md` against the harness loadability
invariants.
- **Input**: pack root `<repo>/skills`.
- **Output**: count of pack findings (0 = loadable); success line reports
skill count + category count.
- **Business Rules**: engine is the shared skill-pack audit; invariants
are layout exactly three path segments, frontmatter `name:` present and
equal to the folder, non-empty `description`, names unique pack-wide,
aggregate description bytes ≤ the description budget, no empty
category, no skill folder missing `SKILL.md`.
- **Edge Cases**: empty pack → `pack-missing`; nested skill deeper than
`<category>/<skill>/SKILL.md` → `nested-layout` (harness scans one level);
duplicate `name:` across categories → `duplicate-name`.
- **Error Handling**: read-only; every finding is an error for the gate
(loadability is binary — a skill either loads or it does not).


## API Contract


| Method | Input | Output | Error | Event | Description |
|---|---|---|---|---|---|
| `CheckOrchestrator.check` | `only: str\|None=None` | `CheckExitCode(0\|1)` | unknown scope → non-zero; any runner error → 1 | banner; `[i/n]` steps; final `PASSED` / `FAILED with N errors` | Surface: `aa check [all\|docs\|skill]` |
| `DocsCheckRunner.run` | — | `CheckExitCode(len(problems))` | any finding → non-zero (strict-only; no advisory tier) | progress `Validating document invariants…`; findings `code path: message` | Capability: `aa check docs` (FR-CHECK-001) |
| `SkillsCheckRunner.run` | — | `CheckExitCode(len(findings))` | any pack finding → non-zero; empty pack → `pack-missing` | progress `Validating skill pack loadability…`; findings; skill + category count | Capability: `aa check skill` (FR-CHECK-002) |

## Integration Points


| System                                                     | Direction | Purpose                                       | Failure mode                |
| ---------------------------------------------------------- | --------- | --------------------------------------------- | --------------------------- |
| root CLI (`aa`)                                            | in        | routes `aa check [scope]` incl. `aa check docs [path]` | none — pass-through         |
| shared doc-invariant engine                                | out       | document invariant audit                      | repo-root/anchor error      |
| shared skill-pack audit                                    | out       | pack layout / loadability audit               | pack-missing if no SKILL.md |
| shared check contracts                                     | out       | runner / aggregate protocols                  | —                           |
| shared path + logging helpers                              | out       | repo root anchor; banner/err/ok/warn          | unanchored tree             |
| CI workflow                               | out       | runs the same gate as the exit code CI trusts | red build on non-zero       |


## Non-functional Requirements


| Metric        | Target                                          | Measurement method                                  |
| ------------- | ----------------------------------------------- | --------------------------------------------------- |
| Determinism   | identical tree → identical findings + exit code | run `aa check` twice; byte-identical output         |
| Read-only     | the gate mutates nothing                        | `git status --porcelain` unchanged after `aa check` |
| Gate speed    | full gate under 2 minutes on a warm host        | time `aa check` on the tree                         |
| Exit fidelity | process exit == orchestrator `CheckExitCode`    | `echo $?` after `aa check`                          |


## Test Scenarios

- `aa check` on a clean tree exits 0 and reports all verifications PASSED.
- `aa check` fails when any finding exists (strict-only; no advisory tier).
- `aa check docs` runs only the document-invariant runner and skips skill audit.
- `aa check skill` runs only the skill-pack runner and skips doc audit.
- `aa check --bogus` (unknown scope) prints usage and exits non-zero.
- A `Done` row without a commit hash is reported by `done-without-evidence`.
- The gate is read-only: no working-tree changes after it runs.
- `aa check` runs docs first then skills (`[1/2]`, `[2/2]`) before the summary.
- A skill at the wrong nesting depth is reported by `nested-layout` and
fails the gate.
- A skill whose frontmatter `name` differs from its folder is reported by
`name-mismatch` and fails the gate.
- `aa check docs [path] --json` emits machine-readable `errors` / `warnings`
arrays without the human banner.


## Assumptions &amp; Constraints

- Runs from a checkout that has the tool manifest (repo-root anchor).
- Engines stay in the shared kernel; this feature only wires runners and
  owns the exit-code contract.
- Removed runners (json / python / shell) are out of scope — delegated to CI
  and the architecture linter.


## Glossary

- **gate**: the `aa check` exit code that CI and operators use as the
pass/fail signal.
- **finding**: one invariant violation reported as `code path: message`.
- **runner**: one document or skills capability under the orchestrator.
- **strict**: the gate's only mode — every finding, warning included, is a failure; the CLI exposes no flag to turn it off.
- **pack**: the `skills/` tree a harness scans one level below each
registered root.

