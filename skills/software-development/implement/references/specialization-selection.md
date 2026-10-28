# Specialization Selection


The orchestrator fills the base slots from the description, then **always pins Simplicity**. Simplicity does not compete for a base slot and is never dropped by the cap. Effort 1 is therefore 1 general + simplicity. This decision is made **before Step 1 (Implement)** based on the implementation description and conversation context. Always use the parallel-reviewer path (`len(reviewer_configs) >= 2` on every run).

### Specialization Catalog

| Specialization | Persona to Inject | Focus Areas | When to Use |
|---------------|-------------------|-------------|-------------|
| **General** | `reviewer` | Code quality, bugs, naming, SOLID, style | Always (every run) |
| **Tests** | None (prompt-only) | Test coverage, test quality, edge cases, mocking | When implementation involves new logic, APIs, or data processing |
| **Plan Alignment** | None (prompt-only) | Implementation matches the design/plan, no scope drift, all requirements addressed | When a design doc or detailed plan is referenced in the description |
| **Security** | `security-auditor` | Auth, injection, data handling, secrets, OWASP | When implementation touches auth, user input, APIs, data storage, or network |
| **Simplicity** | None (prompt-only) | Over-engineering, extra helpers/files for one caller, unused abstractions, reinvented stdlib, YAGNI | Always. Pinned after slot allocation. Never skip. |

**Note on persona injection:** The `Tests`, `Plan Alignment`, and `Simplicity` specializations do NOT get persona instructions prepended — they rely entirely on the task prompt to define their behavior. This avoids a conflict between the `reviewer` persona's review focus and the specialist prompt's scope restriction.

The `security-auditor` persona instructions are prepended for security review because they contain purpose-built audit methodology.

The `reviewer` persona instructions are prepended as-is for the general code quality review.

### Decision Algorithm

The coordinator determines the reviewer composition in two steps:

```
# Step 1: Determine total reviewer slots from effort
if effort <= 3:
    total_slots = effort
elif effort == 4:
    total_slots = 5
else:  # effort == 5
    total_slots = 6

# Step 2: Identify relevant specialists from description
matched_specialists = []

if description mentions auth, security, user input, API keys, 
   secrets, encryption, permissions, tokens, or OWASP:
    matched_specialists.append("security")

if description references a design doc, plan, spec, RFC, 
   or linked document:
    matched_specialists.append("plan_alignment")

if description involves new logic, endpoints, data processing,
   algorithms, or business rules:
    matched_specialists.append("tests")

# Do not put simplicity in matched_specialists. It is pinned below.

# Step 3: Allocate base slots (at least 1 general)
specialists = matched_specialists[:total_slots - 1]
num_generals = total_slots - len(specialists)

# Step 4: Always pin simplicity. Does not consume a base slot.
if "simplicity" not in specialists:
    specialists.append("simplicity")
```

**Examples:**
- Effort 1, anything → 1 general + simplicity
- Effort 2, typo/doc-only → 1 general + 1 extra general + simplicity
- Effort 2, touches auth → 1 general + security + simplicity
- Effort 3, touches auth → 1 general + security + 1 extra general + simplicity
- Effort 3, touches auth + has design doc → 1 general + security + plan + simplicity
- Effort 4, only tests match → 4 generals + tests + simplicity
- Effort 4, feature + auth + design doc → 2 generals + security + tests + plan + simplicity
- Effort 5, all optional match → 3 generals + security + tests + plan + simplicity

### Building reviewer_configs

Build `reviewer_configs` for every effort level. The general reviewer is always included. Simplicity is always included. Other specialists and extra generals fill the remaining base slots:

```
reviewer_configs = []

# Add general reviewers
for i in range(1, num_generals + 1):
    tag = "general" if i == 1 else f"general-{i}"
    reviewer_configs.append({
        subagent_id: null,
        persona_to_inject: "reviewer",  # key into loaded persona instructions
        specialization: tag,
        review_file: f"${scratch_dir}/grok-review-{IMPL_ID}-{tag}.md"
    })

# Add specialist reviewers
for each specialist in specialists:
    reviewer_configs.append({
        subagent_id: null,
        persona_to_inject: specialist == "security" ? "security-auditor" : null,  # null = prompt-only, no persona prepended
        specialization: specialist,
        review_file: f"${scratch_dir}/grok-review-{IMPL_ID}-{suffix_map[specialist]}.md"
    })
```

The specialization-to-suffix mapping is: `general` → `general`, `general-2` → `general-2`, `general-3` → `general-3`, `tests` → `tests`, `security` → `security`, `plan_alignment` → `plan`, `simplicity` → `simplicity`.

For source tags in the merged review, use `[General]`, `[General-2]`, `[General-3]` to distinguish independent general reviewers. All general reviewers use the same `reviewer` persona and the same General Reviewer prompt — independent runs naturally produce different findings due to LLM variance.

### Announce Specializations

Announce the specialization choices to the user **once**, then move on. Examples of correct messages:
> "Using effort level 1: 1 general + simplicity (simplicity always pinned)."
> "Using effort level 2: 1 general + security + simplicity (implementation touches auth)."
> "Using effort level 4: 2 generals + security + tests + plan + simplicity (6 reviewers)."

Strict rules for this announcement:
- This message describes **only the specialization selection**. Do **not** also claim that the implementer is being launched, that reviewers are starting, or that the run is "now running" — those statements belong to later steps, after the corresponding `spawn_subagent` calls.
- Do **not** end the announcement with a question to the user. No "Want me to check in every 30 minutes?", no "Should I proceed?", no "Let me know if you want me to do anything different." This step is fire-and-forget: no blocking interaction, no approval step, no cadence negotiation.
- Proceed directly to Step 0 (Memory Retrieval) and Step 1 (Implement) in the same turn. The next user-visible message should be the post-spawn launch confirmation described in Step 1, not a continuation of this announcement.
