# Step 1: Specialization Selection

The reviewer panel is **fixed**: every run launches exactly **3 reviewers** — 1 General, 1 Tests, 1 Simplicity — regardless of task size or content. No specialization is conditional, nothing competes for slots, and none is ever dropped. This decision is made **before Step 3 (Implement)** and does not depend on the description. Always use the parallel-reviewer path (`len(reviewer_configs) >= 2` on every run) — **every run is multi-reviewer**, with individual review files and a merge on every run, and Simplicity is always in `reviewer_configs`.

### Specialization Catalog

| Specialization | Persona to Inject | Focus Areas | When to Use |
|---------------|-------------------|-------------|-------------|
| **General** | `reviewer` | Code quality, bugs, naming, SOLID, style, security-relevant defects, and plan/requirement alignment of the implementation | Always (every run) |
| **Tests** | None (prompt-only) | Test coverage, test quality, edge cases, mocking | Always (every run) |
| **Simplicity** | None (prompt-only) | Over-engineering, extra helpers/files for one caller, unused abstractions, reinvented stdlib, YAGNI | Always (every run) |

The security and plan-alignment concerns are folded into the General reviewer; they no longer get a dedicated specialist.

**Note on persona injection:** The `Tests` and `Simplicity` specializations do NOT get persona instructions prepended — they rely entirely on the task prompt to define their behavior. This avoids a conflict between the `reviewer` persona's review focus and the specialist prompt's scope restriction.

The `reviewer` persona instructions are prepended as-is for the general code quality review.

### Fixed Reviewer Panel

There is no selection algorithm and no input analysis — the composition is identical on every run:

```
# Fixed panel — no input analysis, no slot allocation, no conditionals.
PANEL = ["general", "tests", "simplicity"]  # 3 reviewers
```

If the task is a typo fix or a doc-only change, the panel is unchanged — every specialist still runs and simply reports 0 issues if they find nothing in their scope.

### Building reviewer_configs

Build `reviewer_configs` the same way on every run — one config per panel member, in panel order:

```
reviewer_configs = []

for specialist in ["general", "tests", "simplicity"]:
    reviewer_configs.append({
        subagent_id: null,
        persona_to_inject: specialist == "general" ? "reviewer" : null,  # null = prompt-only, no persona prepended
        specialization: specialist,
        review_file: f"${scratch_dir}/grok-review-{IMPL_ID}-{suffix_map[specialist]}.md"
    })
```

The specialization-to-suffix mapping is: `general` → `general`, `tests` → `tests`, `simplicity` → `simplicity`.

There is exactly **one** general reviewer per run. The general reviewer's source tag in the merged review is `[General]`.

### Announce Specializations

Announce the specialization choices to the user **once**, then move on. Example of a correct message:
> "Review panel: 1 general + tests + simplicity (3 reviewers)."

Strict rules for this announcement:
- This message describes **only the specialization selection**. Do **not** also claim that the implementer is being launched, that reviewers are starting, or that the run is "now running" — those statements belong to later steps, after the corresponding `spawn_subagent` calls.
- **No permission-asking on launch** — the announcement is informational, not interactive. Do **not** end it with a question to the user: no "Want me to check in every 30 minutes?", no "Should I proceed?", no "Let me know if you want me to do anything different." Pick a default and proceed. This step is fire-and-forget: no blocking interaction, no approval step, no cadence negotiation.
- Proceed directly to Step 2 (Memory Retrieval) and Step 3 (Implement) in the same turn. The next user-visible message should be the post-spawn launch confirmation described in Step 3, not a continuation of this announcement.
