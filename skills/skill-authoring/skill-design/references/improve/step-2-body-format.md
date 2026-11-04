# Improve — Step 2: Enforce the SKILL.md body format

**Goal:** verify the target `SKILL.md` uses exactly `# Title` / `## Global rules` / `## Routing` before any edit.

Every skill being improved must use this exact body shape in `SKILL.md`:

```
# Title

You <one paragraph: what the agent does when this skill loads>.

## Global rules

## Routing
```

- **Title** — one `#` heading with the skill name.
- **Intro paragraph** — immediately after the title, one short paragraph stating what the agent does when this skill loads. It is part of the `# Title` section (the template skeleton puts it under `# <Skill Name>`), not a heading of its own; a body with zero lines between the title and `## Global rules` reads as a dead TOC and is a shape defect.
- **Global rules** — bullets only. Cross-step policy, invariants, record formats, and any fact read by more than one step.
- **Routing** — a table of contents mapping each step/reference to its purpose.

All task data, commands, field shapes, examples, stop conditions, and worked examples belong in `references/*.md` or `scripts/*`. If the body contains anything beyond the three sections above, move it to a reference file before publishing.

## Completion

- [ ] The target `SKILL.md` body is exactly `# Title` / `## Global Rules` / `## Routing` (intro paragraph under the title); overflow is in references.
- [ ] Verified mechanically: `grep -n '^## ' <SKILL.md>` returns exactly two `##` headings — `Global Rules` and `Routing`, in that order, with no third. `aa skills lint` does not check this (body shape is convention-enforced, per `step-4-validator-catalog.md` — What lint does NOT check); the grep is the check. Accept either casing of the second heading — `## Global rules` or `## Global Rules` — the tree is mixed (45 skills lowercase, 24 uppercase, per a 2026-11 census); never force one case on skills that already conform. What the grep rejects is a third `##` section, not casing.
- [ ] A stop-condition is never its own `## Completion` section in the body — it is one bullet in `## Global Rules` (e.g. "**Completion.** <criterion>"), because a fourth heading breaks the three-section shape.
