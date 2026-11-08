# AES Agent HOW-TO (Rust)

> **Purpose**: Orchestrate only: receive a request, call the aggregate contract, return shared VOs — no I/O, no computation.
>
> **Audience**: Agents and engineers scaffolding AES agent orchestrators.
>
> **Scope**: Rust `agent_<domain>_orchestrator` files — one aggregate, 3-block structure, zero I/O.
>
> **Location**: Feature domain package; depends only on shared contracts/taxonomy/utility.
>
> **Length**: One `_orchestrator` file per feature; ≥1 aggregate, ≤3 types.

---

## Rules

### Import rules

| Rule                           | Value                                                                                             |
| ------------------------------ | ------------------------------------------------------------------------------------------------- |
| **Allowed imports**            | `shared::*` — taxonomy VOs, constants, aggregate traits, protocol traits                          |
| **Mandatory imports (AES202)** | At least one taxonomy import and the aggregate trait (Import Matrix row 9)                        |
| **Forbidden imports**          | `capabilities_*`, `agent_*`, `surface_*`                                                          |

### 3-Block Structure

```text
// Block 1: Module Declaration
// Block 2: Module Contract
// Block 3: Module Helpers
```

Method placement:

```text
Free function (outside impl)?               → EXTRACT to *_utility.rs
In aggregate trait?                         → Block 2
std trait impl (Default/Clone/Display)?     → Block 3
fn new() / constructor?                     → Block 3
Private helper (uses &self)?                → Block 3
Pure fn, no struct dep?                     → EXTRACT to *_utility.rs
```

### Helper vs Utility

Keep in Block 3 if ANY: uses `&self`, coupled to this struct, constructor, agent-specific logic, single-use.
Extract to utility only if ALL: no `self`/`Self`, pure, no side effects, domain-agnostic, reusable.
I/O: stateless + I/O + domain-agnostic = taxonomy utility. Stateless + I/O + domain-specific = capabilities.

### Allowed / forbidden

| Rule          | Value                                                                                                                                                                                                                                                                                          |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Allowed**   | `for`/`while`/`loop`, `if/else`/`match`, `?`/`match Err`, `tokio::join!`/`.await`, collecting results into shared VOs; computation allowed: iteration to call deps, routing results, propagating errors |
| **Forbidden** | `std::fs`, `File::open`, `reqwest`, `hyper`, `sqlx`, `rusqlite`, stdout/stderr write, env mutation, global state mutation; computation forbidden: arithmetic, totals, averages, `.sum()`/`.fold()`, parsing, normalization |

**Error and VO rules:**

- Rule 1: Never silently discard — no `checker.check().unwrap_or_default()`.
- Rule 2: Analysis orchestration → return the taxonomy-defined response enum variant; each variant holds VO-wrapped values, not raw primitives.
- Rule 3: Execution orchestration → return `Result<ExecutionReport, AgentExecutionError>` wrapped in a VO variant carrying `ExecutionReport` / `AgentExecutionError` VOs.
- Rule 4: Delegate I/O errors to capabilities — agent only wraps into VO.
- Rule 5: `String`/`i32`..`u64`/`f32`/`f64`/`char` forbidden for domain fields/contracts. `bool` for toggles; `&str` for borrowed non-domain input only.

## Template

```rust
use std::sync::Arc;

use shared::<domain>::taxonomy_<name>_vo::<VO>;
use shared::<domain>::contract_<name>_aggregate::I<Name>Aggregate;
use shared::<domain>::contract_<name>_protocol::I<SeamA>Protocol;
use shared::<domain>::contract_<name>_protocol::I<SeamB>Protocol;

// ─── Block 1: Module Declaration ──────────────────────────
// Injected deps are protocol traits (what the agent dispatches to), not the aggregate.
// Inject ≥2 subsystems (AES405-11: fewer than 2 injected protocol subsystems is a finding).
pub struct Agent<Name> {
    primary: Arc<dyn I<SeamA>Protocol>,
    secondary: Arc<dyn I<SeamB>Protocol>,
}

impl Agent<Name> {
    pub fn new(primary: Arc<dyn I<SeamA>Protocol>, secondary: Arc<dyn I<SeamB>Protocol>) -> Self {
        Self { primary, secondary }
    }
}

// ─── Block 2: Module Contract ─────────────
// Exactly one method — the single entry point. Dispatch to the owning protocol trait.
impl I<Name>Aggregate for Agent<Name> {
    fn execute(&self, request: <RequestVO>) -> <ResponseVO> {
        // Orchestration only: match the request variant, delegate to the protocol.
        // No computation, no I/O, no silently discarded errors.
        match request {
            <RequestVO>::<Variant1> { .. } => <ResponseVO>::<Result1>(self.primary.<operation_1>(..)),
            <RequestVO>::<Variant2> { .. } => <ResponseVO>::<Result2>(self.secondary.<operation_2>(..)),
        }
    }
}

// ─── Block 3: Module Helpers ─────────
impl Agent<Name> {
    pub fn to_string(&self) -> String {
        format!("Agent<Name>()")
    }
}

impl Default for Agent<Name> {
    fn default() -> Self {
        Self {
            primary: Arc::new(PlaceholderProtocol),
            secondary: Arc::new(PlaceholderProtocol),
        }
    }
}
```

