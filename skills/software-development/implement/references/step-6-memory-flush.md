# Step 6 Memory Flush


After the loop terminates with 0 open issues, update the workspace memory file with patterns from this run. The orchestrator performs this directly using its own tools — no subagent is needed for this step.

The write goes through `"${PYTHON}" "${MEMORY_HELPER}" update --file <spec>` so that:
- The path resolves to the **shared workspace-scoped file** (`$HOME/.grok/implement-memory/<workspace-id>.md`), not a per-worktree file.
- An exclusive lock (`fcntl.flock` on POSIX, `msvcrt.locking` on Windows; no `flock(1)` shell binary required) is held during the read-merge-write.
- Strict input validation: malformed types fail fast with exit code 4 and a clear error message.

Full procedure — sub-steps 6a (collect & categorize patterns), 6b (harmonize phrasing), 6c (build the update spec), 6d (invoke the helper) — plus the memory file format and helper exit codes: load [`references/memory-flush.md`](references/memory-flush.md).

Graceful degradation: if the helper exits non-zero, log a warning with its stderr and skip the memory update. The implementation is already complete and reviewed — never fail the run due to memory flush issues.

