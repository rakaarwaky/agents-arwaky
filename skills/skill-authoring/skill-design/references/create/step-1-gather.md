# Create — Step 1: Gather information

Ask the user one at a time, as normal conversation (not option prompts):

1. **Skill name** — must satisfy the `name-format` rule (see the validator catalog in `audit/step-3-validator-catalog.md`). Validate before continuing.
2. **Category** — the category folder the skill belongs under: `<skills-dir>/<category>/<skill-name>/`. Default to the category of its sibling skills.
3. **Scope** — present two options:
   - **Project** (recommended): `<repo-root>/<skills-dir>/<category>/<skill-name>/SKILL.md` — lives in this repo, shareable with teammates. Default when inside a git repo.
   - **User**: the harness's user-level skills directory — available in all projects.
4. **What it should do** — the workflow to automate, a repeated example prompt, or the task description.

Resolve the real directory for the chosen scope from the harness config or repo layout before writing; never hardcode a home path into the skill body.

## Completion

- Skill name validated against `name-format`; category and scope chosen; the job is described.
