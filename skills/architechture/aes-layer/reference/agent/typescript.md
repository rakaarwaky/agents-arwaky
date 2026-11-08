# AES Agent HOW-TO (Typescript)

> **Purpose**: Orchestrate only: implement the aggregate contract, dispatch to the injected protocol subsystems, return shared VOs — no I/O, no computation.
>
> **Audience**: Agents and engineers scaffolding AES agent orchestrators.
>
> **Scope**: TypeScript `agent_<domain>_orchestrator` files — one aggregate, 3-block structure, zero I/O.
>
> **Location**: Feature domain package; depends only on shared contracts/taxonomy/utility.
>
> **Length**: One `_orchestrator` file per feature; ≥1 aggregate, ≤3 types.

---

## Rules

### Import rules


| Rule                           | Value                                                                                     |
| ------------------------------ | ----------------------------------------------------------------------------------------- |
| **Allowed imports**            | `shared/*` — taxonomy VOs and constants, aggregate + protocol interfaces, and `*_utility` |
| **Mandatory imports (AES202)** | At least one taxonomy import and the aggregate interface                                  |
| **Forbidden imports**          | `capabilities_*`, `agent_*`, `surface_*`, `root_*`                                        |


### 3-Block Structure

- Banner labels are exact and in order 1 → 2 → 3; the length of the `───` run is cosmetic.

```text
// ─── Block 1: Module Declaration ───
// ─── Block 2: Module Contract ───
// ─── Block 3: Module Helpers ───
```

```text
Constructor / static factory returning the class?  → Block 1 (R2 — one home for constructors)
Module-level function?                             → EXTRACT to *_utility.ts
Defined in aggregate interface?                    → Block 2
toString / toJSON / valueOf / equals?              → Block 3
private helper (uses this)?                        → Block 3
Pure static, no class dep, not a factory?          → EXTRACT to *_utility.ts
```

### Helper vs Utility

- Keep in Block 3 if ANY: uses `this`, coupled to this class, agent-specific logic, single-use.

- Extract to utility only if ALL: no `this`, pure, no side effects, domain-agnostic, reusable.

### Allowed / forbidden


| Rule          | Value                                                                                                                                                                                                                                                                                          |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Allowed**   | `for`/`while`/`for...of`, `if/else`/`switch`, `try/catch`/`throw` (taxonomy error types only — `throw new Error(...)` is an AES304 PANIC pattern), `Promise.all`/`await`, collecting results into shared VOs; computation allowed: iteration to call deps, routing results, propagating errors |
| **Forbidden** | `fs.*`, `readFile`, `writeFile`, `fetch`, `axios`, `http`, database ops, stdout/stderr write, env mutation, global state mutation; computation forbidden: arithmetic, totals, averages, `.reduce`/`.fold`, parsing, normalization                                                              |


**Error and VO rules:**

- Rule 1: Never silently discard — no `checker.check() ?? ""`.
- Rule 2: Analysis orchestration → return the taxonomy-defined response enum variant; each variant
holds VO-wrapped values, not raw primitives.
- Rule 3: Execution orchestration → return the taxonomy-defined execution-response variant
carrying `ExecutionReport` / `AgentExecutionError` VOs.
- Rule 4: Delegate I/O errors to capabilities — agent only wraps into VO.
- Rule 5: `string`/`number` forbidden for domain fields/contracts. `boolean` for toggles only.
`any`/`Any` annotations forbidden (AES405-1).

## Template

```typescript
import { <VO> } from '../shared/<domain>/taxonomy_<name>_vo';
import { I<Name>Aggregate } from '../shared/<domain>/contract_<name>_aggregate';
import { I<SeamA>Protocol } from '../shared/<domain>/contract_<seam_a>_protocol';
import { I<SeamB>Protocol } from '../shared/<domain>/contract_<seam_b>_protocol';

// ─── Block 1: Module Declaration ───
export class Agent<Name>Orchestrator implements I<Name>Aggregate {
    // Injected deps are protocol interfaces (what the agent dispatches to), never
    // the aggregate and never a concrete capability. Inject ≥2 subsystems
    // (AES405-11: fewer than 2 injected protocol subsystems is a finding).
    constructor(
        private readonly primary: I<SeamA>Protocol,
        private readonly secondary: I<SeamB>Protocol,
    ) {}

    static create(): Agent<Name>Orchestrator {
        return new Agent<Name>Orchestrator(/* inject deps */);
    }

// ─── Block 2: Module Contract ───
    // Only aggregate-interface methods — the single `execute` entry point in the
    // minimal case; add methods only if the aggregate interface defines them.
    async execute(request: <RequestVO>): Promise<<ResponseVO>> {
        // Orchestration only: match the request variant, delegate to the owning
        // protocol. No computation, no I/O, no silently discarded errors —
        // errors wrap into the <ResponseVO> variant (Rules 1–4).
        if (request instanceof <RequestVO>.<Variant1>) {
            return new <ResponseVO>.<Result1>(await this.primary.<operation_1>(...));
        }
        return new <ResponseVO>.<Result2>(await this.secondary.<operation_2>(...));
    }

// ─── Block 3: Module Helpers ───
    toString(): string {
        return 'Agent<Name>Orchestrator()';
    }
}
```

