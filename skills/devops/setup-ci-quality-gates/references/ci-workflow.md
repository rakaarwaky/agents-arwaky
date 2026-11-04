# CI workflow (.github/workflows/ci.yml)

The five jobs on `ubuntu-latest` (Rust flavor shown; substitute per
language from the table in the SKILL.md Global Rules), plus the
differentiating self-lint job.

**Goal:** a `ci.yml` whose five jobs — fmt, clippy, build, test,
self-lint — mirror the gate table and make CI fail on the repo's own
architecture violations.

## Job table

| Job | Command | Notes |
|---|---|---|
| `fmt` | `cargo fmt --all -- --check` | rustfmt component only |
| `clippy` | `cargo clippy --all-targets -- -D warnings` | clippy component; install `mold` linker |
| `build` | `cargo build --release` | needs: build for downstream |
| `test` | `cargo nextest run --workspace --lib --tests -j 2` | needs: build; install nextest via curl |
| `self-lint` | `lint-arwaky-cli check .` == 0 violations | needs: build; also assert ≥24 AES codes on `workspaces-bad` |

Cache with sccache + Swatinem/rust-cache. Key env:
`RUSTC_WRAPPER=sccache`, `CARGO_BUILD_JOBS=4`, `RUST_MIN_STACK=33554432`.
(`CARGO_INCREMENTAL=0` belongs in `scripts/ci.sh` for local runs, not in
the workflow.)

## Self-lint job (architecture enforcement)

The differentiator: CI fails if the repo violates its own architecture
rules — the `self-lint` job asserts zero whole-repo violations plus
the AES rule engine still firing all 24 codes on the
intentional-violation fixture workspace (`workspaces-bad`), catching a
linter that silently stops detecting anything.

See `references/self-lint.md` for the job script (exit-code-authoritative
check, fixture assertion, and the `cargo build --release`
prerequisite).

## Completion

- All five jobs exist in `.github/workflows/ci.yml` with the commands
  above.
- The self-lint job runs after `build` and asserts both the
  zero-violation and the ≥24 AES-code fixture checks.
