# Step 5: Design notes (module/persona review)

## Why module mode does not collect a diff

Diff modes (main, local, branch, PR, stack) review a change set against a base. Module mode reviews the **current state** of a directory in place — there is no base to diff against. Each subagent lists the module's tracked files via `git ls-files <path>` and `read_file`s them. A diff would answer "what changed"; module mode answers "is this module sound."

## Why parallel fan-out, not sequential

Ten personas running sequentially means ten full module-reads, each with its own context window. The personas are independent — no persona's findings feed another's. Running them in parallel (`background: true` on every `spawn_subagent`) cuts wall-clock time by roughly the fan-out factor with no correctness cost: the shared working tree is read-only for all ten, and each writes to its own per-persona file.

## Why per-persona file names embed BOTH the REVIEW_ID and the persona

`grok-review-<REVIEW_ID>-<persona>.md` prevents collision when two module reviews run in the same scratch directory (different `REVIEW_ID`), and keeps a ten-persona run from clobbering its own siblings (different persona). The `REVIEW_ID` alone is not enough; the persona name alone is not enough.

## Why ERROR-not-abort

A single persona subagent can fail (context window overflow on a very large module, a malformed persona file, a transient subagent error). The other nine personas' findings are still useful and cost nothing to keep. Aborting the whole run because one lens failed would throw away nine successful reviews. The orchestrator records the failed persona as `ERROR` with the exact error text and aggregates the rest.

## Why `--all` and the bare form are equivalent

The bare form (`/review modules/skills` with no flags) and `--all` select all 10 personas. The bare form is the common case ("just review this module"); `--all` is the explicit form for scripts or when the user wants to be unambiguous. They produce identical runs.

## Why no GitHub posting

Module mode has no PR to post to. Findings land in per-persona review files plus a single summary file on disk. If the user wants the findings posted to a PR, that is a separate workflow (a diff mode or a manual `gh api` call) and is out of scope for this skill.
