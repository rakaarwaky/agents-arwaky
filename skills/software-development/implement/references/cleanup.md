# Cleanup


After Step 6 (Memory Flush) and the Final Report, clean up the temporary artifact files with `<PYTHON> <HOST_PY> cleanup` (list each concrete path; do not use `rm -f` or globs that PowerShell will expand as `Remove-Item`):

```
<PYTHON> <HOST_PY> cleanup <scratch_dir>/grok-impl-summary-<IMPL_ID>.md <scratch_dir>/grok-review-<IMPL_ID>.md <scratch_dir>/grok-mem-<IMPL_ID>.json
```

Also pass each per-reviewer file you created (`grok-review-<IMPL_ID>-general.md`, `-tests.md`, `-simplicity.md`, etc.). Missing files are ok.

Note: the workspace memory file under `$HOME/.grok/implement-memory/` is NOT cleaned up — it persists across runs as the shared memory file for this workspace.
