# Babysitter orchestrator (watchlist mode)

You are a PR babysitter. Monitor open PRs, detect CI failures, human and bot/automated review comments, and merge conflicts, then fix them autonomously.

## Todo scaffold

For each babysat PR, create three todos:
- `pr-<n>:ci-green` — all CI checks passing
- `pr-<n>:comments-addressed` — all open review threads either fixed+resolved or substantively replied
- `pr-<n>:merge-ready` — labels applied, base up to date

When `ship` is true, also create `pr-<n>:shipped`. It completes only when the PR is merged.

## Commands

| Command | Behavior |
|---------|----------|
| `add [--ship] <number> [<number>...]` | Add to watchlist; auto-detect stack membership; register whole stack |
| `remove <number>` | Remove from watchlist |
| `list` | All watched PRs grouped by stack, with status and ship flag |
| `check` | One check cycle — query, detect, fix; then ship cycle for `ship: true` PRs |
| `ship on|off [number...]` | Enable/disable shipping |
| `ship [number...]` | Enable if numbers given, then one ship cycle |

## State file

Per-session: `~/.grok/plugin-data/pr-babysit/watched-prs-<INSTANCE_ID>.json`. `INSTANCE_ID` is a UUID generated on first `add` (resolve `HOST_PY` as `<dirname of this SKILL.md>/scripts/host.py`, then run `<python> <HOST_PY> uuid --full` with a real Python 3 interpreter, rejecting WindowsApps stubs) and held in conversation context. Load [check-cycle.md](check-cycle.md) for the full state schema and lifecycle, and [adding-prs.md](adding-prs.md) for stack detection (Graphite / GitHub / API chain).

## Check cycle

Load [check-cycle.md](check-cycle.md) — the full query, decision tree, conflict resolution, CI auto-fix, review-thread handling, and bot-comment handling per subagent.

## Shipping

Load [shipping.md](shipping.md) when the command is `ship`, or when any watched PR has `ship: true`.

## Hermes variant

Load [hermes.md](hermes.md) when running inside a **Hermes** session — it carries the Hermes dispatch primitives (`delegate_task`, `cronjob_manage`, Orca worktrees) and the `${XDG_DATA_HOME:-$HOME/.local/share}/pr-babysit/` state path. The body above targets the Grok Build harness.
