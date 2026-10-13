---
name: git-hook-probing
description: Probe git hooks without dirtying the repo.
version: 1.0.0
author: rakaarwaky
license: MIT
metadata:
  tags:
    - git-hooks
    - pre-commit
    - pre-push
    - repo-verification
    - hook-testing
  hermes:
    tags:
      - git-hooks
      - pre-commit
      - pre-push
      - repo-verification
      - hook-testing
    related_skills:
      - agent-worktree-hooks
      - qwen-web-arwaky-dev
  triggers:
    - test git hook
    - verify pre-commit fires
    - dirty main to trigger hook
    - check hook message delivery
---

## When to Use

The user wants to confirm their git hooks fire, block, or deliver a message — without leaving a commit or dirty tree behind. Typical asks: "test my hook protection on main", "check whether the pre-commit scanner blocks", "make the repo dirty to trigger the guard".

## Locate the real hooks path first

- `.git` may be a **file**, not a directory (gitdir pointer). Read it to find the actual git dir, then check `<gitdir>/hooks/` and `git config core.hooksPath` (repo-local and global).
- In a nested repo (parent has `.git/modules/<name>`), the parent's own `.git/hooks/` may hold the active pre-commit — a module-level dir can be empty while the parent-level hook is the one that runs. Check **both** levels before concluding "no hooks".
- The active pre-commit may be a secret scanner (sk-/ghp_/AKIA patterns, forbidden env files). It blocks content patterns, not branch writes — set expectations accordingly.

## Pitfalls

- **Never fabricate a gitdir link.** Creating a dir with a `.git` file (`gitdir: .../modules/<name>`) makes git treat the parent as a submodule. `git status` then loops `git status --porcelain=2` until `Argument list too long`, and subsequent `git add`/`commit` silently no-op. Delete the probe dir and `git reset` in the real repo before continuing.
- **Never create test branches on the protected/default branch.** The guard system pins main; work in-place instead.
- **The agent receives no "message" from git hooks.** Hooks print to stdout, which the agent sees only as tool output. If the user expected a system-reminder-style message, tell them: the hook ran, its stdout is in the tool result, and no message was injected. Point at the path where the hook writes logs if they want durable evidence.

## In-place probe recipe

```bash
cd <repo> && touch probe.txt && git add probe.txt
git commit -m "probe: test pre-commit"   # empty/harmless content passes a secret-scanner hook
git reset --hard <base-sha>             # undo
```

To test the rejection path: put a `Bearer`/`sk-`/`AKIA` string in the probe file content before committing — the hook should print its block message and exit 1, leaving no commit. Confirm with `git log --oneline -1` that base is still HEAD.

After any probe: `git status --short` must be empty and `git log -1` must match the base SHA. Clean up any stray branches created during the probe (`git branch -D <probe-branch>`).

## Report shape

Lead with whether the hook fired and what it output (quote the key line), whether a commit landed or was blocked, and that the repo was restored to base. If nothing was received by the agent, say so plainly and explain that git hooks do not inject messages into agent context.

## Distinguish the protection layer being tested

Ask which layer the user means before concluding: (a) a **git hook** (`.git/hooks/` or `core.hooksPath` — secret scanner, branch protection) prints to stdout and **never** injects a message into agent context; or (b) the **Hermes guard-hook** system (`~/.hermes/scripts/`, wired via `hooks:` in profile `config.yaml`) which **does** nudge the agent. The user's "hook protection" is usually the latter.

- **Guard nudge = soft revert + message, not a hard block.** PreToolUse hard-blocks only specific mutating verbs (`exit 2`). A write/commit that the pre guard *allows* runs, then PostToolUse (`revert-dirty-clone.sh`) reverts it and emits `emit_post_context_json` → `hookSpecificOutput.additionalContext`, which Hermes injects as a message into the next model turn. So the agent **should** receive the nudge text.
- If a `write_file`/`patch` returns `Blocked by shell hook`, that is a **PreToolUse deny** — the write never happened and no post nudge fired. To exercise the nudge path, trigger a mutation the pre guard allows (e.g. `git commit` via terminal on the pinned clone), then confirm it was soft-reset and the nudge text arrived.
- **The agent cannot self-prove a hook fired.** The only operator-side evidence is the guard's audit log: `$HOOK_AUDIT_LOG` (default `~/.hermes/logs/hook-audit.log`), one JSON line per gated event (allow and deny). The agent never sees this log. A **frozen audit log after a trigger = the post hook is not running** — check `hermes hooks doctor` (allowlist entry, mtime drift, exec bit) before assuming the guard is dead.
- See the `agent-worktree-hooks` and `hermes-shell-hooks` skills for the full guard architecture and the audit-log/doctor workflow.
