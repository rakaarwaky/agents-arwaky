# HOW TO MAKE TESTING RUST

> **Purpose**: Give one crate a complete test suite — tests in `tests/`, benchmarks in `benches/`, never inline in `src/`; the file-name prefix is the virtual folder.
>
> **Audience**: Agents and engineers scaffolding AES test suites for Rust crates.
>
> **Scope**: `crates/<name>/` test and bench files — contract, unit, integration, smoke, e2e, acceptance, and bench with flat prefix naming.
>
> **Location**: `crates/<name>/tests/` and `crates/<name>/benches/` — both flat, no subdirectories; source under `src/` stays test-free.
>
> **Length**: One file per subject (`<type>_<subject>.rs`); coverage targets 70/60/50 for capabilities/agent/utility.

---

## Rules

### Placement rules

**Allowed:** `tests/` for every test type, `benches/` for benchmarks only.
**Forbidden:** inline `#[cfg(test)]` suites in `src/` files; subdirectories under `tests/` — the prefix IS the virtual folder.

### Naming rules

Pattern: `<type>_<subject>.rs` in `tests/`, `bench_<subject>.rs` in `benches/`.
Prefixes: `contract_`, `unit_`, `integration_`, `dogfood_`, `smoke_`, `e2e_`, `acceptance_`, `bench_`.

### Language rules

- **Benchmarks** (`benches/`): use `criterion` — never hand-rolled timing.
- Contract tests verify trait implementation.
- Integration tests: use real DI container.
- E2E tests: hit real entry point, assert on real output.
- Acceptance tests: map 1:1 to a business requirement (FRD/PRD ID).
- Smoke tests: must complete in under 5 seconds.

### Coverage targets

| Layer | Minimum |
| ----- | ------- |
| Capabilities | 70% |
| Agent | 60% |
| Utility | 50% |

### Workflow

1. Analyze crate / app structure.
2. Write `tests/contract_<crate>.rs`, `tests/unit_<crate>_<module>.rs`, `tests/integration_<crate>.rs`.
3. Write `tests/dogfood_<pipeline>.rs` (requires live session), then `tests/smoke_<app>.rs`, `tests/e2e_<flow>.rs`, `tests/acceptance_<FR_id>.rs`.
4. Write `benches/bench_<subject>.rs` + register in `Cargo.toml`.
5. Run `cargo test --workspace`, then verify coverage targets met.

---

## Template

### Directory layout

```text
crates/<name>/
├── src/
│   └── capabilities_my_struct.rs   # NO inline tests. Clean.
├── tests/                          # All test types, flat prefix naming
│   ├── contract_<crate>.rs
│   ├── unit_<crate>_<module>.rs
│   ├── integration_<crate>.rs
│   ├── smoke_<app>.rs
│   ├── e2e_<flow>.rs
│   └── acceptance_<FR_id>.rs
├── benches/                        # Benchmark tests only
│   └── bench_<subject>.rs
└── Cargo.toml                      # [[bench]] path → benches/bench_*.rs
```

### Cargo.toml for benchmarks

```toml
[[bench]]
name = "bench_<subject>"
path = "benches/bench_<subject>.rs"
harness = false
```

Registering a benchmark requires the `[[bench]]` block above **and** workflow step 4 includes
"+ register in Cargo.toml".

---

## Section Contract

| Check | Why it belongs here |
| ----- | ------------------- |
| No inline tests in `src/`. | Source stays clean; the suite lives under `tests/`/`benches/` only. |
| Flat prefix naming, no subdirectories under `tests/`. | The prefix IS the virtual folder — keeps discovery and CI filters uniform. |
| Contract test proves trait implementation exists. | Catches unimplemented seams before behaviour tests. |
| Unit tests cover happy path, edge cases, and error paths. | The baseline every PR must carry. |
| Integration test builds the real DI wiring; e2e asserts on real output. | Proves composition, not mocks. |
| Dogfood test runs against live service/session; skips when unavailable. | Real-end-to-end validation without mocks; CI-safe with skipif. |
| Dogfood test runs against live service/session; skips when unavailable. | Real-end-to-end validation without mocks; CI-safe with skipif. |
| Acceptance tests reference FRD/PRD IDs; smoke runs in <5s. | Requirement traceability plus a fast boot gate. |
| Benchmarks use `criterion` + `[[bench]]` registered in `Cargo.toml`. | Comparable, stable numbers; `cargo bench` discovers the target. |
| Coverage meets 70/60/50 for capabilities/agent/utility. | Per-layer floor before merge. |
| `cargo test --workspace` passes. | The suite is green or the work is not done. |

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

Dogfood tests are covered inline above; they skip in CI when services unavailable.


## Verify

```bash
cargo test --workspace
cargo bench
# Checks: contract/unit/integration/smoke/e2e/acceptance all green; criterion
# benchmarks discovered through the [[bench]] registration.
# Manual (not machine-checked): acceptance rows map 1:1 to FRD/PRD IDs; smoke <5s;
# no inline tests left in src/; prefixes flat, no subdirectories; coverage 70/60/50.
# Fallback compile gate: cargo check -p <crate-name>
```
