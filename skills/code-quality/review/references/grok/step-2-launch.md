# Step 2: Launch reviewer subagents in parallel

Spawn one reviewer subagent per entry in `personas` (1–3, set by Step 0 auto-selection), all with `background: true`, all with `subagent_type: "general-purpose"`. Each subagent's `description` is `[<persona-name>] <mode> <target>`.

## Invocation examples

| Command | Behavior |
|---|---|
| `/review commit` | review the last commit; agent auto-selects 1–3 personas from the diff signal |
| `/review uncommit` | review uncommitted working-tree changes; agent auto-selects personas |
| `/review pr 48` | review the diff of PR #48; agent auto-selects personas from the diff |
| `/review path modules/skills` | review the current content of that directory; agent auto-selects personas |

Argument parsing and the persona auto-selection rules live in [step-0-argument-parsing.md](step-0-argument-parsing.md).

## Persona resolution

For each selected persona (1–3, chosen by the orchestrator in Step 0 based on the target's content):

1. Pick the first path that exists: `~/.grok/personas/<name>.toml`, then the repo fallback `<dirname of SKILL.md>/../../../personas/<name>.toml`.
2. Read the file with `read_file`.
3. Parse with `python3 -c "import tomllib,sys; print(tomllib.load(open(sys.argv[1],'rb'))['subagents']['personas']['<name>']['instructions'])" <path>` and take the `instructions` value under the `[subagents.personas.<name>]` table (ignore the `[[subagents.personas.<name>.inputs]]` and `[[...outputs]]` arrays).
4. Store that body as `<name>_persona_instructions`.

## Prompt template

Each subagent is seeded with exactly one persona. Build its prompt from that persona's `instructions`, then the mode-specific context. Substitute per-persona values plus the resolved absolute `scratch_dir`, `PYTHON`, `HOST_PY`, `REVIEW_ID`, `mode`, `target`, `files_file`, and (for diff modes) `diff_file`.

### Diff-mode template (`commit`, `uncommit`, `pr`)

```text
<persona_instructions>

---

You are reviewing a change set. Read the diff first, then open any source file
you need for context.

Mode: <mode>          (one of commit | uncommit | pr)
Target: <target>      (commit summary, or "uncommitted changes", or "PR #N")
REVIEW_ID: <REVIEW_ID>
Persona: <persona-name>
Scratch directory: <absolute scratch_dir>
Python: <absolute PYTHON>
Host helper: <absolute HOST_PY>

Treat the values above as already-resolved absolute paths. Inline them in every
command. Do not rely on shell variables across `run_terminal_command` calls.

The unified diff is at: <diff_file>
The changed-file list is at: <files_file>

Steps:
1. Read the diff file (<diff_file>). It is the primary scope — review only the
   changes shown. The `+` lines are new code; the `-` lines are removed code.
2. Open the full source files in <files_file> where the diff is insufficient for
   context (e.g. to understand surrounding logic, function signatures, or
   call sites). Prefer `read_file`; use `grep` to locate specific symbols.
3. Write structured findings to: <review_file>   (i.e. <scratch_dir>/grok-review-<REVIEW_ID>-<persona>.md)

Format:

## Summary

<2 to 4 sentences: what this change does, whether it looks sound from the
<persona-name> lens, the dominant risk areas in the diff.>

## Issues

### Issue 1 -- Severity: bug
- File: path/to/file.ext:LINE
- Description: <what is wrong in the changed lines>
- Suggestion: <how to fix>
- Status: open

Severity must be one of: bug, suggestion, nit. Each issue's Status field must
be set to "open". The File line must reference a line in the **new** version of
the file (post-diff). Do not flag pre-existing issues that this change does
not touch.

If the change set is genuinely sound from this persona's lens and you have no
issues, write the Summary and an empty `## Issues` section. Do not invent issues.

Parallel-safety constraints:
- Run only read-only git commands. Never checkout, switch, reset, stash, or
  fetch. Do not modify the worktree, index, or HEAD.
- Write only <review_file>. No other files. No cleanup of other paths.

Report: the path to <review_file>, then a one-line count —
"<persona>: X bugs, Y suggestions, Z nits."
On any hard failure, report ERROR with the exact error text.
```

### Path-mode template (`path`)

```text
<persona_instructions>

---

You are reviewing a module in place. No diff — read the current files.

Mode: path
Target: <target>       (absolute file or directory path)
REVIEW_ID: <REVIEW_ID>
Persona: <persona-name>
Scratch directory: <absolute scratch_dir>
Python: <absolute PYTHON>
Host helper: <absolute HOST_PY>

Treat the values above as already-resolved absolute paths. Inline them in every
command. Do not rely on shell variables across `run_terminal_command` calls.

The review-scope file list is at: <files_file>

Steps:
1. Read the file list. It is the scope — review only these files.
2. `read_file` each file in the list. Prefer full-file reads; use `grep` to
   locate the exact symbols or call sites before flagging anything. Do not
   open files that are not in the list.
3. Write structured findings to: <review_file>   (i.e. <scratch_dir>/grok-review-<REVIEW_ID>-<persona>.md)

Format:

## Summary

<2 to 4 sentences: what this module does, whether it looks sound from the
<persona-name> lens, the dominant risk areas.>

## Issues

### Issue 1 -- Severity: bug
- File: path/to/file.ext:LINE
- Description: <what is wrong>
- Suggestion: <how to fix>
- Status: open

Severity must be one of: bug, suggestion, nit. Each issue's Status field must
be set to "open". The File line must reference a line in the current source.

If the module is genuinely sound from this persona's lens and you have no
issues, write the Summary and an empty `## Issues` section. Do not invent issues.

Parallel-safety constraints:
- Run only read-only git commands. Never checkout, switch, reset, stash, or
  fetch. Do not modify the worktree, index, or HEAD.
- Write only <review_file>. No other files. No cleanup of other paths.

Report: the path to <review_file>, then a one-line count —
"<persona>: X bugs, Y suggestions, Z nits."
On any hard failure, report ERROR with the exact error text.
```

## Spawn notes

- `description` for every subagent is `[<persona-name>] <mode> <target>` — the bracketed prefix is parsed by the pager's subagent label renderer.
- Subagents are launched with `background: true` and `subagent_type: "general-purpose"`.
- All subagents share one working tree; the per-persona filenames embed BOTH the `REVIEW_ID` and the persona name so they never collide.
- **Do not pass `capability_mode: read-only`**. It removes the `write` tool that each subagent needs to write its per-persona review file. Enforce source read-only behavior in the prompt instead.

## Waiting and errors

After all launches, call `get_command_or_subagent_output` for all task IDs and wait for every subagent. Record a failed subagent as `ERROR` for that persona and continue aggregating the rest — one failed persona does not abort the run.

Report progress: "All <N> reviewers complete. Aggregating findings..."
