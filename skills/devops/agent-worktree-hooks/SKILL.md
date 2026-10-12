---
name: agent-worktree-hooks
description: Set up guard hooks for immutable clone and Orca worktrees.
version: 1.0.0
author: rakaarwaky
license: MIT
metadata:
  tags:
    - hooks
    - worktree
    - git-discipline
    - orca
    - guard-rails
    - hermes
    - grok
  related_skills:
    - orca-cli
    - hermes-agent
    - hermes-home-cleanup
  triggers:
    - worktree enforcement
    - guard hooks
    - immutable clone
    - orca worktree discipline
    - adapt hooks
  hermes:
    tags:
      - hooks
      - worktree
      - git-discipline
      - orca
      - guard-rails
    related_skills:
      - orca-cli
      - hermes-agent
      - hermes-home-cleanup
---

## When to Use

- Setting up or porting worktree-enforcement guard hooks for any agent (Hermes, Grok, etc.)
- Enforcing immutable default-branch clone + all git work in Orca worktrees
- Adapting the hook system to a new agent environment
- Debugging hook firing, allowlist, or revert behavior

# Agent Worktree Enforcement Hooks

Guard hooks that prevent direct commits/pushes/writes to the default-branch
clone and force all git work into Orca worktrees under `~/orca/workspaces/`.
The agent's default checkout stays pinned to `main`/`master` as a read-only
source of truth.

## Architecture

```text
PreToolUse (guard-main-pre.sh)
    │
    ├─ qualify-tool-input.sh     # auto-qualify tool names, fill required fields
    ├─ guard-worktree-branch.sh  # deny commit/push on default branch IN worktrees
    ├─ guard-branch-pin.sh       # deny checkout/switch/write on main worktree
    └─ guard-main-clone.sh       # deny push/commit/tag/rebase/merge/reset on main clone
    │
PostToolUse (guard-main-revert.sh)
    │
    ├─ revert-dirty-clone.sh     # auto-revert writes, commits, branch switches
    └─ guard-branch-pin.sh post  # pin main worktree back to default branch
    │
Stop (verify-workflow.sh)
    │
    ├─ verify-subagent-nudge.sh  # nudge when 2+ file writes without subagents
    ├─ verify-clean-main.sh      # warn about tracked changes on main clone
    └─ verify-parse-failure.sh   # nudge when tool calls fail arg validation
```

## Core Files

| Script | Role |
|---|---|
| `lib.sh` | Shared constants, git helpers, hook I/O parsing, output helpers, repo allowlist |
| `guard-main-pre.sh` | PreToolUse coordinator: runs qualifier, worktree-branch, branch-pin, main-clone |
| `guard-main-revert.sh` | PostToolUse coordinator: runs revert-dirty-clone + branch-pin post |
| `verify-workflow.sh` | Stop hook: subagent nudge, dirty main check, parse-failure detection |
| `guard-branch-pin.sh` | Pin main worktree to default branch (pre: deny; post: auto-revert) |
| `guard-main-clone.sh` | Block mutating git verbs on immutable clone |
| `guard-worktree-branch.sh` | Deny commit/push on default branch inside worktrees |
| `revert-dirty-clone.sh` | Auto-revert file writes, commits, branch switches on main clone |
| `verify-clean-main.sh` | Stop hook: warn about tracked changes on main clone (once/session) |
| `verify-parse-failure.sh` | Stop hook: nudge on arg-validation failures (scans transcript) |
| `verify-subagent-nudge.sh` | Stop hook: nudge on 2+ file writes without subagents |
| `qualify-tool-input.sh` | Auto-qualify bare tool names, fill missing `description` |
| `hook-allowlist.txt` | Opt-in manifest: one absolute path per line; missing = allow all |
| `worktree-enforce.json` | Hook config wiring all the above |

