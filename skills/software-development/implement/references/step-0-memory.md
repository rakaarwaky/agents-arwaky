# Step 0 Memory Retrieval (Past Issues Briefing)


Before launching the implementer, attempt to load past issue patterns from the workspace memory file. This briefing is injected into both the implementer and reviewer prompts to help avoid recurring issues.

The memory file is **workspace-scoped** and lives under `$HOME/.grok/implement-memory/`, keyed by a stable workspace id derived in this order:

1. Canonicalised `git config remote.origin.url` (SSH and HTTPS variants of the same upstream collapse onto one id, with or without the `.git` suffix).
2. Absolute path of the main `.git` directory (`git rev-parse --git-common-dir`) for repos with no remote.
3. Absolute path of cwd as a last-ditch fallback for non-git workspaces.

The `memory.py` helper at `<dirname of this SKILL.md>/scripts/memory.py` resolves the path and handles concurrent access via a Python lock (`fcntl.flock` on POSIX, `msvcrt.locking` on Windows; no `flock(1)` shell binary required).

### Resolve the helper path once

The helper script lives at a fixed location **relative to this SKILL.md file**: `<dirname of SKILL.md>/scripts/memory.py`. The orchestrator already knows the absolute path to this SKILL.md file from its system context (the skills list announces each skill's path when it's loaded). Derive the helper path from that, **not** from `$(pwd)` — the skill can be loaded from a workspace-local `.grok/skills/`, the user's home `~/.grok/skills/`, or a bundled `~/.grok/bundled/...` location, and only the SKILL-relative path works in all cases.

Capture it once at the start of the run as **orchestrator state** (a value held in your own working memory):

```
memory_helper_path = dirname(<path-to-this-SKILL.md>) + "/scripts/memory.py"
```

For example, if this SKILL.md is at `/Users/alice/.grok/worktrees/org/repo/.grok/skills/implement/SKILL.md`, then `memory_helper_path` is `/Users/alice/.grok/worktrees/org/repo/.grok/skills/implement/scripts/memory.py`. If this SKILL.md is at `/Users/alice/.grok/skills/implement/SKILL.md`, then `memory_helper_path` is `/Users/alice/.grok/skills/implement/scripts/memory.py`.

**Substitute this absolute path directly** into every helper invocation throughout the run — do not rely on a shell environment variable surviving across `run_terminal_command` calls. All examples below show `${MEMORY_HELPER}` for readability; in practice, inline the absolute `memory_helper_path` value.

**Invoke the helper from the run's worktree after Worktree Isolation: `cd <worktree_path> && "${PYTHON}" "${MEMORY_HELPER}" ...`** (before the worktree exists, the session workspace root is fine). The helper itself is cwd-sensitive only for its workspace-id derivation: it runs `git config --get remote.origin.url` and `git rev-parse --git-common-dir` in the cwd, so cwd must be inside the repo that owns the task — the worktree guarantees that even when the session sits in a superproject workspace. Never `cd` to the helper's own directory before invoking it (especially relevant when the skill is loaded from `~/.grok/skills/`, where `cd`-ing to the helper would put cwd outside any workspace and the workspace-id would fall back to that home-dir cwd).

### Read Path

1. Run `"${PYTHON}" "${MEMORY_HELPER}" snapshot` via `run_terminal_command` and capture stdout. The helper prints structured JSON — no markdown re-parsing in the orchestrator. The shape is:

   ```json
   {
     "common_issues": [
       {"category": "Error Handling", "description": "Missing null check", "count": 5},
       ...
     ],
     "recent_runs": [
       {"date": "2026-04-23", "description": "\"Add retry logic\"", "body_lines": ["- **Rounds**: 2", "- **Issues**: 7 total (1 bug, 1 suggestion, 5 nits)", "- **Key patterns**: Missing entries in error-type allowlists, incomplete configuration validation", "- **Specializations used**: general"]},
       ...
     ],
     "exists": true
   }
   ```

   Parse the JSON and store the `common_issues` list as `existing_patterns_snapshot` (used in Step 6b). Store the boolean `exists` as `memory_existed_before` (used in the Final Report to decide between "file created" and "file updated" wording). The `recent_runs` array is included in the snapshot for debugging and forward compatibility (parse `.recent_runs` from the JSON yourself; do not invoke `jq`). The orchestrator does not currently consume it. Each entry's `body_lines` are the verbatim markdown bullets (leading `- ` and `**...**` formatting preserved).
2. If the helper exits non-zero (very rare — only happens if `$HOME` is unset and inferable home fails, or if cwd is unreadable), log a brief note, set `past_issues_briefing` to `""`, `existing_patterns_snapshot` to `[]`, `memory_existed_before` to `false`, and proceed to Step 1. Note that a non-git workspace is **not** a failure mode — the helper falls back to a cwd-based id.
3. If `existing_patterns_snapshot` is empty (or `exists` is `false`), set `past_issues_briefing` to `""` and skip the briefing block below.

Do NOT read or write `.grok/implement-issues.md` directly during a /implement run — that legacy path is per-worktree and is no longer used. The helper is the single source of truth for the path.

**One-time migration from the legacy file:** if a user has a populated `.grok/implement-issues.md` from a prior version, its `## Common Issues` and `## Recent Runs` sections use the **same markdown format** documented under [Memory File Format](#memory-file-format) below. To bring that history forward:

1. **From the workspace root** (the same directory where `.grok/implement-issues.md` lives — the workspace-id is derived from the cwd's git context, so running this from `~` or any unrelated directory will write to the wrong workspace's memory file), write `{}` to a temp file and run `"${PYTHON}" "${MEMORY_HELPER}" update --file <that-file>` once to create the workspace-scoped file and its parent directory — `memory.py path` only computes the path, it does not create the directory.
2. Open the printed file path in an editor.
3. Hand-copy the bullets from the legacy file's `## Common Issues` section into the corresponding categories in the new file (preserving the `- description (seen N time(s))` syntax).
4. The helper picks up the entries on the next `update`.

There is no automatic migration.

### Parsing & Formatting

If `existing_patterns_snapshot` is non-empty:

1. Filter to only entries with `count >= 2` (minimum threshold — one-off issues are excluded as they may not represent real patterns).
2. Sort by `count` descending.
3. Take the top 10 entries.
4. Format them into the briefing block and store in `past_issues_briefing`:

```
## Past Issues to Avoid
Based on previous implementation runs, the following patterns commonly cause issues:
1. Missing null/undefined checks on function inputs (seen 5 times)
2. Missing tests for error/edge case paths (seen 8 times)
3. Functions exceeding 50 lines without decomposition (seen 4 times)
4. Magic numbers without named constants (seen 6 times)

Pay special attention to these patterns in your work.
```

(Use `time` for `count == 1`, `times` otherwise. The helper renders both forms identically in the file, so the briefing should match.)

If there are no qualifying entries, set `past_issues_briefing` to `""`.

### Graceful Degradation

If the helper command fails for any reason, set `past_issues_briefing` to `""`, `existing_patterns_snapshot` to `[]`, `memory_existed_before` to `false`, and proceed normally. Never fail the run due to memory retrieval issues — log a brief note and continue.
