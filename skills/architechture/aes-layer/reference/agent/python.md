# AES Agent HOW-TO (Python)

> **Purpose**: Orchestrate only: receive a request, call the aggregate contract, return shared VOs — no I/O, no computation.
>
> **Audience**: Agents and engineers scaffolding AES agent orchestrators.
>
> **Scope**: Python `agent_<domain>_orchestrator` files — one aggregate, 3-block structure, zero I/O.
>
> **Location**: Feature domain package; depends only on shared contracts/taxonomy/utility.
>
> **Length**: One `_orchestrator` file per feature; ≥1 aggregate, ≤3 types.

---

## Rules

### Import rules

| Rule                           | Value                                                                                             |
| ------------------------------ | ------------------------------------------------------------------------------------------------- |
| **Allowed imports**            | `shared/*` — taxonomy VOs and constants, aggregate + protocol ABCs, and `*_utility` helpers       |
| **Mandatory imports (AES202)** | At least one taxonomy import and the aggregate ABC (Import Matrix row 9)                          |
| **Forbidden imports**          | `capabilities_*`, `agent_*`, `surface_*`                                                          |

### 3-Block Structure

```text
# Block 1: Module Declaration
# Block 2: Module Contract
# Block 3: Module Helpers
```

Method placement:

```text
Module-level def?                    → EXTRACT to *_utility.py
@abstractmethod in aggregate ABC?    → Block 2
Dunder / factory @classmethod?       → Block 3
@staticmethod pure + no class dep?   → EXTRACT to *_utility.py
Private helper (uses self)?          → Block 3
```

### Helper vs Utility

- Keep in Block 3 if ANY: uses `self`, coupled to this class, factory, agent-specific logic, single-use.
- Extract to utility only if ALL: no `self`/`cls`, pure, no side effects, domain-agnostic, reusable.
- I/O: stateless + I/O + domain-agnostic = taxonomy utility. Stateless + I/O + domain-specific = capabilities.

### Allowed / forbidden

| Rule          | Value                                                                                                                                                                                                                                                                                          |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Allowed**   | `for`/`while`/`async for`, `if/else`/`match`, `try/except`/`raise`, `asyncio.wait_for`, collecting results into shared VOs; computation allowed: iteration to call deps, routing results, propagating errors |
| **Forbidden** | `open()`, `Path()`, `os.*`, `requests.*`, `httpx.*`, `sqlite3.*`, `asyncpg.*`, stdout/stderr write, env mutation, global state mutation; computation forbidden: arithmetic, totals, averages, `.reduce`/`.fold`, parsing, normalization |

**Error and VO rules:**

- Rule 1: Never silently discard — no `checker.check() or ""`.
- Rule 2: Analysis orchestration → return the taxonomy-defined response enum variant; each variant holds VO-wrapped values, not raw primitives.
- Rule 3: Execution orchestration → return `Result[...]` wrapped in a VO variant carrying `ExecutionReport` / `AgentExecutionError` VOs.
- Rule 4: Delegate I/O errors to capabilities — agent only wraps into VO.
- Rule 5: `str`/`int`/`float` forbidden for domain fields/contracts. `bool` for semantic toggles only.

## Template

```python
from shared.<domain>.taxonomy_<name>_vo import <VO>
from shared.<domain>.contract_<name>_aggregate import I<Name>Aggregate
from shared.<domain>.contract_<name>_protocol import I<SeamA>Protocol
from shared.<domain>.contract_<name>_protocol import I<SeamB>Protocol

# ─── Block 1: Module Declaration ──────────────
class Agent<Name>:
    # Injected deps are protocol ABCs (what the agent dispatches to), not the aggregate.
    # Inject ≥2 subsystems (AES405-11: fewer than 2 injected protocol subsystems is a finding).
    def __init__(
        self,
        primary: I<SeamA>Protocol,
        secondary: I<SeamB>Protocol,
    ) -> None:
        self._primary = primary
        self._secondary = secondary

    @classmethod
    def create(cls) -> "Agent<Name>":
        return cls(/* inject deps */)

    # ─── Block 2: Module Contract ─────────
    # Only aggregate-ABC method implementations — the single `execute` entry point in the
    # minimal case; add methods only if the aggregate ABC defines them.
    def execute(self, request: <RequestVO>) -> <ResponseVO>:
        # Orchestration only: match the request variant, delegate to the owning protocol.
        # No computation, no I/O, no silently discarded errors — errors wrap into the
        # <ResponseVO> variant (Rules 1–4).
        if isinstance(request, <RequestVO>.<Variant1>):
            return <ResponseVO>.<Result1>(self._primary.<operation_1>(..))
        return <ResponseVO>.<Result2>(self._secondary.<operation_2>(..))

    # ─── Block 3: Module Helpers ─────
    def __repr__(self) -> str:
        return "Agent<Name>()"
```

