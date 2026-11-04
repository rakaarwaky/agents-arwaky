# Step 5c: Rust Verification & Cleanup

Language-variant of Step 5 for `target_lang = rust`. Run this pass after the GREEN/REFACTOR cycle in Step 4, before reporting done.

## Verification Checklist

- [ ] `RUST_BACKTRACE=1` shows the expected frames (if missing, env not propagated to subprocess)
- [ ] `dbg!()` line numbers match source (mismatch = stale build; `cargo clean` then rebuild)
- [ ] Debugger attached to the right binary (`target/debug/deps/` for tests)
- [ ] No stray `dbg!()` / `println!()` in committed code:
  ```bash
  rg -n 'dbg!\(|println!\(' --type rust src/ tests/
  ```

## Next

Return to [`step-5-verify.md`](step-5-verify.md) for the language-independent final pass (rationalization table, red-flags, reporting format).
