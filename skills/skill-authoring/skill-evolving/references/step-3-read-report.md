# Step 3 — Read the report

Read `report.md` first, then present:

- **Overview** — what the traces show the user repeating, correcting, or never using
- **Section 2 — Skills to update** — this is the curation surface. Each row: skill path, stale line (quoted), evidence session ids, replacement, action id

Sections 1 (repeated phrases → skills) and 3 (unused → delete or disable) are informational; section 3 emits no delete/disable action when `disuse_evidence.sufficient` is false (window too narrow: one working directory, fewer than 20 sessions, under 7 days).

Section 4 (gaps) carries no action ids — for the user to decide.
