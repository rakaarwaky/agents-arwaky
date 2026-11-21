# Step 2: Issue Grouping & Planning

Analyze all verified `still-broken` issues, group issues that can be solved together into cohesive implementation cohorts, separate issues requiring isolation, and construct self-contained task briefs for each Grok `/implement` session.

## 2a: Issue Grouping Strategy

Evaluating whether issues belong together or apart prevents merge conflicts, reduces worktree overhead, and keeps pull requests atomic and bisectable.

### When to Group Issues Together (Single `/implement` Session)

Group issues into a single cohort when they meet any of the following criteria:

1. **Shared Subsystem or Module**: The issues touch the same files, directory tree, crate, or service module.
2. **Shared Root Cause**: Multiple bug reports stem from the same defect, misconfiguration, or missing guard.
3. **Coupled Changes**: Resolving issue A directly depends on or alters the contract needed for issue B (e.g. schema migration + API endpoint + client update).
4. **Complementary Minor Fixes**: A cluster of small, low-risk fixes (e.g. typos, documentation updates, related test additions) within the same repository area.

*Outcome*: Exactly one Orca worktree and one Grok session running `/implement` handles all issues in this group.

### When to Separate Issues (Multiple Grok Sessions)

Isolate issues into separate implementation groups when:

1. **Disjoint Subsystems**: Issues affect completely independent components (e.g., frontend UI vs backend auth vs CI pipeline).
2. **Conflicting Changes**: Issues propose competing modifications to shared logic or require divergent architectural choices.
3. **Large Scope or High Blast Radius**: Substantial refactors or complex new capabilities that warrant dedicated review and verification.
4. **Independent Bug Fixes**: Bugs in different areas that should each produce an independent, cleanly bisectable git commit and PR.

*Outcome*: Each isolated issue or disjoint cluster gets its own dedicated Orca worktree and its own Grok session running `/implement`.

## 2b: Cohort Specification & Slug Generation

For each identified group $G_i$, generate:

- **Group Slug**: Lowercase identifier matching `issue-[slug]` (e.g. `issue-auth-redirect`, `issue-42-45`, `issue-parser-crash`), $\le 40$ characters.
- **Issues Handled**: Array of issue numbers (e.g. `[42, 45]`).
- **In-Scope Paths**: List of exact files or directories permitted to be modified.
- **Out-of-Scope Paths**: Sibling modules and unaffected directories forbidden from modification.

## 2c: Compose the `/implement` Brief

For each cohort, compose a complete, self-contained brief. The child Grok session runs in a fresh environment without prior conversation context:

```text
/implement <concise-task-summary>

Issues Addressed:
- #<N>: <title>
- #<M>: <title>

Goal:
<1-2 sentence description of what the implementation achieves>

Scope:
- In-scope: <exact paths or directories>
- Out-of-scope: <sibling files, shared configurations, or external packages>

Verified Symptoms & Reproduction:
- Issue #<N>: Run `<repro-command-N>` (currently fails with `<observed-error>`)
- Issue #<M>: Run `<repro-command-M>` (currently fails with `<observed-error>`)

Constraints:
- Decisions from user quiz: <quiz-decisions>
- Build isolation: Use worktree-local target and cache dirs; never touch shared repo targets.
- Targeted verification: Run targeted package tests only (`<tool> test -p <pkg>`), not full monorepo gates.
- Deliverable: Clean, verified implementation in this worktree. Do not push, do not open PRs, do not close issues.

Acceptance Criteria:
- All reproduction commands exit 0 with expected behavior.
- Regression tests added covering the fixed edge cases.
- Repository linters and type checkers pass for changed files.
```

## 2d: Plan Execution Waves

Count total groups to spawn:

- If total groups $\le 10$: Schedule all groups in Wave 1.
- If total groups $> 10$: Partition groups into waves of at most 10 concurrent worktrees. Wave $k+1$ begins after Wave $k$ completes verification.

Proceed to Step 3 (`step-3-spawn-grok-implement.md`).
