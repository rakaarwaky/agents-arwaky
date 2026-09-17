# FRD.md — How a Feature Works, Functionally

> **Purpose**: Tell an engineer exactly what to build and tell QA exactly what to test —
> without a single follow-up question to the author.
>
> **Audience**: Engineers, QA, Tech Lead.
> **Scope**: One FRD per feature (a Python/TypeScript module or package, a Rust crate).
> **Location**: Inside the feature's directory, beside its `BACKLOG.md`. Never at the project root.
> **Length**: 50–500 lines (flat budget shared by every document type). An FRD's length
> naturally tracks its feature's complexity; the budget is a floor (gutted doc) and a
> bloat cap, not a target.

Checked by `aa docs check`:
`status-in-spec` · `duplicate-fr-id` · `orphan-fr-ref` · `scenario-without-evidence` ·
`scenario-evidence-count` · `unlinked-spec` · `frd-section-missing`.
Invariant definitions → [SKILL.md → Invariants](../SKILL.md#invariants).

---

## Rules

Eight rules. Each one prevents a specific failure mode.

1. **Requirement IDs are the contract.**
   `FR-001`, `FR-002`, … — unique within the feature (`duplicate-fr-id`) and stable forever.
   The backlog's `FRD Ref` column cites them; renumbering or reusing an ID silently un-grounds a
   `Done` row. To retire an ID, mark it retired in place. Never delete and shift.

2. **A requirement is testable, or it is a wish.**
   State input, output, business rules, edge cases, error handling. If you cannot write the
   assertion, split the requirement until you can.

3. **The API contract is exact.**
   Names, signatures, inputs, outputs, error shapes — as implemented *or* as intended. Never both
   in the same cell. Label which one the row represents.

4. **Scenarios are stated here; evidence lives in the backlog.**
   One scenario per bullet, in stable order, so `scenario-evidence-count` can match them against
   the evidence table.

5. **Non-functional numbers live here.**
   The PRD says "fast." This file says *what* the feature guarantees and *how* you measure it.

6. **Assumptions and constraints are written down.**
   Every implicit assumption is a requirement someone discovers later and calls a bug.

7. **Cross-link the pair** in `## Reference` (`unlinked-spec`).
   A reader landing on either file must immediately see promise (spec) and claim (backlog).

8. **No description of current behaviour.**
   A paragraph about what the source does today is a second copy of the code — and always staler
   (`status-in-spec`).

---

## Exemplar

### Weak — nobody can implement or test from this

```markdown
### FR-004: Validation

- **Description**: the checker validates the backlog.
- **Input**: file
- **Output**: errors
```

**Why it fails**: no business rule, no edge case, no error shape. An engineer must ask
five questions before writing one line. QA cannot write a single assertion.

### Strong — each bullet closes a decision; the last two give test and evidence

```markdown
### FR-004: Completed rows owe evidence

- **Description**: A Backlog row whose State is Done or Released must cite
  a re-run command and the commit it ran at.
- **Input**: One parsed Backlog table (header cells, `(line, cells)` rows).
- **Output**: `done-without-evidence` finding per offending row, carrying `file:line`.
- **Business Rules**: Evidence means a backtick code span naming a command
  AND a 7–40-character hex commit token. Either missing → finding.
- **Edge Cases**: Header shorter than a row → reported as `backlog-row-width`,
  not silently skipped. State cell empty → no claim, no finding.
- **Error Handling**: An unknown State word is reported by `unknown-state`,
  so a typo cannot pass as evidence-bearing.
```

### The pair it creates

| Side    | Content                                                                                              |
|---------|------------------------------------------------------------------------------------------------------|
| Spec    | `## Test Scenarios` → "a Done row with no commit hash is reported"                                  |
| Backlog | `CHK-04 │ FR-004 │ Ship evidence check │ P0 │ Done │ pytest … → 35 passed @ a1b2c3d │ @raka │ …`   |

---

## Template

Copy, fill, delete nothing.

```markdown
# FRD — <feature-name>

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Reference

- PRD: <link to root PRD.md>
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.

## System Overview

<One diagram or ≤ 3 sentences: where this feature sits, what calls it, what it calls.>

## Functional Requirements

### FR-001: <Short imperative name>

- **Description**: <what it does — one sentence>
- **Input**: <shape, source>
- **Output**: <shape, destination>
- **Business Rules**: <validation logic, constraints>
- **Edge Cases**: <boundary conditions and their handling>
- **Error Handling**: <what fails, what the caller sees>

### FR-002: <Short imperative name>

- …

## API Contract

| Operation | Input | Output | Error Shape | As Implemented / As Intended |
|-----------|-------|--------|-------------|------------------------------|
| `<fn>`   | …     | …      | …           | implemented                  |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| <name> | in / out  | …       | …            |

## Non-functional Requirements

| Metric       | Target        | Measurement method         |
|--------------|---------------|----------------------------|
| Response time| < p95 ms     | <tool, endpoint, dataset>  |
| Availability | < %          | <window, source>           |
| Security     | <standard>   | <audit / scan reference>   |

## Test Scenarios

- <Scenario stated as observable behaviour + expected result.>
- …

## Assumptions & Constraints

- <Assumption or constraint — name it, scope it, date it if it expires.>

## Glossary

- **Term**: <one definition, one meaning>
```

---

## Section Contract

Every section is required unless marked optional. Each exists for one reason.

| Section                     | Req? | Why it belongs here                              | Watch for                                  |
|-----------------------------|------|--------------------------------------------------|--------------------------------------------|
| Reference                   | ✓    | Separates spec (promise) from backlog (claim).   | Links that resolve to nothing.             |
| System Overview             | ✓    | Orients the reader before details begin.         | Copy-paste of the README architecture.     |
| Functional Requirements     | ✓    | The testable promise — one stable ID each.       | IDs missing edge cases or error handling.  |
| API Contract                | ✓    | What integrators build against.                  | Prose where a signature belongs.           |
| Integration Points          | ✓    | Names every outside system that can fail you.    | "Uses the database" with no contract.      |
| Non-functional Requirements | ✓    | Feature-level numbers the PRD deliberately omits.| Restating PRD bullets verbatim.            |
| Test Scenarios              | ✓    | Promises the backlog must evidence.              | Scenarios with no evidence row.            |
| Assumptions & Constraints   | ✓    | Implicit requirements made explicit.             | Empty section on a feature with real ones. |
| Glossary                    | opt  | One meaning per term; rows and code agree.       | A term defined differently in two features.|

---

## The Spec ↔ Backlog Contract

| In `FRD.md`                          | In `BACKLOG.md`                                                     |
|--------------------------------------|---------------------------------------------------------------------|
| `FR-006: <requirement>`              | A row whose `FRD Ref` is `FR-006` (`orphan-fr-ref` if absent).     |
| Bullet under `## Test Scenarios`     | `Scenario evidence` row: Automated / Proxy / Manual / Gap + test + commit. |
| Anything about current behaviour     | Nothing — the claim moves out of the spec.                          |

> A scenario marked **Gap** is an honest record, not a defect.
> A scenario **absent** from the evidence table is a defect: nobody will ever say whether it was tested.

---

## Verify

```bash
aa docs check . --strict
# Checks: IDs, orphan refs, scenario coverage, status leak, sections, links.
```

The checker catches structure. Two things it cannot see — check by hand:

1. **Cold-read test.** Read `FR-001`'s six bullets as if you never saw the codebase.
   Could you implement it without asking anyone? If not, the requirement is incomplete.

2. **Label test.** In the API Contract, does every row say *as implemented* or *as intended*
   where they differ?

**Done** when an engineer who never met the author can build the feature from this file,
and every test scenario has a named evidence row in the backlog.
```

