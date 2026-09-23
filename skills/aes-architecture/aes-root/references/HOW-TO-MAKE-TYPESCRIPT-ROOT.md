# HOW TO MAKE ROOT TYPESCRIPT

> **Purpose**: Compose the system: containers wire capabilities to contracts; entries bootstrap and start the process.
>
> **Audience**: Agents and engineers scaffolding AES composition roots.
>
> **Scope**: Python, Rust, and TypeScript `root_<concept>_<container|entry>` files (plus documented barrel/entry exceptions).
>
> **Location**: Feature or app package top; the only layer that may construct implementations.
>
> **Length**: One container per feature; one (or few) entry files; no business logic, no orchestration policy.

---

## Rules

### Definition of Done

1. Correct suffix: `_container` or `_entry`.
2. Container: wires Capabilities to Contract interfaces/aggregates.
3. Entry: bootstraps application and composes feature containers.
4. May instantiate and wire components.
5. No business logic.
6. No orchestration policy.
7. No technical parsing or UI behavior.
8. `npx tsc --noEmit` passes.

### Workflow

1. **Determine role** — Container (wire one feature) or Entry (bootstrap all)?
2. **Create file** → `root_<concept>_<suffix>.ts`.
3. **Wire deps** → Connect Capabilities to Contract interfaces.
4. **Register** → update `index.ts`.
5. **Verify** → `npx tsc --noEmit`.

---

## Template

File: `root_<concept>_<suffix>.ts` where `<suffix>` is `_container` or `_entry`.

---

## Section Contract

| Section | Why it belongs here |
| ------- | ------------------- |
| Correct filename + suffix | AES101/AES102 resolve the layer and role from the name. |
| Layer-legal imports | Keeps the dependency arrow pointed down (AES201–AES205). |
| Shared VOs in signatures | Domain values stay opaque; no primitive leakage (AES401/AES402). |
| Registered in shared barrel | Dead code otherwise; composition needs the export. |

---

## Verify

```bash
lint-arwaky-cli scan <layer-path>
# Checks: AES101/AES102 (filename + suffix), AES201–AES205 (layer imports),
# AES401–AES406 (role/primitive/structure rules for this layer).
# Manual (not machine-checked): correct role suffix; no business/orchestration/parsing/UI logic; nothing below root imports root.
# Fallback compile gate: npx tsc --noEmit
```