---

## Section Contract

| Check                                                         | Why it belongs here                                                 |
| ------------------------------------------------------------- | ------------------------------------------------------------------- |
| Block 1 → 2 → 3 order followed.                               | Required by AES layer rules and the linter; missing it is a defect. |
| Block 1 holds the type, the constructor family and static factories (R2). | Required by AES layer rules and the linter; missing it is a defect. |
| Block 2: Module Contract — aggregate trait implementation only. | Required by AES layer rules and the linter; missing it is a defect. |
| Block 3: Module Helpers — constructors, std traits, private helpers; factories are not here (R2). | Required by AES layer rules and the linter; missing it is a defect. |
| ≥1 struct implements aggregate trait; the struct implements no protocol (AES405-3); ≤3 total types. | Required by AES layer rules and the linter; missing it is a defect. |
| ≥2 injected protocol subsystems; `Arc<dyn Trait>` for DI; shared VOs; no local domain data. | Required by AES layer rules and the linter; missing it is a defect. |
| Zero I/O, zero business logic, zero domain computation.       | Required by AES layer rules and the linter; missing it is a defect. |
| No forbidden imports; mandatory imports present.              | Required by AES layer rules and the linter; missing it is a defect. |
| Generic aggregate methods object-safe or `where Self: Sized`. | Required by AES layer rules and the linter; missing it is a defect. |
| Aggregate registered in shared crate `mod.rs`.                | Required by AES layer rules and the linter; missing it is a defect. |
| `cargo check -p <crate-name>` passes.                         | Required by AES layer rules and the linter; missing it is a defect. |

---

## Workflow

1. **Triage (diagnostic tree)** — ask in order; the first "No" dictates the next action: orchestration only (no I/O, no computation, no local domain data)? an `_aggregate` contract exists? — no: create it first with `aes-contract`. Block 2 holds only aggregate methods; ≥1 aggregate; ≤3 types? no silently discarded errors; no raw primitives in signatures (wrap in VOs; propagate errors)? `lint-arwaky-cli scan <layer-path>` exits 0?
2. Confirm orchestration only — computation → capabilities, domain data → taxonomy, pure helpers → utility.
3. Ensure an `_aggregate` contract exists — if missing, run `aes-contract` first.
4. Resolve the feature agent dir. Run `lint-arwaky-cli scan <layer-path>` — findings are the work list.
5. Implement the 3 blocks from § Template / § Section Contract; the struct implements the aggregate trait via DI.
6. Check imports, I/O, computation, error handling, and primitives against § Rules.
7. Register in `mod.rs`, then compose via `aes-root` / consume via `aes-surface`.
8. **Placement (AES702/AES703)** — the file sits in a feature folder (`crates/<feature_name>/src/agent_<domain>_orchestrator`), not in `shared/` or a surface-dominated folder; `FRD.md` + `BACKLOG.md` at the feature folder root beside the source; a capabilities-only folder without its own agent is a split feature.
9. Fallback compile gate: `cargo check -p <crate-name>`.

## Review

- Block 1 → 2 → 3 order; Block 2 holds only aggregate methods; helper-vs-utility split respected (free functions extracted to `*_utility.rs`) — § Rules § 3-Block Structure, § Helper vs Utility.
- Orchestration only: zero I/O, zero computation, zero domain data; DI via protocol traits; shared VOs in signatures — § Rules § Allowed / forbidden operations, § Computation, Errors, VOs.
- No silently discarded errors (`unwrap_or_default()` on results); errors propagate or wrap into VOs — § Rules Error rules.
- No agent file in `shared/`; capabilities-only folders carry an agent of their own — § Workflow step 8.
- `contract_<name>_aggregate.rs` exists; ≥1 aggregate, no implemented protocol (AES405-3), ≤3 types.

## Verify

```bash
lint-arwaky-cli scan --layer agent
# Checks: AES101/AES102 (filename + suffix), AES201–AES205 (layer imports,
# Import Matrix row 9), AES303 (mandatory definition), AES304 (bypass patterns),
# AES405 sub-checks 1–11 (routing, block order, protocol-forbidden, block markers, I/O,
# constants, computation, abstract methods, stateless, free fns, subsystem count),
# AES505 (container wiring), AES702/AES703 (placement).
# AES6xx doc invariants (e.g. FRD protocol parity, AES609) are checked at the
# feature-folder document pass.
# Language compile is a fallback gate only: `cargo check -p <crate-name>`
```
