# HOW TO MAKE TESTING PYTHON

> **Purpose**: Give one module a complete test suite — tests in `tests/`, benchmarks in `benches/`, never inline in the source file; the file-name prefix is the virtual folder.
>
> **Audience**: Agents and engineers scaffolding AES test suites for Python modules.
>
> **Scope**: `modules/<name>/` test and bench files — contract, unit, integration, smoke, e2e, acceptance, and bench with flat prefix naming.
>
> **Location**: `modules/<name>/tests/` and `modules/<name>/benches/` — both flat, no subdirectories; source under `src/` stays test-free.
>
> **Length**: One file per subject (`<type>_<subject>.py`); coverage targets 70/60/50 for capabilities/agent/utility.

---

## Rules

### Placement rules

**Allowed:** `tests/` for every test type, `benches/` for benchmarks only.
**Forbidden:** inline tests in `src/` files; subdirectories under `tests/` — the prefix IS the virtual folder.

### Naming rules

Pattern: `<type>_<subject>.py` in `tests/`, `bench_<subject>.py` in `benches/`.
Prefixes: `contract_`, `unit_`, `integration_`, `smoke_`, `e2e_`, `acceptance_`, `bench_`.

### Language rules

- **Benchmarks** (`benches/`): use `pytest-benchmark` — never hand-rolled timing.
- Contract tests verify class/protocol implementation exists.
- Integration tests: use real DI container / entry point.
- E2E tests: hit real CLI/API, assert on real output.
- Acceptance tests: map 1:1 to a business requirement (FRD/PRD ID).
- Smoke tests: must complete in under 5 seconds.

### Coverage targets

| Layer | Minimum |
| ----- | ------- |
| Capabilities | 70% |
| Agent | 60% |
| Utility | 50% |

### Workflow

1. Analyze module / app structure.
2. Write `tests/contract_<module>.py`, `tests/unit_<module>_<subject>.py`, `tests/integration_<module>.py`.
3. Write `tests/smoke_<app>.py`, `tests/e2e_<flow>.py`, `tests/acceptance_<FRD_ID>.py`.
4. Write `benches/bench_<subject>.py`.
5. Run `pytest --tb=short`, then verify coverage targets met.

---

## Template

### Directory layout

```text
modules/<name>/
├── src/
│   └── capabilities_my_class.py    # NO inline tests. Clean.
├── tests/                          # All test types, flat prefix naming
│   ├── contract_<module>.py
│   ├── unit_<module>_<subject>.py
│   ├── integration_<module>.py
│   ├── smoke_<app>.py
│   ├── e2e_<flow>.py
│   └── acceptance_<FRD_ID>.py
├── benches/                        # Benchmark tests only
│   └── bench_<subject>.py
└── pyproject.toml
```

---

## Section Contract

| Check | Why it belongs here |
| ----- | ------------------- |
| No inline tests in `src/`. | Source stays clean; the suite lives under `tests/`/`benches/` only. |
| Flat prefix naming, no subdirectories under `tests/`. | The prefix IS the virtual folder — keeps discovery and CI filters uniform. |
| Contract test proves protocol/class implementation exists. | Catches unimplemented seams before behaviour tests. |
| Unit tests cover happy path, edge cases, and error paths. | The baseline every PR must carry. |
| Integration test builds the real DI wiring; e2e asserts on real output. | Proves composition, not mocks. |
| Acceptance tests reference FRD/PRD IDs; smoke runs in <5s. | Requirement traceability plus a fast boot gate. |
| Benchmarks use `pytest-benchmark`, not manual timing loops. | Comparable, stable numbers across runs. |
| Coverage meets 70/60/50 for capabilities/agent/utility. | Per-layer floor before merge. |
| `pytest --tb=short` passes. | The suite is green or the work is not done. |

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
pytest --tb=short
pytest --benchmark-only benches/bench_<subject>.py
pytest --cov=<module> --cov-fail-under=<target>
# Checks: contract/unit/integration/smoke/e2e/acceptance all green; benchmark runs
# through pytest-benchmark; per-layer coverage floors 70/60/50 met.
# Manual (not machine-checked): acceptance rows map 1:1 to FRD/PRD IDs; smoke <5s;
# no inline tests left in src/; prefixes flat, no subdirectories.
# Fallback compile gate: python -c "import <module>"
```
