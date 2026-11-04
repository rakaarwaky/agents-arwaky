# Improve — Step 2: Enforce the SKILL.md body format

**Goal:** verify the target `SKILL.md` uses exactly `# Title` / `## Global rules` / `## Routing` before any edit.

Every skill being improved must use this exact body shape in `SKILL.md`:

```
# Title

## Global rules

## Routing
```

- **Title** — one `#` heading with the skill name.
- **Global rules** — bullets only. Cross-step policy, invariants, record formats, and any fact read by more than one step.
- **Routing** — a table of contents mapping each step/reference to its purpose.

All task data, commands, field shapes, examples, stop conditions, and worked examples belong in `references/*.md` or `scripts/*`. If the body contains anything beyond the three sections above, move it to a reference file before publishing.

## Completion

- The target `SKILL.md` body is exactly `# Title` / `## Global rules` / `## Routing`; overflow is in references.
- Verified mechanically: `grep -n '^#' <SKILL.md>` returns only the `#` title and exactly two `##` headings — `## Global rules`, `## Routing`. `sdc lint` does not check this (body shape is convention-enforced, per `step-4-validator-catalog.md` — What lint does NOT check); the grep is the check. Case matters: the heading is `## Global rules` (lowercase `r`), matching the `template/skill.md` skeleton and the rebuilt skills in this pack (`research-study`, `web-design`).
- A stop-condition is never its own `## Completion` section in the body — it is one bullet in `## Global rules` (e.g. "**Completion.** <criterion>"), because a fourth heading breaks the three-section shape.
