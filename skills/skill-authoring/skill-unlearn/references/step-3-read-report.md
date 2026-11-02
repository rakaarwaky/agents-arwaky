# Step 3 — Read report

Read `report.md`; present the Overview plus section 3 (Unused → delete or disable). The report comes first on its own; curation questions belong to the next turn.

# Signal Definitions

The trace pipeline extracts five signal types per session. The full definitions for these signals are owned by the Global Rules of the respective consuming skills to avoid second copies:

- **§1 Instructions typed by hand** & **§5 Gaps**: See `skill-learning` Global Rules.
- **§2 Friction** & **§3 Stale skill lines**: See `skill-evolving` Global Rules.
- **§4 Unused surfaces**: See `skill-unlearn` Global Rules (deterministic counts in `usage.json` and structural findings in `surfaces.json`).

## Per-session record shape (mappers)

```
### <index> <session id> — <title>
- area: repo and top directories touched
- task type: feature | bug fix | debugging | ops/infra | research | config/harness | writing | other
- skills used / mcps used: names from the session file (or none)
- instructions outside skills: quoted, with the owning skill or NEW
- friction: quoted
- stale skill signals: skill, quoted current line, quoted evidence
- gaps
```

End each mapper note with `## Batch candidates`: `- [phrase|stale|gap] <text> | sessions: <ids> | owner: <skill or NEW>`, duplicates merged within the batch.

## Report shape (`report.md`)

Write short sentences with one meaning each. No hedged summaries: a count is a number, a path is a path.

```markdown
# trace-learning report — <today>

## Overview
Problem: <2–4 sentences: what the traces show the user repeating, correcting, or never using>
Proposed change: <2–4 sentences: the smallest set of harness edits that removes that repetition>
Actions: <N> total — <a> new skills, <b> skill updates, <c> enables, <d> deletes/disables, <e> need a decision

## 1. Repeated phrases -> skills
| # | Phrase (quoted) | Sessions | Owner | Action |
Owner is an existing skill (name, path) or NEW <name>. Action is the action id from actions.json.

## 2. Skills to update
| # | Skill (path) | Stale line (quoted) | Evidence (session ids) | Replacement | Action |

## 3. Unused -> delete or disable
| # | Name | Kind | Count | Last used | Why safe | Action |
Kind is skill, plugin, mcp, workflow, or hook. "Why safe" names what still does the job, or says `only copy — ask`, or `referenced by <names> — ask`. A grouped action is one row that names the group and lists its members in the Name cell.

## 4. Gaps
Recurring needs with no owner. No action ids; these are for the user to decide.

## Unverified claims
Only present when a verifier section failed: the claims from that section, listed but not acted on unless the user asks; any action emitted for them carries `requires_confirmation: true`.

## Dropped claims
Bullet list: claim, reason it was dropped (which verifier, what failed). Include "previously rejected by the user" items here.

## Coverage
- sessions seen / kept / dropped by reason (from manifest.json)
- human turns read; sessions read by mappers vs total
- map or reduce slots lost; verifier sections that failed
- window and filters used (params from manifest.json)
- what this run could not see: headless sessions unless included, hook use, managed MCP servers, anything outside this machine's GROK_HOME
```
