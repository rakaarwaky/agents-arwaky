# 4-Lens Diff Sweep — Execution Model and Lenses

Run when the request is diff-scoped (step 0 captured a diff). Four focused reviewers
run in parallel; each deeply searches the codebase for a single class of problem
without diluting its attention across all four. Four narrow reviewers beat one broad
reviewer.

## Execution model

- **Preferred:** subagent batch fan-out — pass all four reviewer tasks in one batch so
  they run concurrently. Four is the right fan-out; it is within the default
  `max_concurrent_children` budget. **Never fan out wider than 4** — more reviewers means
  more cost and more conflicting suggestions to reconcile, not better coverage.
- **Fallback:** if subagents are unavailable (leaf agent, delegation disabled, budget
  exhausted), do **not** skip the review or drop angles. Work through all four reviewer
  angles yourself, sequentially, in this context — same search standards, same finding
  format. State clearly in the final summary that this was a single-pass inline review,
  not the parallel fan-out.

**Give every reviewer the complete diff** (not fragments — cross-file issues hide in the
gaps) plus the absolute repo path so they can search the wider codebase. Each reviewer gets
`terminal`, `file`, and `search` toolsets so it can `git`, `read_file`, and grep.

## The four lenses

Full prompt text for each reviewer lives in [`reviewer-prompts.md`](reviewer-prompts.md).

- **Reviewer 1 — Reuse.** Find code that duplicates functionality already in the codebase
  (utilities, shared helpers, canonical patterns). Flag new functions that duplicate existing
  ones; hand-rolled logic an existing utility already does. Name the existing thing and where
  it lives.
- **Reviewer 2 — Quality.** Redundant state, parameter sprawl, copy-paste-with-variation,
  leaky abstractions, stringly-typed code, deeply nested conditionals, AI-generated slop
  patterns. For each, give the concrete refactor.
- **Reviewer 3 — Efficiency.** Unnecessary work, N+1 patterns, missed concurrency, hot-path
  bloat, TOCTOU anti-patterns, memory/listener leaks, overly broad reads, silent failures
  (swallowed exceptions). For each, give the concrete fix and why it is faster or safer.
- **Reviewer 4 — Altitude.** Changes implemented at the wrong depth — band-aids layered over
  shared infrastructure instead of fixes to the infrastructure itself. Special-case branches on
  generic paths, workarounds stacked on earlier workarounds. Identify the underlying mechanism
  being dodged and describe the deeper fix.

## Evidence standard

- **Chesterton's Fence:** before flagging anything for removal, run `git blame` on the line
  to understand why it exists. If the original purpose cannot be determined, mark
  `confidence: low` — do not guess.
- **Reviewers search, they do not guess.** A reuse finding with no pointer to the existing
  utility ("there's probably a helper for this") is noise. Require `file:line` evidence;
  drop findings that lack it.
- **Finding format** (the `cost` field is mandatory — a finding that cannot articulate what
  the problem actually costs is probably a nit and gets dropped):

```text
file:line → problem → cost (what's duplicated/wasted/harder to maintain) → suggested fix | confidence: high/medium/low | risk: SAFE/CAREFUL/RISKY
```

## Sweep pitfalls

- **Over-trusting dead-code tools.** `knip`, `ts-prune`, and `depcheck` flag exports that
  **are** used dynamically (string-based imports, reflection). Always grep for the symbol
  name before removing — a clean tool report is not proof.
- **Removing "unnecessary" error handling.** An empty catch block or ignored error might be
  intentional — the error is expected and benign in that context. Flag it, don't remove it;
  let the human decide.
- **Not every special case is a band-aid.** Compat shims, staged migrations, and isolation
  layers around vendored code look like altitude violations but are deliberate design. Check
  `git blame` and surrounding comments before flagging; when the intent is unclear, mark
  `confidence: low`.
- **Renaming without checking public contracts.** Export names, API route paths, DB column
  names, and config keys are contracts — even if the name is bad, renaming breaks consumers.
  Tag public-contract changes as RISKY; never auto-rename them.

## Completion

- All four lenses produced findings in the mandatory finding format; every flagged item has a `git blame` check or `confidence: low` marker.