---

## Section Contract

| Check                                                         | Why it belongs here                                                 |
| ------------------------------------------------------------- | ------------------------------------------------------------------- |
| Block 1 → 2 → 3 order followed.                               | Required by AES layer rules and the linter; missing it is a defect. |
| Block 1 holds the type, the constructor family and static factories (R2). | Required by AES layer rules and the linter; missing it is a defect. |
| Block 2: Module Contract — aggregate ABC method implementations only. | Required by AES layer rules and the linter; missing it is a defect. |
| Block 3: Module Helpers — dunders, factories, private helpers; factories are not here (R2). | Required by AES layer rules and the linter; missing it is a defect. |
| ≥1 class inherits aggregate ABC; the class implements no protocol (AES405-3); ≤3 total classes. | Required by AES layer rules and the linter; missing it is a defect. |
| ≥2 injected protocol subsystems; DI via protocol ABCs; shared VOs; no local domain data. | Required by AES layer rules and the linter; missing it is a defect. |
| Zero I/O, zero business logic, zero domain computation.       | Required by AES layer rules and the linter; missing it is a defect. |
| No forbidden imports; mandatory imports present.              | Required by AES layer rules and the linter; missing it is a defect. |
| Aggregate registered in shared `__init__.py`.                 | Required by AES layer rules and the linter; missing it is a defect. |
| `python -c "import <module>"` passes.                         | Required by AES layer rules and the linter; missing it is a defect. |

---

## Workflow

1. **Triage (diagnostic tree)** — check in order; the first "No" dictates the next action:
   - Orchestration only — no I/O, no computation, no local domain data?
   - An `_aggregate` contract exists? — no: create it first with `aes-contract`.
   - Block 2 holds only aggregate methods; ≥1 aggregate; ≤3 types?
   - ≥2 injected protocol subsystems; no silently discarded errors; no raw primitives in signatures (wrap in VOs; propagate errors)?
   - `lint-arwaky-cli scan <layer-path>` exits 0?
2. Verify orchestration only — computation → capabilities, domain data → taxonomy, pure helpers → utility.
3. Ensure an `_aggregate` contract exists — if missing, run `aes-contract` first.
4. Resolve the feature agent dir. Run `lint-arwaky-cli scan <layer-path>` — findings are the work list.
5. Implement the 3 blocks from § Template / § Section Contract; the class inherits the aggregate ABC via DI.
6. Check imports, I/O, computation, error handling, and primitives against § Rules.
7. Register in `__init__.py`, then compose via `aes-root` / consume via `aes-surface`.
8. **Placement (AES702/AES703)** — the file sits in a feature folder (`modules/<feature_name>/src/agent_<domain>_orchestrator`), not in `shared/` or a surface-dominated folder; `FRD.md` + `BACKLOG.md` at the feature folder root beside the source, with `FR-<NAME>-NNN` ids in protocol parity (`I*Protocol` count = FR count, `I*Aggregate` excluded; on mismatch fix the stale side — docs follow code — AES609); a capabilities-only folder without its own agent is a split feature (AES702 `feature_missing_agent`).
9. Fallback compile gate: `python -c "import <shared_package>.<module>"`.

## Review

- Block 1 → 2 → 3 order; Block 1 holds the constructor family including static factories; Block 2 holds only aggregate ABC methods; helper-vs-utility split respected (free functions extracted to `*_utility.py`) — § Rules → 3-Block Structure, § Rules → Helper vs Utility.
- Orchestration only: zero I/O, zero computation, zero domain data; DI via protocol ABCs (≥2 subsystems); shared VOs in signatures — § Rules → Allowed / forbidden operations, § Rules → Error and VO rules.
- No silently discarded errors (`or ""` on results); errors propagate or wrap into VOs — § Rules → Error and VO rules (Rule 1).
- No agent file in `shared/`; capabilities-only folders carry an agent of their own — § Workflow step 8.
- `contract_<name>_aggregate.py` exists; ≥1 aggregate, no implemented protocol (AES405-3), ≤3 types.

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
# Language compile is a fallback gate only: `python -c "import <module>"`
```
