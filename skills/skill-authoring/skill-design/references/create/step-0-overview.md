# Create — Step 0: Overview

Autonomous workflow for creating a new skill from scratch — default runs write without confirmation; `--dry-run` stops after the report. Design rules and frontmatter constraints are Global Rules in `SKILL.md`; these files hold only the step order.

**Goal:** produce a publishable `SKILL.md` + `references/` for a job the user describes, ending at the pre-publish checklist with the skill registered in the catalog.

Run the steps in order; each links to the next.

| Step | File | What it does |
| ---- | ---- | ------------ |
| 1 | [`step-1-gather.md`](step-1-gather.md) | Collect name, category, scope, and the job description. |
| 2 | [`step-2-trigger-fields.md`](step-2-trigger-fields.md) | Draft and approve `description:` / `when-to-use:`. |
| 3 | [`step-3-directory.md`](step-3-directory.md) | Create the skill directory and any `scripts/` / `references/` subdirs. |
| 4 | [`step-4-writer.md`](step-4-writer.md) | Pick a writer by description length. |
| 5 | [`step-5-write-skill.md`](step-5-write-skill.md) | Write `SKILL.md` and supporting files. |
| 6 | [`step-6-verify.md`](step-6-verify.md) | Verify and report the outcome; `--dry-run` ends with the planned-create report instead. |