---

## Section Contract


| Check                                                                                                      | Why it belongs here                                                 |
| ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| Block 1 → 2 → 3 order followed.                                                                            | Required by AES layer rules and the linter; missing it is a defect. |
| Block 1 holds the type, the constructor family and static factories (R2).                                  | Required by AES layer rules and the linter; missing it is a defect. |
| Block 2: Module Contract — aggregate interface method implementations only.                                | Required by AES layer rules and the linter; missing it is a defect. |
| Block 3: Module Helpers — toString/toJSON/valueOf/equals and private helpers; factories are not here (R2). | Required by AES layer rules and the linter; missing it is a defect. |
| ≥1 class implements the aggregate interface; the class implements no protocol (AES405-3); ≤3 total types.  | Required by AES layer rules and the linter; missing it is a defect. |
| ≥2 injected protocol subsystems; DI via protocol interfaces; shared VOs; no local domain data.             | Required by AES layer rules and the linter; missing it is a defect. |
| Zero I/O, zero business logic, zero domain computation.                                                    | Required by AES layer rules and the linter; missing it is a defect. |
| No forbidden imports; mandatory imports present.                                                           | Required by AES layer rules and the linter; missing it is a defect. |
| Aggregate registered in the feature `index.ts` and wired in the `root_*` container (AES505).               | Required by AES layer rules and the linter; missing it is a defect. |
| `npx tsc --noEmit` passes.                                                                                 | Required by AES layer rules and the linter; missing it is a defect. |


---

## Workflow

1. **Triage (diagnostic tree)** — check in order; the first "No" dictates the next action:
   - Orchestration only — no I/O, no computation, no local domain data?
   - An `_aggregate` contract exists? — no: create it first with `aes-contract`.
   - Block 2 holds only aggregate methods; ≥1 aggregate implementor; ≤3 types?
   - ≥2 injected protocol subsystems; no silently discarded errors; no raw primitives in signatures (wrap in VOs; propagate errors)?
   - `lint-arwaky-cli scan --layer agent` exits 0?
2. Verify orchestration only — computation → capabilities, domain data → taxonomy, pure helpers → utility.
3. Ensure an `_aggregate` contract exists — if missing, run `aes-contract` first.
4. Resolve the feature agent dir. Run `lint-arwaky-cli scan --layer agent` findings are the work list.
5. Implement the 3 blocks from § Template / § Section Contract; the class implements the aggregate interface and dispatches to the injected protocol subsystems via DI.
6. Check imports, I/O, computation, error handling, and primitives against § Rules.
7. Register the aggregate in the feature `index.ts`, wire the orchestrator in the `root_*` container (AES505), then compose via `aes-root` / consume via `aes-surface`.
8. **Placement (AES702/AES703)** — the file sits in a feature folder (`packages/<feature_name>/src/agent_<domain>_orchestrator`), not in `shared/` or a surface-dominated folder; `FRD.md` + `BACKLOG.md` at the feature folder root beside the source, with `FR-<NAME>-NNN` ids in protocol parity (`I*Protocol` count = FR count, `I*Aggregate` excluded; on mismatch fix the stale side — docs follow code — AES609); a capabilities-only folder without its own agent is a split feature (AES702 `feature_missing_agent`).
9. Fallback compile gate: `npx tsc --noEmit`.

## Review

- Block 1 → 2 → 3 order; Block 1 holds the constructor family including static factories; Block 2 holds only aggregate methods; helper-vs-utility split respected (free functions extracted to `*_utility.ts`) — § Rules → 3-Block Structure, § Rules → Helper vs Utility.
- Orchestration only: zero I/O, zero computation, zero domain data; DI via protocol interfaces (≥2 subsystems); shared VOs in signatures — § Rules → Allowed / forbidden, § Rules → Error and VO rules.
- No silently discarded errors (`?? ""` / empty-string fallbacks on results); errors propagate or wrap into VOs — § Rules → Error and VO rules.
- No agent file in `shared/`; capabilities-only folders carry an agent of their own — § Workflow step 8.
- `contract_<name>_aggregate.ts` exists; ≥1 aggregate implementor, no implemented protocol (AES405-3), ≤3 types.

## Verify

```bash
lint-arwaky-cli scan --layer agent
# Checks: AES101/AES102 (filename + `orchestrator` suffix), AES201–AES205 (layer imports,
# Import Matrix row 9), AES303 (mandatory definition), AES304 (bypass patterns),
# AES405 sub-checks 1–11 (routing, block order, protocol-forbidden, block markers, I/O,
# constants, computation, abstract methods, stateless, free fns, subsystem count),
# AES505 (container wiring), AES702/AES703 (placement).
# AES6xx doc invariants (e.g. FRD protocol parity, AES609) are checked at the
# feature-folder document pass.
# Language compile is a fallback gate only: `npx tsc --noEmit`
```