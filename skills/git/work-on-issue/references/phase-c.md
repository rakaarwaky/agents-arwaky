# Phase C — Fan-out setup: 1 issue → 1 Orca worktree → 1 owner

Resolve the Orca CLI once (`orca-cli` skill): `$ORCA_CLI_COMMAND`, else `orca-dev` in a dev checkout, else `orca-ide` on Linux outside Orca, else `orca`. Prefer `--json`.

```bash
ORCA repo list --json
# capture repoId for this repository
```

Create all worktrees from the repo default base in one loop. Independent issue work uses `--no-parent` and omits `--base-branch` so Orca uses the repo default:

```bash
ORCA worktree create --repo id:<repoId> --name issue-N --no-parent --json
```

To spawn the owner in the same call, add `--agent <id> --prompt "<child brief>"`. For a single issue you implement yourself, omit `--agent` and open a shell/agent later.

Defaults (override only when the user names different options):

| Knob | Default |
| --- | --- |
| Worktree manager | Orca (`worktree create` / `set` / `rm`) |
| Lineage | `--no-parent` for independent issue work |
| Name / selector | `issue-N`; selector `path:<absPath>` or full `id:<repoId>::<path>` |
| Branch | Orca default from repo base ref (do not base on the current feature branch) |
| Isolation | one build artifact dir per worktree — see [isolation-recipes.md](isolation-recipes.md) |
| Wave size | ≤ concurrency limit (typically 10) |
| Child scope | local commits only; no push, no PR, no tracker writes |

Write decisions + per-issue evidence to a session state file the children can read (e.g. `.agents/session-notes.md`). It is the source for every child's context — children see nothing else of this conversation.

When driving an already-running agent terminal: wait for TUI idle before send.

```bash
ORCA terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json
# only when satisfied: true
ORCA terminal send --terminal <handle> --text "<child brief>" --enter --json
```

Every child brief must state:

- Work **only** inside the assigned worktree; never touch sibling worktrees or shared state dirs.
- Use **per-worktree build isolation** (own artifact/cache dir; never the repo-shared one).
- Targeted checks only (`<tool> check/test -p <package>` or the language equivalent); never workspace-wide gate scripts — they serialize and slow every sibling.
- Local commits allowed (conventional messages); **no push, no PR, no tracker writes**.
- Close the report with: files changed, mechanism, verification command + real output, commit sha.

For "verify first, fix if still broken" issues, the child brief asks for a verdict (`fixed-on-main` / `still-broken`) plus the regression test pinning the behavior — never for issue closure (the parent decides closure).
