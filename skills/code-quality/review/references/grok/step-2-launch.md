# Step 2: Launch reviewer subagents in parallel

Spawn one reviewer subagent per entry in `personas`, all with `background: true`, all with `subagent_type: "general-purpose"`. Each subagent's `description` is `[<persona-name>] module <target>`. Prepend that persona's instructions to the prompt (the persona loading and injection procedure is defined in this file, "For each selected persona").

## Invocation examples

| Command | Behavior |
|---|---|
| `/review modules/skills` | review that module with all 10 personas in parallel |
| `/review modules/skills --all` | same as above (explicit) |
| `/review modules/skills --qa-engineer` | that module with only the QA Engineer persona |
| `/review modules/skills --qa-engineer --security-engineer` | that module with both the QA Engineer and Security Engineer personas |
| `/review internal/lint-arwaky --software-architect` | a specific crate with one persona |

Argument parsing (the persona roster, the `--all` handling, and the rejection
messages) lives in [step-0-argument-parsing.md](step-0-argument-parsing.md).

## Persona resolution

For each selected persona:

1. Pick the first path that exists: `~/.grok/personas/<name>.toml`, then the repo fallback `<dirname of SKILL.md>/../../../personas/<name>.toml`.
2. Read the file with `read_file`.
3. Parse with `python3 -c "import tomllib,sys; print(tomllib.load(open(sys.argv[1],'rb'))['subagents']['personas']['<name>']['instructions'])" <path>` and take the `instructions` value under the `[subagents.personas.<name>]` table (ignore the `[[subagents.personas.<name>.inputs]]` and `[[...outputs]]` arrays).
4. Store that body as `<name>_persona_instructions`.

All 10 personas when no persona flag is given (the bare form) or when `--all` is given; exactly the selected personas when one or more persona flags are given.

## Prompt template

Each subagent is seeded with exactly one persona. Build its prompt from that persona's `instructions`, then this module context. Substitute per-persona values plus the resolved absolute `scratch_dir`, `PYTHON`, `HOST_PY`, `REVIEW_ID`, and `target`.

```text
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

## Spawn notes

- `description` for every subagent is `[<persona-name>] module <target>` — the bracketed prefix is parsed by the pager's subagent label renderer.
- Subagents are launched with `background: true` and `subagent_type: "general-purpose"`.
- All subagents share one working tree; the per-persona filenames embed BOTH the `REVIEW_ID` and the persona name so they never collide.
- No diff collection: module mode reviews the current state of the files, not a change set.

**Do not pass `capability_mode: read-only`.** It removes the `write` tool that each subagent needs to write its per-persona review file. Enforce source read-only behavior in the prompt instead.

## Waiting and errors

After all launches, call `get_command_or_subagent_output` for all task IDs and wait for every subagent. Record a failed subagent as `ERROR` for that persona and continue aggregating the rest — one failed persona does not abort the run.

Report progress: "All <N> reviewers complete. Aggregating findings..."
