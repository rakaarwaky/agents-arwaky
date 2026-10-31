# Step 3c: Rust Debugger (dbg!, RUST_BACKTRACE, rust-gdb/lldb)

Language-variant of Step 3 for `target_lang = rust`. Picked when the bug site is Rust source.

## When to Use

- A `cargo test` failure whose traceback doesn't reveal why a value is wrong
- A panic with a truncated or missing backtrace
- Borrow-checker or lifetime errors you need to inspect at runtime
- Performance: CPU/memory profiling of a Rust binary

## Quick Reference

| Need | Command / Macro |
|---|---|
| Quick inspect a value | `dbg!(x);` — prints `file.rs:42: x = value` to stderr |
| Quick print | `println!("x = {:?}", x);` |
| Backtrace on panic | `RUST_BACKTRACE=1 cargo run` (`RUST_BACKTRACE=full` for all frames) |
| Test output (no capture) | `cargo test -- --nocapture` |
| Single test with output | `cargo test test_name -- --nocapture` |
| GDB breakpoints | `rust-gdb ./target/debug/<bin>` → `break src/main.rs:42`, `run` |
| LLDB | `rust-lldb ./target/debug/<bin>` |
| Programmatic backtrace | `let bt = std::backtrace::Backtrace::capture(); eprintln!("{}", bt);` |
| Conditional logging | `log::debug!("x={:?}", x)` + `RUST_LOG=debug cargo run` |
| Debug-only code path | `#[cfg(debug_assertions)] { ... }` |
| Log all modules | `RUST_LOG=trace cargo run` |

## Conditional Debug with `log` crate

```rust
// Cargo.toml: log = "0.4", env_logger = "0.11"
fn main() {
    env_logger::init();
    log::debug!("starting with config: {:?}", cfg);
}
```

```bash
RUST_LOG=debug cargo run          # this crate only
RUST_LOG=my_crate=trace cargo run # one crate at trace
```

## Programmatic Backtrace

```rust
use std::backtrace::Backtrace;
let bt = Backtrace::capture();   // disabled unless RUST_BACKTRACE set
eprintln!("captured:\n{}", bt);
```

Note: `Backtrace::capture()` returns a disabled backtrace unless `RUST_BACKTRACE` is set or `RUST_BACKTRACE=1` is in the environment at runtime.

## Common Pitfalls

1. **Borrow checker during debugging.** Temporary `let` bindings may fail to compile. Use `dbg!()` directly on expressions, or `.clone()` for inspection only (never commit the clone).
2. **`#[no_mangle]` affects symbol visibility.** Breakpoints by symbol name may not resolve. Use `file.rs:line` breakpoints instead.
3. **`cargo build` vs `cargo test` debug info.** Test binaries live in `target/debug/deps/`. Attach debuggers to the test binary, not the library. Run `cargo test --no-run` to build the test binary without executing.
4. **Buffered output under `cargo test`.** `println!`/`dbg!` are captured; use `--nocapture` or `eprintln!`.
5. **`RUST_BACKTRACE` only on panic by default.** For non-panic paths, call `Backtrace::capture()` explicitly and ensure the env var is set.
6. **Optimization hides variables.** Debug with `cargo build`/`cargo test` (debug profile). `cargo build --release` strips debug info by default; use `[profile.release] debug = true` only if profiling release.
7. **Conditional breakpoints in rust-gdb.** Use `break file.rs:42 if x > 5` — condition is Rust expression evaluated in scope.

## One-Shot Recipes

**"Why did this panic?"**
```bash
RUST_BACKTRACE=full cargo test -- --nocapture
# or for a binary:
RUST_BACKTRACE=full cargo run
```

**"What is this value at line X?"**
```rust
let result = compute(x);
dbg!(&result);   // prints file:line: &result = ...
```

**"Step through a failing test."**
```bash
cargo test --no-run          # build test binary
rust-gdb ./target/debug/deps/mycrate-<hash>
(gdb) break tests/integration.rs:42
(gdb) run --test-threads=1
```

**"Trace an intermittent failure."**
```bash
cargo test -- --nocapture 2>&1 | grep -i "test result"
# or run one test N times:
for i in $(seq 1 50); do cargo test flaky_test -- --nocapture || break; done
```

## Back to Step 3

After confirming the hypothesis with the debugger, return to [`step-3-hypothesis.md`](step-3-hypothesis.md) §3 to record the result and advance to Step 4. For post-fix cleanup verification, see [`step-5c-rust-verify.md`](step-5c-rust-verify.md).
