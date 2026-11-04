# Report Format (all phases)

```text
## Deep-Clean Report: <unit>
### Summary            # files scanned, items analyzed, counts per category found
### Per-File Findings  # per file: | Item | Type | Lines | Verdict | Reason |
### 4-Lens Sweep Findings   # from Phase 3: | Finding | File:Line | Lens | Risk | Judo/fix |
### Structural Audit Findings  # from Phase 4: | Finding | File:Line | Severity | Judo move |
### Items Requiring Manual Review   # RISKY / ambiguous / INVESTIGATE / audit disagreements
### Formatting Fixes (auto-applied) # format-only changes needing no approval
### Bugs found          # genuine correctness bugs, separate from cleanup fixes
### Run mode           # "parallel fan-out" or "single-pass inline review"
```

Every finding carries a Verdict (KEEP / REMOVE / DELETE / INVESTIGATE / RESTRUCTURE) and a
one-line Reason. Each language reference contains a fully worked example table
(`python.md` § Phase 1 Workflow Step 1.7, `rust.md` § Phase 1 Workflow Step 1.7,
`typescript.md` § Phase 1 Workflow Step 1.7).

## Completion

- The report contains every section above and every finding carries a Verdict and one-line Reason.
