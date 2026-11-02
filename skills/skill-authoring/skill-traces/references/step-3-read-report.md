# Step 3 — Read report

Open `report.md`. Present the Overview plus the sections the chosen modes own — when
all three are on, that is sections 1-4 in one pass. The report comes first on its
own; curation questions belong to the next turn.

**Report shape** — what to present, in order:

- **Overview** — Problem (2–4 sentences: what the traces show the user repeating,
  correcting, or never using), Proposed change (the smallest set of skill edits that
  removes that repetition), Actions count (`<N> total — <a> new skills, <b> skill
  updates, <c> retirements, <d> need a decision`).

- **Section 1** — one row per repeated phrase: `| # | Phrase (quoted) | Sessions | Owner | Action |`.
  Owner is an existing skill (name, path) or `NEW <name>`; Action is the action id
  from `actions.json`. `--learn` owns the rows that carry a `create` action.

- **Section 2** — one row per stale-line claim:
  `| # | Skill (path) | Stale line (quoted) | Evidence (session ids) | Replacement | Action |`.
  `--evolve` owns the rows that carry an `edit` or `propose` action.

- **Section 3** — one row per unused skill:
  `| # | Skill (name, path) | Sessions loaded | Last used | Why safe | Action |`.
  `--unlearn` owns the rows that carry a `delete`, `ask`, or `group` action. When
  `manifest.json` -> `sessions_kept` is under 20 or the `params.days` window is
  under 7 days, this section is titled `## 3. Not seen in this window` and lists
  zero-use skills as information only; no retirement action is emitted.

- **Section 4** — recurring needs with no owner; no action ids; these are for the
  user to decide. `--learn` presents them.

Write short sentences with one meaning each. No hedged summaries: a count is a
number, a path is a path.

**Unverified claims** (present only when a verifier section failed) and **Dropped
claims** (bullet list: claim, reason, which verifier) are shown but not acted on
unless the user asks; any action emitted for them carries `requires_confirmation:
true`.

A mode with no matching row in its section ends with `nothing to apply` and no
decision record; it does not block the other modes.
