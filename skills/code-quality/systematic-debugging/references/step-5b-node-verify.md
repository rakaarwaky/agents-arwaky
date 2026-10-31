# Step 5b: Node.js / TypeScript Verification & Cleanup

Language-variant of Step 5 for `target_lang = typescript` or `node`. Run this pass after the GREEN/REFACTOR cycle in Step 4, before reporting done.

## Verification Checklist

After setting up a debug session, verify:

- [ ] `curl -s http://127.0.0.1:9229/json/list` returns exactly the target you expect
- [ ] First breakpoint actually hit (if not: missed `--inspect-brk` or attached after execution completed)
- [ ] Source listing at pause shows the right file (mismatch = sourcemap issue, see pitfall 1 in [`step-3b-node-debugger.md`](step-3b-node-debugger.md))
- [ ] `exec process.pid` in `repl` returns the PID you meant to attach to

## Cleanup Grep

```bash
rg -n 'console\.log\(|debugger;' --type ts
```

Remove any temporary `console.log` / `debugger;` added during investigation, or re-tag them as `[DEBUG-a4f2]`-style prefixes so cleanup is a single search.

## Next

Return to [`step-5-verify.md`](step-5-verify.md) for the language-independent final pass (rationalization table, red-flags, reporting format).
