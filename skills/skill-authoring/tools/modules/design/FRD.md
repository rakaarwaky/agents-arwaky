# FRD — design

## Feature Overview

The design feature sits in the agent layer and is called by the surface and root CLI through the design aggregate contract. It orchestrates four capabilities — creator, adopter, linter, runner — plus an optional catalog, and routes each of the six design ops (`CREATE`, `ADOPT`, `LINT`, `RUN`, `PAUSE`, `RESUME`) to the matching capability. The agent performs no filesystem I/O; all I/O is delegated to the capabilities.

## Functional Requirements

### FR-DESIGN-001: Orchestrate design-side skill operations

**Description:** `SkillsDesignAgent.execute(request)` shall route each design op (`CREATE`, `ADOPT`, `LINT`, `RUN`, `PAUSE`, `RESUME`) to the matching capability and return a typed `SkillsResult` to the caller. The agent coordinates the capability protocols and shared kernel utilities; it performs no filesystem I/O itself.

#### Business Logic

- The agent shall delegate all filesystem I/O to the capabilities it coordinates; the agent itself holds no filesystem state.
- If a required capability was not injected at construction, the agent shall raise a root-level error at call time, not at construction.
- An op string that is not one of the six design ops shall produce a `SkillsResult` with `USAGE_ERROR` exit code and a message naming the unknown op.
- A `SkillsError` raised by a capability shall be caught by the agent and mapped to a `SkillsResult` carrying the error's exit code and message.
- On `CREATE`, the agent shall require a `--category` flag; a missing category shall produce a `USAGE_ERROR` result.
- On `CREATE` with `apply=False`, the agent shall return a plan without invoking the catalog.
- On `CREATE` with `apply=True` and a new skill or category, the agent shall rebuild the catalog and include the result in the `SkillsResult`.

#### Edge Cases

- A missing required capability shall raise a root-level error at call time, not at agent construction.
- An empty or absent skill name on `CREATE` or `ADOPT` shall produce a `SkillsResult` with `ISSUES_FOUND` exit code and the message "Skill name required".
- An unknown op string shall produce a `SkillsResult` with `USAGE_ERROR` exit code and a message naming the unknown op.
- A `SkillsError` raised by any capability shall be caught and mapped to a `SkillsResult` with the error's exit code and message.
- On `RUN`, `PAUSE`, or `RESUME`, an `OSError` from the runner shall be caught and returned as a `SkillsResult` with `ISSUES_FOUND` exit code.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | `SkillsRequest` (op, query, flags, apply, root). Source: surface / root CLI. |
| **Output** | `SkillsResult` (ok, op, exit_code, message, op-specific payload fields). Destination: surface / root CLI. |
| **Protocol** | `ISkillsDesignAggregate` |
| **Method** | `execute` |
| **Event** | None |
| **Error** | `CLEAN` 0, `ISSUES_FOUND` 1, `USAGE_ERROR` 2 |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| A `LINT` request that finds no issues | The surface invokes `execute` with `op=LINT` | `SkillsResult` with `ok=True`, `lint_report` populated, exit code `CLEAN` |
| A `LINT` request that finds issues | The surface invokes `execute` with `op=LINT` | `SkillsResult` with `ok=False`, `lint_report` populated, exit code `ISSUES_FOUND` |
| An unknown op string | The surface invokes `execute` with an op string outside the design set | `SkillsResult` with `ok=False`, exit code `USAGE_ERROR`, message naming the unknown op |
| A valid `CREATE` request without `apply` | The surface invokes `execute` with `op=CREATE` | `SkillsResult` with `ok=True`, `create_plan` populated, `catalog` is `None` |
| A valid `CREATE` request with `apply=True` | The surface invokes `execute` with `op=CREATE` and `apply=True` | `SkillsResult` with `ok=True`, `create_plan` populated, `catalog` populated |
| A `CREATE` request missing the category | The surface invokes `execute` with `op=CREATE` and no category in flags | `SkillsResult` with `ok=False`, exit code `USAGE_ERROR`, message naming the missing flag |
| A valid `RUN` request | The surface invokes `execute` with `op=RUN` | `SkillsResult` with `ok=True`, `records` populated |
| A valid `PAUSE` request | The surface invokes `execute` with `op=PAUSE` | `SkillsResult` with `ok=True`, message "lifecycle paused" |
| A valid `RESUME` request | The surface invokes `execute` with `op=RESUME` | `SkillsResult` with `ok=True`, message "lifecycle resumed" |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Dispatch p95 latency | 5 ms |
| Unknown-op rejection rate | 100 % |
| Unhandled exception escape rate | 0 % |

### FR-DESIGN-002: Capability contract implementation

