# HOW TO MAKE TAXONOMY PYTHON

> **Purpose**: Define the stable language of the domain: value objects, entities, errors, events, and constants.
>
> **Audience**: Agents and engineers scaffolding AES taxonomy files in the shared domain.
>
> **Scope**: Python, Rust, and TypeScript `taxonomy_<domain>_<suffix>` files — suffixes `_vo`, `_entity`, `_error`, `_event`, `_constant` only.
>
> **Location**: Shared domain source root next to contracts (`modules/shared/src/<domain>/` | `crates/shared/src/<domain>/` | `packages/shared/src/<domain>/`), registered in the shared barrel.
>
> **Length**: One type per file; no I/O, no upward imports, no primitives for domain fields.

---

## Rules

### Import rules

**Allowed imports:** other taxonomy types, stdlib.
**Forbidden:** capabilities, agents, surface, root, contracts, I/O (in VOs/entities/errors/events/constants).

### File-name suffix table

| Suffix         | Content                | Key constraint                             |
| ---------------- | ------------------------ | -------------------------------------------- |
| `_vo.py`       | Value Objects          | Validate in`__init__`, immutable, no I/O   |
| `_entity.py`   | Entities with identity | Identity VO field required                 |
| `_error.py`    | Domain errors          | Extend`Exception`, VO fields only          |
| `_event.py`    | Domain events          | Immutable, VO payload fields               |
| `_constant.py` | Compile-time constants | Pure literals only — no functions, no I/O |
| `_utility.py`  | Stateless helpers      | No class, no`self`, domain-agnostic        |

### VO primitive rules (AES401)

Forbidden for domain fields: `str`, `int`, `float`, `list[str]`, `dict`.
`bool` allowed for semantic toggles only.

### Workflow

1. Determine type (VO/Entity/Error/Event/Constant/Utility).
2. Create `taxonomy_<domain>_<type>.py` in `shared/src/<domain>/`.
3. VOs: validate in `__init__`, use `@dataclass(frozen=True)` or manual.
4. Errors: extend `Exception`.
5. Constants: pure literals only.
6. Register in `__init__.py`.
7. `python -c "import <module>"`.

---

## Template

### Value Object

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class <Name>:
    _value: str

    def __post_init__(self) -> None:
        if not self._value.strip():
            raise ValueError("<Name> cannot be empty")

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value
```

### Entity

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class <Name>:
    _value: str

    def __post_init__(self) -> None:
        if not self._value.strip():
            raise ValueError("<Name> cannot be empty")

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value
```

### Error

```python
class <Name>Error(Exception):
    def __init__(self, message: str):
        self._message = message
        super().__init__(message)

    @property
    def message(self) -> str:
        return self._message
```

### Constants

```python
# Default value description.
<NAME>_DEFAULT: float = 24.0

# Minimum value description.
<NAME>_MIN: float = 0.5

# Filename constant.
<NAME>_FILENAME: str = "file.json"
```

---

## Section Contract

| Check | Why it belongs here |
| ----- | ------------------- |
| Correct suffix. | Required by AES layer rules and the linter; missing it is a defect. |
| VOs validate on construction; composite VOs use other VOs (no raw primitives). | Required by AES layer rules and the linter; missing it is a defect. |
| Errors extend `Exception`. | Required by AES layer rules and the linter; missing it is a defect. |
| Constants are pure literal values. | Required by AES layer rules and the linter; missing it is a defect. |
| No import from capabilities, agents, surface, root, contracts. | Required by AES layer rules and the linter; missing it is a defect. |
| No I/O, network, or database in taxonomy files. | Required by AES layer rules and the linter; missing it is a defect. |
| Registered in shared `__init__.py`. | Required by AES layer rules and the linter; missing it is a defect. |
| `python -c "import <module>"` passes. | Required by AES layer rules and the linter; missing it is a defect. |

---

## Verify

```bash
lint-arwaky-cli scan <layer-path>
# Checks: AES101/AES102 (filename + suffix), AES201–AES205 (layer imports),
# AES401–AES406 (role/primitive/structure rules for this layer).
# Manual (not machine-checked): VO validates on construction; constants are pure literals; no I/O.
# Fallback compile gate: python -c "import <shared_package>.<module>"
```
