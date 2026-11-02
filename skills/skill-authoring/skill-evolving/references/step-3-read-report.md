# Step 3 — Read the report

Read `report.md` first, then present:

- **Overview** — what the traces show the user repeating, correcting, or never using
- **Section 2 — Skills to update** (this skill's curation target) — one row per stale-line claim:
  `| # | Skill (path) | Stale line (quoted) | Evidence (session ids) | Replacement | Action |`
  The action id is the id from `actions.json`.
- **Sections 1 and 4** — informational only; route section 1 to `skill-learning`, section 4 carries no action ids.

Section 3 (unused → retire) emits no delete/disable action when `disuse_evidence.sufficient` is false (window too narrow: one working directory, fewer than 20 sessions, under 7 days).

Write short sentences with one meaning each. No hedged summaries: a count is a number, a path is a path.

**Unverified claims** (present only when a verifier section failed): listed but not acted on unless the user asks; any action emitted for them carries `requires_confirmation: true`.

**Dropped claims**: bullet list — claim, reason it was dropped (which verifier, what failed). Includes "previously rejected by the user" items.

The report comes first on its own; curation questions belong to the next turn.