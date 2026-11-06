# Improve — Step 2: Enforce the SKILL.md body format

**Goal:** verify the target `SKILL.md` uses exactly `# Title` / `## Rules` / `## Routing` before any edit.

Every skill being improved must use this exact body shape in `SKILL.md`:

```
# Title

## Rules

## Routing
```

- **Title** — one `#` heading with the skill name.
- **Rules** — bullets only. Cross-step policy, invariants, record formats, and any fact read by more than one step.
- **Routing** — a table of contents mapping each step/reference to its purpose.

All task data, commands, field shapes, examples, stop conditions, and worked examples belong in `references/*.md` or `scripts/*`. If the body contains anything beyond the three sections above, move it to a reference file before publishing.

## Completion

- The target `SKILL.md` body is exactly `# Title` / `## Rules` / `## Routing`; overflow is in references.
- Verified mechanically: `grep -n '^#' <SKILL.md>` returns only the `#` title and exactly two `##` headings — `## Rules`, `## Routing`. `sdc lint` does not check this (body shape is convention-enforced, per `step-4-validator-catalog.md` — What lint does NOT check); the grep is the check. Case matters: the heading is `## Rules`, matching the `template/skill.md` skeleton and the rebuilt skills in this pack (`research-study`, `web-design`).
- A stop-condition is never its own `## Completion` section in the body — it is one bullet in `## Rules` (e.g. "**Completion.** <criterion>"), because a fourth heading breaks the three-section shape.
- Moving a section (or its table) out of the body to a reference is a **two-part edit**: the heading move *and* the Routing-table row that pointed at the in-body section. A row like `| SKILL.md <Section> | ... |` is a self-referential dangling entry once `<Section>` no longer exists in the body; either delete it or re-point it at the reference file that now owns the content. Verify with `grep 'SKILL.md ' <SKILL.md>` on the Routing table that no row still names a heading that has been moved out.
