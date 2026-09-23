# HOW TO MAKE TESTING TYPESCRIPT

> **Purpose**: Give one package a complete test suite — tests in `tests/`, benchmarks in `benches/`, never inline in the source file; the file-name prefix is the virtual folder.
>
> **Audience**: Agents and engineers scaffolding AES test suites for TypeScript packages.
>
> **Scope**: `packages/<name>/` test and bench files — contract, unit, integration, smoke, e2e, acceptance, and bench with flat prefix naming.
>
> **Location**: `packages/<name>/tests/` and `packages/<name>/benches/` — both flat, no subdirectories; source under `src/` stays test-free.
>
> **Length**: One file per subject (`<type>_<subject>.ts`); coverage targets 70/60/50 for capabilities/agent/utility.

---

## Rules

### Placement rules

**Allowed:** `tests/` for every test type, `benches/` for benchmarks only.
**Forbidden:** inline tests in `src/` files; subdirectories under `tests/` — the prefix IS the virtual folder.

### Naming rules

Pattern: `<type>_<subject>.ts` in `tests/`, `bench_<subject>.ts` in `benches/`.
Prefixes: `contract_`, `unit_`, `integration_`, `smoke_`, `e2e_`, `acceptance_`, `bench_`.

### Language rules

- **Benchmarks** (`benches/`): use `vitest/benchmark` — never hand-rolled timing.
- Contract tests verify class/interface implementation.
- Integration tests: use real DI container / entry point.
- E2E tests: hit real API/CLI, assert on real output.
- Acceptance tests: map 1:1 to a business requirement (FRD/PRD ID).
- Smoke tests: must complete in under 5 seconds.

### Coverage targets

| Layer | Minimum |
| ----- | ------- |
| Capabilities | 70% |
| Agent | 60% |
| Utility | 50% |

### Workflow

1. Analyze package / app structure.
2. Write `tests/contract_<package>.ts`, `tests/unit_<package>_<module>.ts`, `tests/integration_<package>.ts`.
3. Write `tests/smoke_<app>.ts`, `tests/e2e_<flow>.ts`, `tests/acceptance_<FRD_ID>.ts`.
4. Write `benches/bench_<subject>.ts`.
5. Run `npx vitest run`, then verify coverage targets met.

---

## Template

### Directory layout

```text
packages/<name>/
├── src/
│   └── capabilities_my_class.ts    # NO inline tests. Clean.
├── tests/                          # All test types, flat prefix naming
│   ├── contract_<package>.ts
│   ├── unit_<package>_<module>.ts
│   ├── integration_<package>.ts
│   ├── smoke_<app>.ts
│   ├── e2e_<flow>.ts
│   └── acceptance_<FRD_ID>.ts
├── benches/                        # Benchmark tests only
│   └── bench_<subject>.ts
├── vitest.config.ts                # Test config + coverage
└── package.json                    # devDependencies: vitest
```

### vitest.config.ts

```typescript
import { defineConfig } from "vitest/config";
export default defineConfig({
  test: {
    globals: true,
    environment: "node",
    include: ["tests/**/*.ts"],
    exclude: ["benches/**/*.ts"],
  },
});
```

---

## Section Contract

| Check | Why it belongs here |
| ----- | ------------------- |
| No inline tests in `src/`. | Source stays clean; the suite lives under `tests/`/`benches/` only. |
| Flat prefix naming, no subdirectories under `tests/`. | The prefix IS the virtual folder — keeps discovery and CI filters uniform. |
| Contract test proves class/interface implementation exists. | Catches unimplemented seams before behaviour tests. |
| Unit tests cover happy path, edge cases, and error paths. | The baseline every PR must carry. |
| Integration test builds the real DI wiring; e2e asserts on real output. | Proves composition, not mocks. |
| Acceptance tests reference FRD/PRD IDs; smoke runs in <5s. | Requirement traceability plus a fast boot gate. |
| `vitest.config.ts` includes `tests/`, excludes `benches/`. | Test runs and benchmark runs never mix. |
| Benchmarks use `vitest/benchmark`, not manual timing loops. | Comparable, stable numbers across runs. |
| Coverage meets 70/60/50 for capabilities/agent/utility. | Per-layer floor before merge. |
| `npx vitest run` passes. | The suite is green or the work is not done. |

---


---

## Dogfood / Integration Pipeline Tests

For tests that exercise actual CLI commands against live services/sessions:

1. **Place** in `tests/integration/` or project-equivalent directory.
2. **Name** with `integration_` prefix (e.g., `integration_pipeline.py`).
3. **Always provide skip logic** — check for required credentials/sessions before running.
4. **Structure tests first** — verify command exists without external deps.
5. **Functional tests second** — run actual pipeline with real inputs.
6. **Use fixtures** — create temporary test files, cleanup after.
7. **Never require login in CI** — skip gracefully when deps unavailable.

See [HOW-TO-MAKE-DOGFOOD-TESTS.md](HOW-TO-MAKE-DOGFOOD-TESTS.md) for complete template.


## Verify

```bash
npx vitest run
npx vitest bench benches/bench_<subject>.ts
npx vitest run --coverage
# Checks: contract/unit/integration/smoke/e2e/acceptance all green; benchmarks run
# through vitest/benchmark with benches excluded from the test glob; coverage floors met.
# Manual (not machine-checked): acceptance rows map 1:1 to FRD/PRD IDs; smoke <5s;
# no inline tests left in src/; prefixes flat, no subdirectories; coverage 70/60/50.
# Fallback compile gate: npx tsc --noEmit
```
