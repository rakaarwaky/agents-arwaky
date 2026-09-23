# HOW TO MAKE RUST CONTRACT

> **Purpose**: State a Rust contract's public promises (protocol or aggregate) so outer
> layers can depend on the seam without importing a concretion.
>
> **Audience**: Agents and engineers scaffolding AES contract traits in the shared domain.
>
> **Scope**: Pure trait definitions in `contract_<concept>_<suffix>.rs` — `_protocol` or
> `_aggregate` only. No default bodies.
>
> **Location**: Shared domain crate next to taxonomy, registered in the shared `mod.rs`.
>
> **Length**: `_protocol` = one method per feature; `_aggregate` = every method the
> surface/root exports. Only methods outer layers actually call.

---

## Rules

Seven rules. Each one prevents a specific failure mode.

1. **Suffix is strictly `_protocol` or `_aggregate`.** Type names: `I<Name>Protocol`,
   `I<Name>Aggregate`. File: `contract_<concept>_<suffix>.rs`.
2. **`pub trait` only — methods end with `;`, no bodies.** Never default
   implementations, never private-helper signatures (`AES101`/`AES102`).
3. **Protocol = exactly one method for one feature.** Each feature/capability gets a
   single uniform method. Same shape for every capability in the domain — no second
   method, no helpers on the trait.
4. **Aggregate = many methods, one per exported consumer operation.** The aggregate is
   the **export surface**: every action the CLI/surface/root may call appears as its
   own method. Rich, typed, one row per export — not a single dump-all `execute()`.
5. **Allowed imports: taxonomy types and other contract types only.** Capabilities,
   agents, surface, root invert the dependency arrow (`AES201`/`AES205`).
6. **Signatures use shared VOs** — no `String`/`i32`..`u64`/`f32`/`f64`/`Vec<String>` for
   domain values. `bool` and `&str` (non-domain input) allowed with care. Trait
   object-safe (generic members `where Self: Sized`) and `Send + Sync` bounded. All
   methods type-annotated.
7. **Register in shared `mod.rs`** so the pair is importable.

---

## Template

Copy, fill, delete nothing.

### Protocol trait — one method for one feature (uniform across capabilities)

```rust
use shared::<domain>::taxonomy_<domain>_vo::{ResultVO, VO};

pub trait I<Name>Protocol: Send + Sync {
    /// Capability contract for one feature: <feature name> — <one sentence>.
    fn <feature_method>(
        &self,
        param: &VO,
    ) -> ResultVO;
}
```

**One feature → one method.** A second feature is a *second protocol trait* (or a
second capability implementing the same shape), never a second method bolted onto the
same protocol.

### Aggregate trait — many methods, one per export

```rust
use shared::<domain>::taxonomy_<domain>_vo::{ArgsVO, QueryVO, VO};

pub trait I<Name>Aggregate: Send + Sync {
    /// Export surface over <domain>: one method per consumer operation.

    /// Export 1: <what the surface runs>.
    fn <export_1>(&self, args: &ArgsVO) -> ExitCode;

    /// Export 2: <what the surface runs>.
    fn <export_2>(&self, query: &QueryVO) -> VO;

    /// Export n: add one method per new surface verb.
    fn <export_n>(&self, /* … */) -> ExitCode;
}
```

**The aggregate is what gets exported to consumers.** Every public operation the
surface/root needs is its own method; the agent implements them by dispatching to
one-method protocol capabilities.

### mod.rs

```rust
// <domain> — contract traits for <domain> operations
pub mod contract_<name>_protocol;
pub mod contract_<name>_aggregate;
```

---

## Section Contract

Every contract file is required to carry the rows that apply. Each exists for one reason.

| Section                        | Why it belongs here                                                         |
| ------------------------------ | --------------------------------------------------------------------------- |
| Module docstring (required)    | Names the contract's role: capability trait or export/aggregate trait.      |
| Suffix in file + trait name    | AES101/AES102 resolve `_protocol` vs `_aggregate` from the name.            |
| Protocol: one method / feature | Fan-out stays uniform; each feature is one capability, one trait method.    |
| Aggregate: one method / export | Surface/root exports stay typed and discoverable; no dump-all entry.         |
| Method signatures only (`;`)   | Outer layers depend on promises, not behaviour.                             |
| `Send + Sync` + object-safe    | Trait objects cross thread/task boundaries without surprises.               |
| Shared VOs in signatures       | Domain values stay opaque across layers; no primitive leakage.              |
| No impl-layer imports          | Keeps the dependency arrow (capabilities → trait ← agent).                  |
| Register in shared `mod.rs`    | Importable without reaching into private modules.                           |

---

## Verify

```bash
lint-arwaky-cli scan <contract-dir>
# Checks: AES101/AES102 (filename contract_<concept>_{protocol,aggregate}),
# AES201–AES205 (layer imports: no impl-layer imports; protocol ≠ aggregate import),
# AES402 (no primitives in signatures), role rules (contract ↔ capabilities/agent/surface).
# Manual (not machine-checked): protocol = exactly one method for one feature;
# aggregate = one method per consumer export (many exports, not a single execute());
# traits object-safe, Send + Sync, no default bodies.
# Fallback compile gate: cargo check -p <crate-name>.
```
