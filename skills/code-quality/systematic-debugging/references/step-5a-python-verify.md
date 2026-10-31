# Step 5a: Python Verification & Cleanup

Language-variant of Step 5 for `target_lang = python`. Run this pass after the GREEN/REFACTOR cycle in Step 4, before reporting done.

## Verification Checklist

- [ ] In the project's own dev venv, confirm: `.venv/bin/python -c "import debugpy; print(debugpy.__version__); print(debugpy.__file__)"`
- [ ] For remote debug, confirm the port is actually listening: `ss -tlnp | grep 5678`
- [ ] First breakpoint actually hit (if not: `PYTHONBREAKPOINT=0`, parallel/capturing runner, or execution finished before attach)
- [ ] `where` / `w` showed the expected call stack
- [ ] Post-debug cleanup complete — no stray `breakpoint()` / `set_trace()` in committed code:
  ```bash
  rg -n 'breakpoint\(\)|set_trace\(|debugpy\.listen' --type py
  ```

## Next

Return to [`step-5-verify.md`](step-5-verify.md) for the language-independent final pass (rationalization table, red-flags, reporting format).
