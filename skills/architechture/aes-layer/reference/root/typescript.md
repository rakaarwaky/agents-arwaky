# AES Root HOW-TO (Typescript)

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

1. **Suffix is strictly `_container` or `_entry`.** File: `root_<concept>_<suffix>.ts`.
   Documented exceptions: `index.ts`, `index.js`, barrel/entry files (AES101/AES102).
2. **Container = wire one feature only.** Instantiate capabilities; expose the aggregate (contract) type — never a concrete capability. Never business logic.
3. **Entry = bootstrap the app.** Read `process.argv` (if needed), compose feature container factories, start the surface/CLI loop. Never construct capabilities directly.
4. **Allowed imports: everything below root** — agent, capabilities, surface, contract, taxonomy, utility. Nothing below root may import root (AES201–AES205).
5. **No business logic, no orchestration policy, no technical parsing, no UI behaviour** — those live in capabilities / agent / utility / surface.
6. **Signatures use shared VOs** where domain values appear (AES402). `boolean` for semantic toggles only.
7. **Register** in package `index.ts`.

---

## Template

Copy, fill, delete nothing. File: `root_<concept>_<suffix>.ts` where `<suffix>` is `_container` or `_entry`.

### Container — wire one feature

```typescript
import { <Concept>Orchestrator } from '../<feature>/agent_<concept>_orchestrator';
import { <Capability> } from '../<feature>/capabilities_<concept>_<role>';
import { I<Concept>Aggregate } from '../shared/contract_<concept>_aggregate';
import { I<Concept>Protocol } from '../shared/contract_<concept>_protocol';

export class <Concept>Container {
    private readonly orchestrator: I<Concept>Aggregate;

    constructor(/* shared deps */) {
        const runners: I<Concept>Protocol[] = [
            new <Capability>(/* deps */),
        ];
        this.orchestrator = new <Concept>Orchestrator(runners);
    }

    get aggregate(): I<Concept>Aggregate {
        return this.orchestrator;
    }
}

export function create_<concept>_feature(/* shared deps */): I<Concept>Aggregate {
    return new <Concept>Container(/* deps */).aggregate;
}
```

**Container rules:** import capabilities + agent + contract types only; expose the aggregate (contract), never a concrete capability; no business/orchestration logic — construction and binding only.

### Entry — bootstrap the application

```typescript
import { create_<concept>_feature } from './root_<concept>_container';
import { main as surface_main } from './surface_<concept>_command';

async function main(argv: string[]): Promise<number> {
    const aggregate = create_<concept>_feature();
    return surface_main(aggregate, argv);
}

main(process.argv.slice(2)).then((code) => process.exit(code));
```

**Entry rules:** may parse argv (bootstrap only) and compose containers; start the surface/CLI loop; never import concrete capabilities directly — go through a container factory; no business logic.

---

## Section Contract

| Check | Why it belongs here|
| ----- | -------------------|
| Module docstring | Names the role: composition container or app entry.|
| Correct filename + suffix | AES101/AES102 resolve the layer and role from the name.|
| Layer-legal imports | Keeps the dependency arrow pointed down (AES201–AES205).|
| Contract types in signatures | Expose aggregate/protocol, not concretions (AES402).|
| Container: construct + bind only | Wiring is the whole job; logic belongs below.|
| Entry: compose containers + start | Bootstrap only; never new capabilities directly.|
| Registered in package barrel | Dead code otherwise; composition needs the export.|

---

## Workflow

1. **Determine role** — Container (wire one feature) or Entry (bootstrap all)?
2. **Create file** → `root_<concept>_<suffix>.ts`.
3. **Wire deps** → instantiate capabilities; bind to contract interfaces/aggregates.
4. **Verify** → `lint-arwaky-cli scan <layer-path>` then `npx tsc --noEmit`.

---

## Review

- Role suffix correct: `_container` (composition container) or `_entry` (app entry) — § Rules role rules.
- Container: construct + bind only, wiring is the whole job — § Rules container rules.
- Entry: compose containers + start, bootstrap only — § Rules entry rules.
- Layer-legal imports — expose contracts, never concrete capability types — § Rules import/signature rules.
- Registered in `index.ts` — dead code otherwise — § Rules registration rule.

### Anti-Patterns

- **Business / orchestration / parsing / UI logic in root** — move down a layer.
- **Entry importing `capabilities_*` directly** — go through a container factory.
- **Container exposing a concrete capability type** — return the aggregate contract.
- **Wrong suffix or undocumented name** — only `_container` / `_entry` (or listed exceptions).

---

## Verify

```bash
lint-arwaky-cli scan --layer root
# Checks: AES101/AES102 (filename + suffix), AES201–AES205 (layer imports),
# AES401–AES406 (role/primitive/structure rules for this layer).
# Manual (not machine-checked): correct role suffix; no business/orchestration/parsing/UI logic; nothing below root imports root.
# Fallback compile gate: npx tsc --noEmit
```
