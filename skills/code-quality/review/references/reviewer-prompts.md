# Reviewer subagent prompts

## Module template (one subagent per persona)

Each subagent is seeded with exactly one persona. Build its prompt from that persona's `instructions`, then this module context. Substitute per-persona values plus the resolved absolute `scratch_dir`, `PYTHON`, `HOST_PY`, `REVIEW_ID`, and `target`.

```
<persona_instructions>

---

You are reviewing a module in place. No diff — read the current files.

Module path: <absolute target>
REVIEW_ID: <REVIEW_ID>
Persona: <persona-name>
Scratch directory: <absolute scratch_dir>
Python: <absolute PYTHON>
Host helper: <absolute HOST_PY>

Treat the four values above as already-resolved absolute paths. Inline them in every command. Do not rely on shell variables across `run_terminal_command` calls.

The module's tracked file list is at: <files_file>

Steps:
1. Read the file list. It is the scope — review only these files.
2. `read_file` each file in the list. Prefer full-file reads; use `grep` to locate the exact symbols or call sites before flagging anything. Do not open files that are not in the list.
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

### Issue 2 -- Severity: suggestion
- File: path/to/file.ext:LINE
- Description: ...
- Suggestion: ...
- Status: open

Severity must be one of: bug, suggestion, nit. Each issue's Status field must
be set to "open" (as shown above). The File line must reference a line in the
current source.

If the module is genuinely sound from this persona's lens and you have no
issues, write the Summary and an empty `## Issues` section (or omit the Issues
section entirely). Do not invent issues to fill space.

Parallel-safety constraints:
- Run only read-only git commands. Never checkout, switch, reset, stash, or
  fetch. Do not modify the worktree, index, or HEAD.
- Write only <review_file>. No other files. No cleanup of other paths.

Report: the path to <review_file>, then a one-line count —
"<persona>: X bugs, Y suggestions, Z nits."
On any hard failure, report ERROR with the exact error text.
```

## Notes

- `description` for every subagent is `[<persona-name>] module <target>` — the bracketed prefix is parsed by the pager's subagent label renderer.
- Subagents are launched with `background: true` and `subagent_type: "general-purpose"`.
- All subagents share one working tree; the per-persona filenames embed BOTH the `REVIEW_ID` and the persona name so they never collide.
- No diff collection: module mode reviews the current state of the files, not a change set.
