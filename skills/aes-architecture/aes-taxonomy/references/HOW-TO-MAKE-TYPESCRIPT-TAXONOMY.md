# HOW TO MAKE TAXONOMY TYPESCRIPT

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

**Allowed imports:** other taxonomy types, stdlib (`node:path`, etc.).
**Forbidden:** capabilities, agents, surface, root, contracts, `fs.`/`fetch`/database (in VOs/entities/errors/events/constants).

### File-name suffix table

| Suffix         | Content                | Key constraint                                     |
| ---------------- | ------------------------ | ---------------------------------------------------- |
| `_vo.ts`       | Value Objects          | `readonly` fields, validate in constructor, no I/O |
| `_entity.ts`   | Entities with identity | Identity VO field required                         |
| `_error.ts`    | Domain errors          | `extends Error`, set `this.name`                   |
| `_event.ts`    | Domain events          | Immutable, VO payload fields                       |
| `_constant.ts` | Compile-time constants | `export const` only — no functions                |
| `_utility.ts`  | Stateless helpers      | No class, no`this`, domain-agnostic                |

### VO primitive rules (AES401)

Forbidden for domain fields: `string`, `number`, `string[]`, `Record<string,T>`.
`boolean` allowed for semantic toggles only.

### Workflow

1. Determine type (VO/Entity/Error/Event/Constant/Utility).
2. Create `taxonomy_<domain>_<type>.ts` in `shared/src/<domain>/`.
3. VOs: `readonly` fields, validate in constructor, throw on invalid.
4. Errors: `extends Error`, set `this.name`.
5. Constants: `export const NAME = value` only.
6. Register in `index.ts`.
7. `npx tsc --noEmit`.

---

## Template

### Value Object

```typescript
export class <Name> {
    private readonly _value: string;

    constructor(value: string) {
        if (!value.trim()) {
            throw new Error('<Name> cannot be empty');
        }
        this._value = value;
    }

    get value(): string {
        return this._value;
    }

    toString(): string {
        return this._value;
    }
}
```

### Entity

```typescript
export class <Name> {
    private readonly _value: string;

    constructor(value: string) {
        if (!value.trim()) {
            throw new Error('<Name> cannot be empty');
        }
        this._value = value;
    }

    get value(): string {
        return this._value;
    }

    toString(): string {
        return this._value;
    }
}
```

### Error

```typescript
export class <Name>Error extends Error {
    constructor(message: string) {
        super(message);
        this.name = '<Name>Error';
    }
}
```

### Constants

```typescript
/** Default value description. */
export const <NAME>_DEFAULT: number = 24.0;

/** Minimum value description. */
export const <NAME>_MIN: number = 0.5;

/** Filename constant. */
export const <NAME>_FILENAME: string = 'file.json';
```

---

## Section Contract

| Check | Why it belongs here |
| ----- | ------------------- |
| Correct suffix. | Required by AES layer rules and the linter; missing it is a defect. |
| VOs: `readonly` fields, validate on construction; composite VOs use other VOs. | Required by AES layer rules and the linter; missing it is a defect. |
| Errors extend `Error`, set `this.name`. | Required by AES layer rules and the linter; missing it is a defect. |
| Constants are `export const` pure literal values. | Required by AES layer rules and the linter; missing it is a defect. |
| No import from capabilities, agents, surface, root, contracts. | Required by AES layer rules and the linter; missing it is a defect. |
| No I/O, network, or database in taxonomy files. | Required by AES layer rules and the linter; missing it is a defect. |
| Registered in shared `index.ts`. | Required by AES layer rules and the linter; missing it is a defect. |
| `npx tsc --noEmit` passes. | Required by AES layer rules and the linter; missing it is a defect. |

---

## Verify

```bash
lint-arwaky-cli scan <layer-path>
# Checks: AES101/AES102 (filename + suffix), AES201–AES205 (layer imports),
# AES401–AES406 (role/primitive/structure rules for this layer).
# Manual (not machine-checked): VO validates on construction; constants are pure literals; no I/O.
# Fallback compile gate: npx tsc --noEmit
```
