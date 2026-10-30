# Cleanup

After Step 6 (Memory Flush) and the Final Report, clean up the temporary artifact files with `<PYTHON> <HOST_PY> cleanup`. List each concrete path; do not use `rm -f` or globs that PowerShell will expand as `Remove-Item`. Missing files are ok.

```
<PYTHON> <HOST_PY> cleanup <path> <path> ...
```

## Files to Remove

| File | Count |
|------|-------|
| Implementation summary | `<scratch_dir>/grok-impl-summary-<IMPL_ID>.md` |
| Merged review | `<scratch_dir>/grok-review-<IMPL_ID>.md` |
| Per-reviewer reviews | `<scratch_dir>/grok-review-<IMPL_ID>-<suffix>.md` (`general`, `general-2`, `general-3`, `tests`, `security`, `plan`, `simplicity`) |
| Memory update spec | `<scratch_dir>/grok-mem-<IMPL_ID>.json` |

## Kept

| Item | Why |
|------|-----|
| Workspace memory file under `$HOME/.grok/implement-memory/` | Persists across runs as the shared memory file for this workspace |
| The worktree | Retired by a human or CI after the PR merges to `main` (post-merge action in the Final Report) |
