# Step 3 — Read report

Open `report.md`. Present the Overview plus **section 1** (Repeated phrases → skills) and **section 4** (Gaps).

**Report shape** — what to present, in order:

- **Overview** — Problem (2–4 sentences: what the traces show the user repeating, correcting, or never using), Proposed change (the smallest set of harness edits that removes that repetition), Actions count (`<N> total — <a> new skills, <b> skill updates, …`).
- **Section 1** (this skill's curation target) — one row per repeated phrase: `| # | Phrase (quoted) | Sessions | Owner | Action |`. Owner is an existing skill (name, path) or `NEW <name>`; Action is the action id from `actions.json`.
- **Section 4** (this skill's curation target) — recurring needs with no owner; no action ids; these are for the user to decide.

Write short sentences with one meaning each. No hedged summaries: a count is a number, a path is a path.

**Unverified claims** (present only when a verifier section failed) and **Dropped claims** (bullet list: claim, reason, which verifier) are shown but not acted on unless the user asks; any action emitted for them carries `requires_confirmation: true`.

The report comes first on its own; curation questions belong to the next turn.