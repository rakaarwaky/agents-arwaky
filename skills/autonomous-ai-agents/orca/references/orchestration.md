# Orca Orchestration — supervised multi-agent coordination

Coordinate supervised Orca workers: threaded messages, blocking ask/reply,
task dispatch, worker_done/escalation waits, task DAGs, decision gates,
coordinator loops, and decomposing work across agents.

Engage Orca orchestration whenever you need structured multi-agent coordination.
Use [cli.md](cli.md) instead for full ownership handoffs ("hand off", "handoff",
"handover", "give this to another agent", "another worktree") when the user
did not ask to supervise, monitor, wait for results, or coordinate a DAG — and
for ordinary terminal control, shell commands, worktree management, and the
built-in browser. Coordination requires real Orca runtime state; never
substitute a non-Orca subagent tool.

## Load the version-matched guide

```text
ORCA skills get orchestration
```

That prints the compact, version-matched guide for the exact binary that will
handle your next commands. It covers the normal local coordinator loop. For a
conditional action gate such as remote placement, uncertain release recovery,
or expanded DAG work, load only the reference that gate names with
`ORCA skills get orchestration --reference references/<file>.md`
(`--references` lists the names). If that binary rejects `--reference`, run
`ORCA skills get orchestration --full` and read the named bundled reference
before acting.
