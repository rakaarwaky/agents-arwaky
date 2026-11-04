---
name: study-roadmap-builder
description: Build folder-structured quarterly study/learning roadmaps.
when-to-use: Use when the user wants to build a folder-structured quarterly study/learning roadmap with specific sub-fields per quarter, or to teach a section from an existing roadmap.
argument-hint: "<build | teach> [quarter | field | section]"
version: "1.0"
author: hermes-agent
license: MIT
tags:
  - productivity
  - learning
  - roadmap
---

# Study Roadmap Builder

Build study plans the user actually keeps and follows. For this user:
Indonesian, lifelong learner, wants long-term compounding, commits ~2 h/day
with one field per day (no context switching), and thinks in quarterly
rotations of specific sub-fields.

## Global rules

- **Do not ask permission for read-only next steps.** "Want me to open the
  reference file?" / "Should I read the next section?" — just do it. Asking
  for a trivial read signals you haven't read the material. The user has
  corrected this explicitly and gets irritated by it.
- **Specific sub-fields, not broad domains.** Never plan "math" or
  "biology" — plan a concrete slice (e.g. "linear algebra", "molecular cell
  biology", "classical mechanics"). The user explicitly rejected
  whole-discipline fields as too large.
- **Foundational → unlocks next.** Each quarter's fields are prerequisites
  that open the next quarter's fields. State the unlock relationship for
  every field ("F1 linear algebra unlocks ML in Q2").
- **Flat section files, no sub-folder.** Each section of a field's source
  roadmap is its OWN file inside the field folder: `NN-section-slug.md`. No
  per-section sub-folder, no `plan.md` inside a sub-folder. The user
  explicitly wants this flat layout.
- **Quarterly rotation, ~7 specific fields per quarter.** The user commits
  ~2 h/day but rotates one field per day across ~7 fields, so each field
  actually receives one 2-hour session per week (~12 sessions / quarter).
  Use that number to size how many section-subtopics a field can truly cover
  in the quarter. ~26 h is the theoretical maximum; realistic per-field
  throughput is lower because the field only runs on its rotation day.
- **No context switching within a day** — the user's hard rule; the plan
  must make one field per day explicit, never two fields on the same day.
- **Always end with a concrete start-now action**, not just the file tree.
- **Honest hour math.** Don't promise mastery of a whole discipline in 26 h;
  promise mastery of one specific slice, which is the point of the design.
- **Don't over-scope a field to its full source roadmap.** Expand every
  section of the public tree so nothing is lost, then cut the live
  curriculum to what the quarter's rotation cap can actually cover. The
  user pushes back on sections they cannot finish ("I only have 3 months").
  List the remainder as a named Q2 backlog, never imply the whole tree fits.
- **Don't name the user's files after the source site.** No `roadmap.sh`
  in the tree; files are `<Field>FieldDoc.md`, `NN-section-name.md`, and
  optionally a field-named reference file. Name sections by topic
  ("S01 Vectors and Spaces"), and if a reference tree file is kept, call it
  by the field name only (e.g. `linear-algebra-reference.md`), never the
  source domain. The user corrected this explicitly.
- **Keep the content self-contained, not a verbatim dump.** Expand each
  section's subtopics and concepts into the section file's own checklist.
  Do not rely on a separate `roadmap-sh-*.md` full-tree file; if you save
  one, it is optional reference, and it must not be named after the source
  site.
- **Trim to the actually-reachable scope, and be honest about it.** A field
  studied one day per week in a 7-field rotation gets 1 two-hour session a
  week, so ~12 sessions in a quarter. That is the real cap, not "26 h per
  field." List only the sections that fit; the rest is a named Q2 backlog,
  not a promise.
- **Every field has an exit test** — a real benchmark, not "I feel done."
  No pass = stay on that field. End-of-quarter, fields are "done" when
  their exit test passes.
- **Keep a no-forgetting layer.** 2 h/week spaced review (Anki) of
  everything learned so earlier quarters don't decay. Monthly 1-h
  meta-review: what's decaying → add to Anki; what's strong → mark done.
- **Use free resources.** Khan Academy, 3Blue1Brown, CrashCourse, MIT OCW.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Build procedure | [`references/procedure.md`](references/procedure.md) — 7 steps: clarify → pick 7 specific sub-fields → verify hour budget → fetch public roadmap full tree → scaffold folder structure → update README.md → give start-now action | The full build workflow with per-step guidance. |
| Deliverable structure | [`references/deliverable-structure.md`](references/deliverable-structure.md) — the flat-per-field filesystem layout, `<Field>FieldDoc.md` vs `NN-section-name.md`, the 2-hour 3-part session template (Input → Solve → Write) | How to scaffold the filesystem; do not restore the old timed 4-part format. |
| Prose style | [`references/prose-style.md`](references/prose-style.md) — the user's writing standard for this repo (no trailing parenthetical in headers, no emoji, lead with the point, no invented claims, plain active voice) | Match on first draft, not on correction. Repo AGENTS.md carries the full rules — read it before writing docs in that repo. |
| Interactive teaching | [`references/interactive-teaching.md`](references/interactive-teaching.md) — the full hard rules of the teaching mode (session start, turn shape, scoping questions, term definitions, language and register, long-session degeneration) | Building the roadmap is step one; teaching a section is a distinct mode. Running it like a chat assistant is the failure mode this section exists to prevent. |
| Video sourcing | [`references/sourcing-videos.md`](references/sourcing-videos.md) — the verified curl pipeline (DuckDuckGo lite → oEmbed verification → duration scrape) and the fetch-tool calls that do not work on YouTube URLs | For a session's input block. |
| Public roadmap API | [`references/public-roadmap-api.md`](references/public-roadmap-api.md) — how to pull the content from a public roadmap | FETCH ITS FULL TREE, then TRIM to the quarter's reachable scope. |
| Practice problems | [`references/practice-problems.md`](references/practice-problems.md) | Problem sets and worked examples for the build/teach modes. |
| Reference example (Q1) | F1 linear algebra · F2 basic statistics · F3 molecular cell biology · F4 genetics · F5 classical mechanics · F6 technical English · F7 personal finance | Each ~26 h; unlocks ML/data, biochem, E&M, technical reading, and economics in Q2. |
