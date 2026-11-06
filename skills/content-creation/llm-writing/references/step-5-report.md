# Step 5 — Report

End every run with this report (max 10 lines):

```
mode: create | improve
files: <path> (<before> -> <after> lines) | new: <path> (<after> lines)
tokens: ~<before> -> ~<after> (-<pct>%)
conflicts: <n> (<CONFLICT: ...> lines, or none)
skipped: <out-of-scope issues left unchanged, or none>
```

## Checks before completion

- [ ] No repeated fact (R1).
- [ ] No filler sentence (R2).
- [ ] Every name exact or `UNKNOWN` (R3).
- [ ] Control keywords backticked (R4).
- [ ] Meaning preserved: no deleted action, constraint, or fact.
- [ ] Nothing outside slop/concision/clarity was changed.