## Hook Configuration (worktree-enforce.json)

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "write|search_replace|create_file|run_terminal_command|spawn_subagent|use_tool",
        "hooks": [{"type": "command", "command": "~/.hermes/scripts/guard-main-pre.sh", "timeout": 5}]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "write|search_replace|create_file|spawn_subagent|use_tool",
        "hooks": [{"type": "command", "command": "~/.hermes/scripts/guard-main-revert.sh", "timeout": 5}]
      },
      {
        "matcher": "run_terminal_command",
        "hooks": [{"type": "command", "command": "~/.hermes/scripts/guard-main-revert.sh", "timeout": 5}]
      }
    ],
    "Stop": [
      {
        "hooks": [{"type": "command", "command": "~/.hermes/scripts/verify-workflow.sh", "timeout": 60}]
      }
    ]
  }
}
```

## Installation Procedure

Hermes and Grok use **different hook systems** — installing the scripts
without re-wiring the config does nothing:

- **Grok**: hook JSON file in `~/.grok/hooks/` (`worktree-enforce.json`)
  with `PreToolUse`/`PostToolUse`/`Stop` events; payloads use
  `{toolName, toolInput, toolResult, cwd, workspaceRoot, ...}`.
- **Hermes**: there is no hooks JSON dir. Shell hooks are declared in the
  profile's `config.yaml` `hooks:` block via
  `hermes config set --force 'hooks.<event>' '<JSON array>'` (events:
  `pre_tool_call`, `post_tool_call`, `pre_verify`, ...). Payloads use
  `{hook_event_name, tool_name, tool_input, result, cwd, session_id,
  extra}`. Consent is per-profile: write the (event, command) approvals
  into `<profile home>/shell-hooks-allowlist.json` (approval at the TTY
  prompt does the same). Verify with `hermes hooks list` and
  `hermes hooks doctor`. Hooks only register at process start — restart
  or start a new session for the wiring to take effect.

1. **Copy all scripts** to `~/.hermes/scripts/` (or `~/.grok/scripts/` for Grok).
   Keep them at the top-level user home, never inside
   `~/.hermes/hermes-agent/` (upstream, read-only).
2. **Make executable**: `chmod +x ~/.hermes/scripts/*.sh`
3. **Wire the config for the target harness** (see above): Grok gets the
   `worktree-enforce.json` hook file; Hermes gets the `hooks:` block in
   `config.yaml`. Grok's JSON is NOT a Hermes concept — do not copy it
   to `~/.hermes/hooks/`.
4. **Edit `hook-allowlist.txt`** to include the repos where guards should be active:
   ```
   /home/raka/.hermes
   /home/raka/orca/workspaces/
   /home/raka/projects/
   ```
5. **Test each hook** with sample payloads (see test examples below) and run
   `hermes hooks doctor` (Hermes) to check exec bit, allowlist entries,
   script-mtime drift, and synthetic-payload validity.

## Test Payloads

```bash
# Allow: read-only git status
cd ~/.hermes && echo '{"toolName": "run_terminal_command", "toolInput": {"command": "git status", "description": "check status"}, "cwd": "/home/raka/.hermes", "workspaceRoot": "/home/raka/.hermes", "sessionId": "test"}' | ~/.hermes/scripts/guard-main-pre.sh
# → exit 0, no output

# Deny: git commit on main clone
echo '{"toolName": "run_terminal_command", "toolInput": {"command": "git commit -m test", "description": "commit"}, "cwd": "/home/raka/.hermes", "workspaceRoot": "/home/raka/.hermes", "sessionId": "test"}' | ~/.hermes/scripts/guard-main-pre.sh
# → exit 2, deny JSON with Orca worktree instructions

# Deny: file write to main worktree
echo '{"toolName": "write", "toolInput": {"file_path": "/home/raka/.hermes/test.txt", "content": "test"}, "cwd": "/home/raka/.hermes", "workspaceRoot": "/home/raka/.hermes", "sessionId": "test"}' | ~/.hermes/scripts/guard-main-pre.sh
# → exit 2, deny JSON

# Auto-qualify: codegraph_explore → codegraph__codegraph_explore
echo '{"toolName": "use_tool", "toolInput": {"tool_name": "codegraph_explore", "tool_input": {}}, "cwd": "/home/raka/.hermes", "workspaceRoot": "/home/raka/.hermes", "sessionId": "test"}' | ~/.hermes/scripts/guard-main-pre.sh
# → exit 0, tool rewrite JSON

# Stop hook: clean repo → no nudge
echo '{"reason": "end_turn", "sessionId": "test", "workspaceRoot": "/home/raka/.hermes", "stopHookActive": false, "subagentType": ""}' | ~/.hermes/scripts/verify-workflow.sh
# → exit 0, no output

# PostToolUse: branch switch reverted
echo '{"toolName": "run_terminal_command", "toolInput": {"command": "git checkout -b test", "description": "switch"}, "toolResult": {"exit_code": 0}, "cwd": "/home/raka/.hermes", "workspaceRoot": "/home/raka/.hermes", "sessionId": "test", "timestamp": "2026-10-12T05:12:00Z"}' | ~/.hermes/scripts/guard-main-revert.sh
# → exit 0, additionalContext JSON with reverted files list
```

## Adapting to a New Agent

When porting to a new agent (e.g., Grok → Hermes):

1. **Replace paths/constants in `lib.sh`**:
   - `GROK_HOME` → `HERMES_HOME` (or agent-specific home)
   - `GROK_WORKSPACE_ROOT` → `HERMES_WORKSPACE_ROOT`
   - State directories: `/tmp/grok-*` → `/tmp/hermes-*`
   - Transcript path: `$GROK_HOME/sessions/...` → `$HERMES_HOME/sessions/...`

2. **Bridge the payload wire shape in `lib.sh` `read_hook_input()`**, not in
   each guard script. Hermes shell-hook stdin
   `{tool_name, tool_input, result, cwd, session_id, extra}` must be mapped
   onto the Grok shape `{toolName, toolInput, toolResult, ...}` plus tool-name
   mapping (`terminal` → `run_terminal_command`, `patch` →
   `search_replace`, `write_file` → `write`), because every guard matches on
   `TOOL_NAME` strings. Pass native payloads through untouched, and
   republish the normalised JSON as `INPUT` — downstream scripts re-read
   `$INPUT` with their own jq expressions, so they see the Grok shape too.
   (See `references/hermes-shell-hooks.md`.)

3. **Fix the allowlist gate fallback**: `hook_repo_allowed` must resolve the
   workspace from values `read_hook_input` actually populated
   (`WORKSPACE_ROOT` → `OPERATING_DIR` → agent home). A gate that reads an
   env var nobody exports (e.g. `${HERMES_WORKSPACE_ROOT:-}`) is silently
   fail-open — the manifest never gates and the guards can never deny.

4. **Update `hook-allowlist.txt`** with the new agent's repo paths

5. **Wire the new agent's hook config** (Grok: `worktree-enforce.json`;
   Hermes: per-profile `hooks:` block in `config.yaml` +
   `shell-hooks-allowlist.json` consent, all profiles the guards must
   protect). Registering the scripts in only one profile is the classic
   gap — every profile runs its own `config.yaml`.

6. **Preserve all git logic** — the directory resolution, reflog verification,
   worktree exemption, and multi-repo broadening are agent-agnostic

## Key Design Decisions (Pitfalls to Preserve)

- **Fail-open manifest**: missing/empty `hook-allowlist.txt` allows everything.
  Guards are opt-in per repo, not opt-out. This prevents breaking unrelated work.
- **Reflog verification for commits**: `did_fresh_commit_happen()` checks the
  reflog subject (`commit: msg`) and entry timestamp (±120s grace) before
  reverting. A command merely *mentioning* `git commit` must not trigger a reset.
- **Effective directory resolution**: `effective_git_dir()` resolves
  `git -C <dir>` > `cd <dir>` > `CWD` so wrapped commands (`sh -c "git -C ..."`)
  are handled. All guards share this logic via `lib.sh`.
- **Orca worktree exemption**: `in_worktree_path()` checks `~/orca/workspaces/`.
  Any path under it is exempt from main-clone guards. Worktrees have their
  own policy (guard-worktree-branch.sh).
- **Broadened multi-repo (2026-10-10)**: `in_main_clone_under_home()` guards
  ANY git repo under `$HOME` whose toplevel is not an Orca worktree — not just
  the agent's home directory. `repo_toplevel()` walks up to find the repo root.
- **State files in `/tmp`**: Per-session logs (`write-nudge`, `parse-failure`,
  `dirty-fired`) use `$SESSION_ID` as key. Cleaned up by Stop hook.
- **Stop hook fires once per event**: `verify-workflow.sh` blocks with a notice,
  then resets the nudge log so the next turn starts fresh. `STOP_HOOK_ACTIVE`
  prevents double-block in the same turn.
- **Parse-failure anchor**: `verify-parse-failure.sh` anchors on
  `startswith("Failed to parse arguments for tool ")` to avoid matching
  quoted text in reasoning or fixtures.
- **Auto-qualify before deny**: `qualify-tool-input.sh` runs first in
  `guard-main-pre.sh`. It rewrites `codegraph_explore` →
  `codegraph__codegraph_explore` and fills missing `description` for
  `run_terminal_command` so the call reaches the real guards instead of being
  dropped at argument-validation.

## Orca Worktree Workflow (Enforced by Guards)

```bash
# 1. Create worktree from main clone
orca worktree create --repo path:/home/raka/.hermes --name <task> --agent <id> --prompt '<task>' --no-parent --json

# 2. Work in the worktree (spawn_subagent or terminal)
spawn_subagent(cwd="<worktree path>", prompt="...")

# 3. Commit on feature branch (allowed by guard-worktree-branch.sh)
git checkout -b worktree/<name>
git commit -m 'feat: ...'
git push origin <branch>

# 4. Open PR → CI passes → auto-merge → main updated
```

The guards make deviation impossible: commits/pushes on `main` in the main
clone are denied; commits/pushes on `main` in a worktree are denied; file
writes to the main clone are denied and reverted.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Hooks don't fire | Repo not in `hook-allowlist.txt` | Add repo path to allowlist |
| `command not found` | Scripts not executable | `chmod +x ~/.hermes/scripts/*.sh` |
| Legitimate commit reverted | Reflog check failed | Check `did_fresh_commit_happen()` grace window (120s) |
| Worktree commands denied | `effective_git_dir()` wrong | Verify `git -C` / `cd` capture in `read_hook_input()` |
| Stop hook blocks repeatedly | `STOP_HOOK_ACTIVE` not reset | Ensure `verify-workflow.sh` resets nudge log |
| Parse failures not caught | Transcript path wrong | Check `$HERMES_HOME/sessions/*/$SESSION_ID/chat_history.jsonl` |
| Guards never deny, allowlist ignored | `hook_repo_allowed` gate reads an unset env var → empty workspace → fail-open return 0 | Make the gate fall back to the payload-resolved `WORKSPACE_ROOT`/`OPERATING_DIR`; test with a non-allowlisted CWD and expect silent allow, with an allowlisted CWD expect exit 2 |
| Hermes profile uses old/no hooks | Shell hooks register per profile from its own `config.yaml`, at process start only | `hermes -p <name> config set --force 'hooks.<event>' ...` per profile + per-profile `shell-hooks-allowlist.json`; then restart that surface; `hermes -p <name> hooks doctor` to verify |
| Hermes hooks show "not allowlisted" / get skipped on non-TTY runs | No consent recorded for the (event, command) pair | Pre-approve in `shell-hooks-allowlist.json` (entries carry `event`, `command`, `script_mtime_at_approval`), or set `hooks_auto_accept: true` / run once with `--accept-hooks` |
| New files under `~/.hermes/scripts/` vanish after a hook run | A guard's post-hook `git clean`/revert ran inside a tracked `~/.hermes` repo | Keep allowlisted guard targets out of the tracked home, or make the revert scripts exempt their own script/allowlist paths; verify with `git -C ~/.hermes status` |
| Upstream code modified by mistake | Scripts installed into `~/.hermes/hermes-agent/` (upstream checkout) | User home layer only: `~/.hermes/scripts/` + `config.yaml`; confirm `git -C ~/.hermes/hermes-agent status` stays clean |

## Related Workflows

- `orca-cli` — create/manage Orca worktrees
- `hermes-agent` — Hermes configuration, profiles, skills
- `local-ci` / `setup-ci-quality-gates` — CI that mirrors these gates
- `systemd-headless-service` — run agent as 24/7 service (hooks still apply)

## References

See `references/hook-payload-schema.md` for the JSON input/output schemas each
hand expects and emits (Grok wire shape; the Hermes shell-hook wire shape and
registration procedure are in `references/hermes-shell-hooks.md`).
