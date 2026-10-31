---
name: skill-evolving
description: Autonomous self-evolution engine for agent skills. Ingests session traces via learn, fans out category-level audit subagents, coordinates authoring, library cataloging, and lifecycle pruning, verifies quality gates, and publishes pull requests. Use when the user runs /skill-evolving --scope 24h --headless (or any of its flags such as --since-last, --dry-run), names pr-la-xxx commands (auto-fix, cli-commands, config-system, doc-rules, external-lint, file-watch, filesystem, git-hooks, import-rules, logging, maintenance, mcp-server, naming-rules, orphan-rules, project-setup, quality-rules), or asks for a daily/scheduled skill optimization pass.
when-to-use: Use when running autonomous or scheduled self-evolution across the skill tree, evolving skills from execution traces, or running a headless daily skill optimization pass; coordinating multi-agent skill maintenance.
argument-hint: "[--scope <window>] [--headless] [--since-last] [--dry-run]"
---

# skill-evolving

The orchestrator skill for autonomous skill evolution. Coordinates trace collection,
parallel category audits via subagents, frontmatter and body refinements, catalog
synchronization, and lifecycle consolidation into a single verified publication pass.

Modeled on the four-skill pack under `skills/skill-authoring/`:
- **`research-study/learn`** — mines session traces, repeated user phrases, and friction.
- **`skill-design`** — creates new skills and refines frontmatter, triggers, and hints.
- **`skill-library`** — audits category placement, repairs metadata, and updates `CATALOG.md`.
- **`skill-lifecycle`** — prunes bloat, consolidates variants, and deletes empty categories.

## Architecture & Responsibilities

```
                                 skill-evolving
                               (Top-Level Agent)
                                      │
                   ┌──────────────────┴──────────────────┐
                   ▼                                     ▼
        Step 1: Ingest Traces                 Step 2: Tree Discovery
        research-study/learn            aa skills list & categories
                   │                                     │
                   └──────────────────┬──────────────────┘
                                      ▼
                        Step 3: Parallel Subagents
                      (1 Subagent per Category Folder)
                     ┌────────────────┬────────────────┐
                     ▼                ▼                ▼
                devops/         automation/     skill-authoring/
                 agent             agent             agent
                     │                │                │
                     └────────────────┼────────────────┘
                                      ▼
                        Step 4: Central Aggregation
                        Apply proposed mutations
                                      │
                                      ▼
                        Step 5: Library & Lifecycle
                        aa skills repair & aa skills catalog
                        skill-lifecycle --evolution
                                      │
                                      ▼
                        Step 6: Gate & Verification
                        aa skills validate --summary
                        aa skills catalog --check
                                      │
                                      ▼
                        Step 7: Commit & Pull Request
                        Branch -> Commit -> gh pr create
```

## Related Skills & Routing

| Role | Skill | Action in Evolution Loop |
|---|---|---|
| Trace Mining | `research-study/learn` | Run `collect_sessions.py --days 1 --include-headless` to extract friction points, tool failures, and user phrases from the last 24 hours. |
| Creation & Refinement | `skill-design` | Rewrite descriptions, adjust `argument-hint:`, split bloated bodies into `references/`, add newly discovered workflows. |
| Catalog & Mechanical Repair | `skill-library` | Run `aa skills repair --apply`, `aa skills weed`, and `aa skills catalog`. |
| Pruning & Consolidation | `skill-lifecycle` | Run `skill-lifecycle --evolution` across the tree to merge overlapping variants and retire duplicates. |

## Workflow

### Step 1: Trace Ingestion (Telemetry)
Run the session collector from `research-study/learn` scoped to the target window (default 24h):

```bash
python3 skills/research-study/learn/collect_sessions.py --days 1 --include-headless
```

Argument mapping: `--scope <window>` selects `--days N` (a day count; `24h` means 1 day) and `--since-last` selects `--since-last`; `--headless` passes `--include-headless`. `--dry-run` runs Steps 1-6 but stops before commit/PR and reports the proposed diff.

Headless semantics: no `ask_user_question` (no interactive prompts), reversible edits are auto-applied, and the pass ends with commit + PR (Step 7).

Examine output artifacts in the run directory (`<RUN>`):
- `usage.json`: identifies zero-hit or heavily invoked skills.
- `phrases.json`: captures user phrasing patterns, shorthand terms, and repeated instructions.
- `surfaces.json`: highlights missing skills, unregistered slash commands, or collisions.

### Step 2: Category Discovery
List all top-level category directories under `skills/`:

```bash
find skills -mindepth 1 -maxdepth 1 -type d ! -name "_*" ! -name ".*"
```

### Step 3: Spawn Parallel Category Subagents
For each category folder containing skills, spawn a dedicated subagent with bounded scope:

- **Prompt template for category subagent:**
  > "You own category `<category>` under `skills/<category>`. Read `<RUN>/phrases.json` and `<RUN>/usage.json`. Audit each `SKILL.md` inside `skills/<category>/` against actual trace friction: (1) Update `description:` and `when-to-use:` with observed user phrasing. (2) Ensure `argument-hint:` matches the current CLI flags. (3) If a skill body exceeds 200 lines, factor scenario sections into `references/<scenario>.md`. (4) Verify all four mandatory keys exist (`name`, `description`, `when-to-use`, `argument-hint`). Apply changes in place."

Spawn subagents in parallel using `spawn_subagent`.

### Step 4: Central Aggregation & Mechanical Repairs
Once all category subagents finish:
1. Run mechanical repairs for standard violations:
   ```bash
   aa skills repair --apply
   ```
2. Rebuild the master catalog:
   ```bash
   aa skills catalog
   ```

### Step 5: Cross-Category Consolidation
Execute the unattended lifecycle pass to consolidate cross-category variants:

```bash
/skill-lifecycle skills --evolution
```

### Step 6: Zero-Trust Quality Gate
Run the full suite of skill validation gates:

```bash
aa skills validate --summary
aa skills catalog --check
python3 -m pytest modules/skills/tests -q
```

If any check fails:
- Inspect error messages against `modules/skills/_rules/skill-rules.md`.
- Fix offending frontmatter or links.
- Re-run validation until all checks report clean.

### Step 7: Publication & Pull Request
1. Check for uncommitted changes:
   ```bash
   git status --short
   ```
2. If changes exist:
   ```bash
   git add skills/
   git commit -m "chore(skills): daily autonomous self-evolution pass"
   git push origin HEAD
   gh pr create --title "chore(skills): daily autonomous self-evolution" --body "Automated daily evolution pass across skills/ tree driven by skill-evolving."
   ```
3. If no changes exist:
   ```bash
   git commit --allow-empty -m "chore(skills): daily evolution check - clean tree"
   ```

## Completion Criteria

- All category folders reviewed against recent session traces.
- All four mandatory frontmatter keys present and valid across all touched skills.
- Zero rule violations reported by `aa skills validate`.
- `CATALOG.md` synchronized and `aa skills catalog --check` exits 0.
- Work committed and submitted via GitHub pull request.
