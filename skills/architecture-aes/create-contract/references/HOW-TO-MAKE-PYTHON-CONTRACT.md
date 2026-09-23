# HOW TO MAKE PYTHON CONTRACT

> **Purpose**: State a Python contract's public promises (protocol or aggregate) so outer
> layers can depend on the seam without importing a concretion.
>
> **Audience**: Agents and engineers scaffolding AES contract files in the shared domain.
>
> **Scope**: Pure ABC definitions in `contract_<concept>_<suffix>.py` — `_protocol` or
> `_aggregate` only.
>
> **Location**: Shared domain package next to taxonomy, registered in the shared
> package `__init__.py`.
>
> **Length**: `_protocol` = one method per feature; `_aggregate` = every method the
> surface/root exports. Only methods outer layers actually call.

---

## Rules

Seven rules. Each one prevents a specific failure mode.

1. **Suffix is strictly `_protocol` or `_aggregate`.** Type names: `I<Name>Protocol`,
   `I<Name>Aggregate`. File: `contract_<concept>_<suffix>.py`.
2. **ABC only — `@abstractmethod`, body is `...` or `pass`.** Never real code, never
   private-helper signatures, never convenience API (`AES101`/`AES102`).
3. **Protocol = exactly one method for one feature.** Each feature/capability gets a
   single uniform method (e.g. `run(...)` or the feature verb once). Same shape for
   every capability in the domain — no second method, no helpers on the ABC.
4. **Aggregate = many methods, one per exported consumer operation.** The aggregate is
   the **export surface**: every action the CLI/surface/root may call appears as its
   own method (`list_*`, `install_*`, `check_*`, `backup`, `restore`, …). Rich, typed,
   one row per export — not a single dump-all `execute()`.
5. **Allowed imports: taxonomy types and other contract types only.** Capabilities,
   agents, surface, root invert the dependency arrow (`AES201`/`AES205`).
6. **Signatures use shared VOs** — no `str`/`int`/`float`/`list[str]`/`dict` for domain
   values. `bool` allowed for semantic toggles only. All methods fully type-annotated;
   inherit `abc.ABC`.
7. **Register in shared `__init__.py`** with `__all__` + `_layer_symbols` for harness
   introspection.

---

## Template

Copy, fill, delete nothing.

### Protocol ABC — one method for one feature (uniform across capabilities)

```python
from abc import ABC, abstractmethod
from shared.<domain>.taxonomy_<domain>_vo import <VO>, <ResultVO>

class I<Name>Protocol(ABC):
    """Capability contract for one feature: <feature name> — <one sentence>."""

    @abstractmethod
    def <feature_method>(self, param: <VO>) -> <ResultVO>:
        """Run this one feature for *param*; return the result VO."""
        ...
```

**One feature → one method.** A second feature is a *second protocol ABC* (or a second
capability implementing the same shape), never a second method bolted onto the same
protocol. Naming: match the feature (`run`, `generate`, `install`, …) — still exactly
one abstract method per protocol file/class.

### Aggregate ABC — many methods, one per export

```python
from abc import ABC, abstractmethod
from shared.<domain>.taxonomy_<domain>_vo import (
    ExitCode,
    <ArgsVO>,
    <QueryVO>,
    <ResultVO>,
)

class I<Name>Aggregate(ABC):
    """Export surface over <domain>: one method per consumer operation."""

    @abstractmethod
    def <export_1>(self, args: <ArgsVO>) -> ExitCode:
        """Export 1: <what the surface runs>. Return exit code."""
        ...

    @abstractmethod
    def <export_2>(self, query: <QueryVO>) -> <ResultVO>:
        """Export 2: <what the surface runs>. Return result VO/exit code."""
        ...

    @abstractmethod
    def <export_n>(self, ...) -> ExitCode:
        """Export n: … — add one method per new surface verb."""
        ...
```

**The aggregate is what gets exported to consumers.** Every public operation the
surface/root needs is its own method here; the agent implements them by dispatching to
one-method protocol capabilities. Adding a consumer verb = a new aggregate method +
the matching one-method protocol feature — not a flag on a mega `execute()`.

---

## Section Contract

Every contract file is required to carry the rows that apply. Each exists for one reason.

| Section                       | Why it belongs here                                                        |
| ----------------------------- | -------------------------------------------------------------------------- |
| Module docstring (required)   | Names the contract's role: capability ABC or export/aggregate ABC.         |
| Suffix in file + class name   | AES101/AES102 resolve `_protocol` vs `_aggregate` from the name.           |
| Protocol: one method / feature | Fan-out stays uniform; each feature is one capability, one ABC method.     |
| Aggregate: one method / export | Surface/root exports stay typed and discoverable; no dump-all entry.        |
| Abstract methods only         | Outer layers depend on promises, not behaviour.                            |
| Shared VOs in signatures      | Domain values stay opaque across layers; no primitive leakage.             |
| No impl-layer imports         | Keeps the dependency arrow (capabilities → contract ← agent).              |
| `__all__` + `_layer_symbols`  | Harness/loader introspection and explicit public surface.                  |
| Register in shared `__init__` | Importable without reaching into private modules.                          |

---

## Verify

```bash
lint-arwaky-cli scan <contract-dir>
# Checks: AES101/AES102 (filename contract_<concept>_{protocol,aggregate}),
# AES201–AES205 (layer imports: no impl-layer imports; protocol ≠ aggregate import),
# AES402 (no primitives in signatures), role rules (contract ↔ capabilities/agent/surface).
# Manual (not machine-checked): protocol = exactly one method for one feature;
# aggregate = one method per consumer export (many exports, not a single execute()).
# Fallback compile gate: python -c "import <shared_package>.contract_<concept>_<suffix>".
```