**Description:** Each of the four capability modules shall implement its corresponding protocol. No capability shall import a sibling capability; cross-capability data shall flow through shared kernel protocols or shared kernel utilities.

#### Business Logic

- The creator capability shall implement the creator protocol: `create_skill` and `create_category`.
- The adopter capability shall implement the adopter protocol: `adopt`.
- The linter capability shall implement the linter protocol: `lint`.
- The runner capability shall implement the runner protocol: `apply_automatic_transitions`, `pause`, `resume`.
- No capability module shall import another capability module directly; data crossing capability boundaries shall go through shared kernel protocols or shared kernel utilities.
- Every computed filesystem destination written by the creator capability shall be asserted to remain inside the skills root at plan time and re-checked at apply time, so a symlink created between the two phases fails closed.

#### Edge Cases

- A capability module that imports a sibling capability module shall be flagged by the architecture scanner.
- A creator plan that computes a destination outside the skills root at apply time shall fail closed and produce no write.
- A missing skill name on `adopt` shall raise an error that the agent maps to a `SkillsResult` with `ISSUES_FOUND`.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | Capability-specific arguments as defined by each protocol. Source: agent. |
| **Output** | Capability-specific results as defined by each protocol. Destination: agent. |
| **Protocol** | Creator protocol, Adopter protocol, Linter protocol, Runner protocol |
| **Method** | `create_skill`, `create_category`, `adopt`, `lint`, `apply_automatic_transitions`, `pause`, `resume` |
| **Event** | None |
| **Error** | `OSError`, `SkillsError` subclasses; agent maps them to `SkillsResult` exit codes |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| A creator capability is constructed and `create_skill` is called with `apply=False` | Creator plan is returned | `SkillCreatePlan` with `apply=False`; no filesystem write occurs |
| A linter capability is called with a valid root | `lint` returns a `LintReport` | `LintReport` with `issues`, `weed_lines`, `skills`, `categories` populated |
| A runner capability is called when lifecycle is paused | `apply_automatic_transitions` is called | Result dict with `paused=True` and empty `applied` list |
| The architecture scanner scans the design module for sibling capability imports | Scan completes | No sibling capability imports are reported |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Sibling-capability import count | 0 |
| Out-of-root write occurrence rate | 0 % |
| Capability contract test pass rate | 100 % |

### FR-DESIGN-003: Design aggregate contract

**Description:** The design aggregate contract shall define a single `execute(SkillsRequest) → SkillsResult` entry point that the agent implements. The root composition root shall wire the agent into the composed facade so that the surface and CLI can call the design ops through one stable interface.

#### Business Logic

- The aggregate contract shall be an abstract base class with one abstract method: `execute`.
- The agent shall implement the aggregate contract; the root composition root shall instantiate the agent and register it in the composed facade.
- The aggregate contract shall live in the shared design contract module, not in the feature's source tree.
- The surface and root CLI shall call design ops exclusively through the aggregate contract; no direct capability calls from outside the agent.

#### Edge Cases

- A composition root that wires the agent without the runner capability shall raise a root-level error at the point `RUN`, `PAUSE`, or `RESUME` is first called, not at construction.
- A surface that calls a design op through the aggregate contract with an invalid op string shall receive a `SkillsResult` with `USAGE_ERROR`.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | `SkillsRequest`. Source: surface / root CLI. |
| **Output** | `SkillsResult`. Destination: surface / root CLI. |
| **Protocol** | `ISkillsDesignAggregate` |
| **Method** | `execute` |
| **Event** | None |
| **Error** | `USAGE_ERROR` 2, `ISSUES_FOUND` 1 |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| The agent is constructed and registered in the root composition root | The surface calls a design op through the facade | The agent's `execute` is invoked; a `SkillsResult` is returned |
| The agent is constructed without the runner capability and `RUN` is called | `execute(SkillsRequest(op=RUN))` | A root-level error is raised naming the missing capability |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Direct capability call rate from outside the agent | 0 % |
| Aggregate contract test pass rate | 100 % |

## Public Interface

| Aspect     | Detail                         |
|------------|--------------------------------|
| Agent      | `SkillsDesignAgent`            |
| Aggregate  | `ISkillsDesignAggregate`       |
| Method     | `execute`                      |
| Request    | `SkillsRequest` (op, query, flags, apply, root) |
| Response   | `SkillsResult` (ok, op, exit_code, message, op-specific fields) |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | Business goals and scope                   | [PRD.md](../../../../../PRD.md) |
| Backlog      | Task tracking and implementation status    | [BACKLOG.md](BACKLOG.md) |
| Roadmap      | Timeline, phasing, and dependencies        | [ROADMAP.md](../../../../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |
