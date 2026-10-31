# Scenario: Simplify a Diff (4-Reviewer Sweep)

The merged simplify-code scenario. Trigger: "simplify", "simplify my changes",
"clean up my changes", "review my recent changes".

This is a **cleanup pass, not a bug hunt.** You are improving the quality of
code that already works — removing duplication, flattening needless complexity,
cutting waste, and deepening band-aid fixes. Do not go hunting for
correctness bugs here; that's what the reviewer persona (`review` skill) is
for.

**Core principle:** Four narrow reviewers beat one broad reviewer. Each one
deeply searches the codebase for a single class of problem — reuse, quality,
efficiency, altitude — without diluting its attention across all four. They
run concurrently, so you pay the latency of one review, not four.

## When to Use

- "simplify" / "simplify my changes" / "simplify these changes"
- "review my code" / "review my recent changes" / "clean up my changes"

Optional modifiers — honor them:

- **Focus:** "simplify focus on efficiency" → run only the efficiency
  reviewer (or weight the aggregation toward it). Recognized focuses: `reuse`,
  `quality` (also accepts `simplification`), `efficiency`, `altitude`.
- **Dry run:** "simplify but don't change anything" / "just report" → run the
  four reviewers, present findings, apply NOTHING. Ask before applying.
- **Scope:** "simplify the last commit" / "simplify staged" / "simplify
  src/foo.py" → narrow the diff source accordingly.

Do NOT auto-run this after every edit or tack it onto the end of unrelated
tasks. It costs four subagents' worth of tokens — invoke it only when the
user explicitly asks.

## Process

### Step 1 — Identify the changes

Capture the diff to review. Pick the source by what the user asked for, in
this default order:

```bash
# 1. Default: uncommitted working-tree changes (tracked files)
git diff

# 2. If that's empty, include staged changes
git diff HEAD

# 3. Scoped variants the user may request:
git diff --staged                 # "staged changes"
git diff HEAD~1                    # "the last commit"
git diff main...HEAD              # "this branch" / "my PR"
git diff -- src/foo.py            # specific file(s)
```

If `git diff` and `git diff HEAD` are both empty and there's no git repo or
no changes, fall back to the files the user explicitly named or that were
recently created/edited in this session. If you genuinely can't find any
changed code, say so and stop — there's nothing to simplify.

Capture the full diff text. Note its size: if it's very large (say >2000
changed lines), warn the user that four subagents each carrying the full diff
will be token-heavy, and offer to scope it down (per-directory, per-commit)
before proceeding.

### Step 2 — Launch four reviewers in parallel

Use `delegate_task` **batch mode** — pass all four tasks in one `tasks`
array so they run concurrently. Four is the right fan-out for this pattern;
it's within the `delegation.max_concurrent_children` budget on any default
install.

**No delegation available?** If you can't call `delegate_task` in this
context (you're a leaf subagent, delegation is disabled, or the budget is
exhausted), do NOT skip the review or drop angles. Work through all four
reviewer angles yourself, sequentially, in this context — same search
standards, same finding format. Then say clearly in your final summary that
this was a single-pass inline review, not the parallel fan-out, so the user
knows what actually ran.

Give **every** reviewer the **complete diff** (not fragments — cross-file
issues hide in the gaps) plus the absolute repo path so they can search the
wider codebase. Each reviewer gets `terminal`, `file`, and `search`
toolsets (so they can `git`, `read_file`, and `search_files`/grep).

Tell each reviewer to:

- Search the existing codebase for evidence (don't reason from the diff alone).
- **Apply Chesterton's Fence:** before flagging anything for removal, run
  `git blame` on the line to understand why it exists. If you can't
  determine the original purpose, mark it `confidence: low` — don't guess.
- Report findings as structured output with the concrete cost, confidence,
  and risk:

```text
file:line → problem → cost (what's duplicated/wasted/harder to maintain) → suggested fix | confidence: high/medium/low | risk: SAFE/CAREFUL/RISKY
```

The **cost** field forces each finding to justify itself — a finding that
can't articulate what the problem actually costs is probably a nit.

- **SAFE** = proven not to affect behavior (unused imports, commented-out
  code, pass-through wrappers). Auto-apply these.
- **CAREFUL** = improves without changing semantics (rename local variable,
  flatten nested ternary, extract helper). Apply with test verification.
- **RISKY** = may change behavior or breaks public contracts (N+1
  restructuring, public API rename, memory lifecycle change). Flag for
  human review — do NOT auto-apply.
- Skip nits and style-only churn. Only flag things that materially improve
  the code.

Pass these four goals (drop any the user's focus excludes). The full
reviewer prompts (reuse / quality / efficiency / altitude, verbatim) are in
[`reviewer-prompts.md`](reviewer-prompts.md).

### Step 3 — Aggregate and apply

For the full aggregate-and-apply procedure (merge, dedupe, conflict
resolution order, risk-tier application, verification, summary), see
[`phase3-aggregate.md`](phase3-aggregate.md).

## Pitfalls

- **Don't fan out wider than 4.** More reviewers means more cost and more
  conflicting suggestions to reconcile, not better coverage. The four
  categories cover the space.
- **Give the WHOLE diff to each reviewer.** Splitting the diff across
  reviewers defeats the design — cross-file duplication and N+1s only show
  up with the full picture.
- **Reviewers search, they don't guess.** A reuse finding with no pointer to
  the existing utility ("there's probably a helper for this") is noise.
  Require `file:line` evidence; drop findings that lack it.
- **Apply ≠ rewrite.** This is cleanup of the user's recent changes, not a
  license to refactor the whole module. Keep edits scoped to what the diff
  touched plus the minimal surrounding change a fix requires. Altitude
  findings are the exception that proves the rule: when the right fix is
  deeper than the diff, FLAG it — don't unilaterally rebuild the shared
  mechanism inside a cleanup pass.
- **Don't drift into bug-hunting.** If a reviewer surfaces a genuine
  correctness bug, report it prominently — but as a separate "found a bug"
  note, not folded into cleanup fixes. Correctness review is a different
  pass with different verification standards.
- **Respect project conventions.** If the repo has AGENTS.md / CLAUDE.md /
  HERMES.md or a linter config, fold those rules into the reviewer prompts
  so suggestions match house style instead of fighting it.
- **Large diffs blow context.** If the diff is huge, scope it down before
  delegating — four subagents each carrying a 5000-line diff is expensive
  and may truncate.
- **Over-trusting dead code tools.** `knip`, `ts-prune`, and `depcheck`
  flag exports that ARE used dynamically (string-based imports, reflection).
  Always grep for the symbol name before removing — a clean tool report is
  not proof.
- **Renaming without checking public contracts.** Export names, API route
  paths, DB column names, and config keys are contracts — even if the name
  is bad, renaming breaks consumers. Tag public-contract changes as RISKY;
  never auto-rename them.
- **Removing "unnecessary" error handling.** An empty catch block or
  ignored error might be intentional — the error is expected and benign in
  that context. Flag it, don't remove it; let the human decide.
- **Not every special case is a band-aid.** Compat shims, staged
  migrations, and isolation layers around vendored code look like altitude
  violations but are deliberate design. Check `git blame` and surrounding
  comments before flagging; when the intent is unclear, mark
  `confidence: low`.

## Related

The structural audit in the main SKILL.md (Phase 3) and the mechanical
cleanup phases (Phase 1–2) cover the same territory at the repo level; this
simplify scenario is the standalone after-the-fact pass over a diff. For
the pre-commit security/quality gate (the bug hunt), use the `review` skill;
this is the cleanup.
