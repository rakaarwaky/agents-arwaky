# HOW TO MAKE FRD.md

> **Purpose**: Tell an engineer exactly what to build and tell QA exactly what
> to test — without a single follow-up question to the author.
>
> **Audience**: Engineers, QA, Tech Lead.
>
> **Scope**: One FRD per feature folder
>
> **Location**: Inside the feature's directory
>
> **Length**: 50–500 lines

---

## Rules

Eight rules. Each one prevents a specific failure mode.

1. **Requirement IDs are the contract.** `FR-<name>-<number>`,
  unique within the feature and stable forever.
 
2. **A requirement is testable, or it is a wish.**
 State input, output, business rules, edge cases, error handling.
3. **The API contract is exact.** method, inputs, outputs, errors, events. 
4. **Scenarios are stated here; evidence lives in the backlog.**One scenario per bullet , so `scenario-evidence-count`can match them
5. **Non-functional numbers live here.**
 The PRD says "fast." This file says *what* the feature guarantees and
 *how* you measure it.
6. **Assumptions and constraints are written down.**
 Every implicit assumption is a requirement someone discovers later and
 calls a bug.
7. **Cross-link the pair** in `## Reference`.A reader landing on either file must immediately see promise and claim.
8. **No description of current behaviour.** A paragraph about what the source does today is a second copy of the code and always staler.

---

## Template

Copy, fill, delete nothing.

```markdown
# FRD — <feature-name>

## Reference

- PRD: <link to root PRD.md>
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature;
  this file is specification only.

## System Overview

<One diagram or ≤ 3 sentences: where this feature sits, what calls it, what it calls.>

## Functional Requirements

### FR-<FEATURENAME>-001: <Short imperative name>

- **Description**: <what it does — one sentence>
- **Input**: <shape, source>
- **Output**: <shape, destination>
- **Business Rules**: <validation logic, constraints>
- **Edge Cases**: <boundary conditions and their handling>
- **Error Handling**: <what fails, what the caller sees>

### FR-<FEATURENAME>-XXX: <Short imperative name>
### FR-<FEATURENAME>-XXX: <Short imperative name>
### FR-<FEATURENAME>-XXX: <Short imperative name>
### FR-<FEATURENAME>-XXX: <Short imperative name>
- …

## API Contract

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| …      | …     | …      | …     | …     | …           |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| <name> | in / out  | …       | …            |

## Non-functional Requirements

| Metric       | Target      | Measurement method        |
|--------------|-------------|---------------------------|
| Response time| < p95 ms    | <tool, endpoint, dataset> |
| Availability | < %         | <window, source>          |
| Security     | <standard>  | <audit / scan reference>  |

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

Every section is required unless marked optional. Each exists for one
reason.


| Section                       | Why it belongs here                               |
| ----------------------------- | ------------------------------------------------- |
| Reference                     | Separates spec promise from backlog claim.        |
| System Overview               | Orients the reader before details begin.          |
| Functional Requirements       | The testable promise                              |
| API Contract                  | What integrators build against.                   |
| Integration Points            | Names every outside system that can fail you.     |
| Non-functional Requirements   | Feature-level numbers the PRD deliberately omits. |
| Test Scenarios                | Promises the backlog must evidence.               |
| Assumptions &amp; Constraints | Implicit requirements made explicit.              |
| Glossary                      | One meaning per term; rows and code agree.        |


---

## Verify

```bash
aa docs check . --strict
# Checks: IDs, orphan refs, scenario coverage, status leak, sections, links.
```

