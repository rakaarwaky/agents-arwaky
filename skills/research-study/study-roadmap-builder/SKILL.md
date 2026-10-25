---
name: study-roadmap-builder
description: Build folder-structured quarterly study/learning roadmaps.
version: "1.0"
author: hermes-agent
license: MIT
tags:
  - productivity
  - learning
  - roadmap
related_skills:
  - session-librarian
---

# Study Roadmap Builder

Build study plans the user actually keeps and follows. For this user: Indonesian,
lifelong learner, wants long-term compounding, commits ~2 h/day with one field per
day (no context switching), and thinks in quarterly rotations of specific sub-fields.

## Always-on rules (apply to every plan you build)

- **Do not ask permission for read-only next steps.** "Want me to open the reference file?" / "Should I read the next section?" — just do it. Asking for a trivial read signals you haven't read the material. The user has corrected this explicitly and gets irritated by it.
- **Specific sub-fields, not broad domains.** Never plan "math" or "biology" —
  plan a concrete slice (e.g. "linear algebra", "molecular cell biology", "classical
  mechanics"). The user explicitly rejected whole-discipline fields as too large.
- **Foundational → unlocks next.** Each quarter's fields are prerequisites that open the
  next quarter's fields. State the unlock relationship for every field ("F1 linear
  algebra unlocks ML in Q2").
- **Flat section files, no sub-folder.** Each section of a field's source
  roadmap is its OWN file inside the field folder: `NN-section-slug.md`. No
  per-section sub-folder, no `plan.md` inside a sub-folder. The user explicitly
  wants this flat layout.
- **Quarterly rotation, ~7 specific fields per quarter.** The user commits ~2 h/day
  but rotates one field per day across ~7 fields, so each field actually receives
  one 2-hour session per week (~12 sessions / quarter). Use that number to size
  how many section-subtopics a field can truly cover in the quarter. ~26 h is the
  theoretical maximum; realistic per-field throughput is lower because the field
  only runs on its rotation day.

## Interactive teaching — the second half of this skill

Building the roadmap is step one. The user then opens the section file and asks
to be TAUGHT it. That teaching session is a distinct mode with its own hard
rules; running it like a chat assistant is the failure mode this section exists
to prevent.

### Session start: read before you speak

1. Read the section file the user pointed at (`README.md`, `NN-section.md`) and
   the field doc. The checklist in that file IS the day's plan.
2. The whole pasted checklist is TODAY's scope. Do not invent a "later" tier,
   do not narrow it to one module, do not propose coming back to the rest.
3. Announce the 3-part session block ONCE (Input → Solve → Essay). After that
   single announcement, never restate a block, the goal sentence, or the
   section title again for the rest of the session.
4. Then teach, in checklist order, without asking permission to begin.

### Turn shape: one move, then hand back

- **One concept block per turn**, then a concrete problem the user solves. The
  user's answer is the next turn's input — that is the interaction. Never stack
  several scaffold layers (definition → properties table → geometric/algebraic
  split → examples → "ready to practise?") on a single definition.
- **Default to one line when the user asks "what is X".** If they ask for a
  definition, a definition is what they get. Expanding a requested one-liner
  into five headed sections is a failure, not thoroughness.
- **Problem-only when the user asks for practice.** "Don't give me a hint, give
  the problem only" means: emit the problem, emit nothing else, and wait. Do not
  pre-attach a solution or a hint list for comparison.
- **When the user is wrong, teach the mechanism, not just the verdict.**
  "That's incorrect" leaves them stuck. Show the operation that would have to be
  true for their step to work (you cannot divide an exponent; you take a root).

### Scoping questions

- Never ask "which topic should we start with?" / "which subtopic do you want
  to practise?" when the user has already pasted or pointed at the checklist.
  That question reads as not having read the file.
- Only ask a scoping question when the material genuinely has no order and the
  user has not named one. Otherwise pick the order yourself and start.

### Term definitions — the corrected vector definitions

The user holds these; restating them wrongly will be caught.

- **Geometric vector representation** carries the WHOLE journey: start point,
  end point, arrow between them. Position-independent — slide it anywhere.
- **Algebraic vector representation** carries ONLY the displacement: the delta
  components `(Δx, Δy)`, no position context. Two representations of the same
  vector, but different data, not a mere restatement.
- **A vector needs two points.** One point is geometry but not a vector; a
  vector is a displacement, `Q − P`. Do not define a geometric vector as "an
  arrow with length and direction" and separately call a single dot geometry in
  the same breath — that reads as a contradiction.
- **Magnitude** is length, written `besar` when the user wants Indonesian.
- Exponents do not cancel by division. `(√x)² = x` because √ and squaring are
  inverses; `a² = 32` is solved by `a = ±√32`.

### Language and register

- The user writes casual Indonesian and mixes it with English math terms. Reply
  in the same register; do not switch to formal English prose.
- Keep it tight. The user asks for direct teaching, not comprehensive coverage,
  and gets irritated by long preamble.
- Accept corrections immediately and move on — no defending, no extended
  apology paragraph, no restating what the user said back at them.

### Long-session degeneration

If a turn has already restated the same scaffolding twice, the next move is to
shorten and switch to a task, never to expand again. A turn that starts
repeating its own headings has lost the thread; stop, give one concrete problem,
and let the user's answer re-anchor the session.

## Video sourcing for a session's input block

See `references/sourcing-videos.md` for the verified curl pipeline (DuckDuckGo
lite → oEmbed verification → duration scrape) and the fetch-tool calls that do
not work on YouTube URLs.

## References

- The user's study repo follows AGENTS.md conventions for flat section files, specific sub-fields per quarter, and the 2-hour daily template with goal → input → practice → write structure.
- User explicitly rejected broad domains ("math" vs "linear algebra") and wants flat section files, no sub-folders, no plan.md inside sub-folders. State the honest "you finish X this quarter, the
  rest is Q2 backlog" framing in the entry doc — do not imply the whole roadmap
  fits.
- **Do not reference the source tool by name in the plan files.** The user does not
  want `roadmap.sh` (or similar) named inside their own study files — it reads as
  clutter and as dependence on a paid/limited external service. Name sections by
  topic ("S01 Vectors and Spaces"), and if a reference tree file is kept, call it
  by the field name only (e.g. `linear-algebra-reference.md`), never the source
  domain. The user corrected this explicitly.
- **Keep the content self-contained, not a verbatim dump.** Expand each section's
  subtopics and concepts into the section file's own checklist. Do not rely on a
  separate `roadmap-sh-*.md` full-tree file; if you save one, it is optional
  reference, and it must not be named after the source site.
- **Trim to the actually-reachable scope, and be honest about it.** A field studied
  one day per week in a 7-field rotation gets 1 two-hour session a week, so
  ~12 sessions in a quarter. That is the real cap, not "26 h per field." List
  only the sections that fit; the rest is a named Q2 backlog, not a promise. The
  user pushes back on keeping sections they cannot finish ("I only have 3
  months") — honor that and cut the stretch tier from the live curriculum.
- **Every field has an exit test** — a real benchmark, not "I feel done." No pass =
  stay on that field. End-of-quarter, fields are "done" when their exit test passes.
- **Keep a no-forgetting layer.** 2 h/week spaced review (Anki) of everything learned
  so earlier quarters don't decay. Monthly 1-h meta-review: what's decaying → add to
  Anki; what's strong → mark done.
- **Use free resources.** Khan Academy, 3Blue1Brown, CrashCourse, MIT OCW.

## Prose style (match on first draft, not on correction)

The user has an explicit writing standard for this repo — a repo AGENTS.md carries
the full rules and is the source of truth; read it before writing docs in that
repo. These are the parts most likely to be corrected:

- **No trailing parenthetical in a header.** Write `## Gap`, not
  `## Gap (what I still don't get)`; `## Study checklist`, not
  `## Study checklist (all concepts in this section)`. The user explicitly hates
  the `## Header (...)` pattern. Parens are fine mid-title as an example list
  (`## WEEK09 — Organelle detail (ER, Golgi, mitochondria)` is OK).
- **No emoji.** Ban by default.
- **Lead with the point; keep concrete facts.** No throat-clearing openers, puffery,
  or mic-drop endings. End on the last concrete point or next action.
- **No invented claims.** Don't add sources, stats, or examples that aren't in the
  material being edited.
- **Plain, active voice.** Use "is"/"has" when clearer; complete sentences; no
  synonym cycling; no dramatic binary contrasts ("not X, it's Y") or colon reveals.

## How to structure the deliverable (flat, per field)

Produce a filesystem structure, not one giant file. The user iterates on it:

```
Study/Q1/
├── README.md                  # index: Mon–Sun rotation table + Q2 unlock map + rules
└── NN-field-name/             # one folder per specific field
    ├── <Field>FieldDoc.md     # why-this-slice, resources, 2-h template, section map, exit test
    └── NN-section-name.md     # one FLAT file per reachable section, no sub-folder
```

- `<Field>FieldDoc.md` (e.g. `LinearAlgebra.md`, `BasicStatistics.md`) = overview +
  section table + exit test + a "what you actually finish this quarter" honest-
  pacing note. Name it after the field, not the source site.
- Each `NN-section-name.md` = that section's subtopics AND every concept under them,
  each as a `- [ ]` tick box, followed by a small **Plan / RESOURCE / PROJECT TASK /
  Notes** block the user can fill. These are FLAT files in the field folder — no
  sub-folder, no `plan.md` inside a sub-folder.
- Section count = what actually fits in the quarter (see the rotation-cap rule above).
  Drop the stretch tier from the live curriculum; name the remainder as the Q2
  backlog in the field doc.

An older layout used `WEEK01..WEEK12/` sub-folders and, later, one sub-folder per
section. Both are superseded. The flat-per-section-file layout is current. If you
find a field still in the old shape, migrate it when you touch it.

### The 2-hour session (3-part block, current template)

The user has moved from the earlier 4-part timed template to a simpler 3-part structure:

```
1. Input: learn the day's content (read, watch, work examples).
2. Solve problems on that topic until you can reproduce the method from memory.
3. Write an essay on what you learned.
```

Do not restore the old timed format (0:00–0:05 goal, 0:05–1:00 input, 1:00–1:50 practice, 1:50–2:00 write) or the "2–3 English sentences + 1 gap" output format — the user explicitly rejected both. Use this 3-part shape in all new and edited files.

Pitfall: don't write empty template shells — fill the solve step with
field-specific content. A future session should be able to open a section file
and start immediately.

## Procedure
1. Ask (via `clarify`) what the user is starting from, which domains, time budget,
   and goal. If already known, skip.
2. Pick the 7 specific sub-fields for the quarter in the user's priority order;
   design each to unlock a next-quarter field. Do NOT open a big CS/ML field in Q1
   if the user wants science-first — lay the prereqs instead.
3. Verify the hour budget honestly. The rotation cap is the binding number: one
   field/day across ~7 fields = 1 session/field/week = ~12 two-hour sessions
   (24 h) per field in a quarter, NOT the ~26 h theoretical max. Use ~12
   sessions to decide how many section-subtopics a field can genuinely cover, and
   say so in the field doc.
4. If the user points at a public roadmap (e.g. roadmap.sh), FETCH ITS FULL TREE
   and expand each section into a FLAT file in the field folder. See
   `references/public-roadmap-api.md` for how to pull the content. Then TRIM the
   section list to the quarter's reachable scope (rotation cap) and name the rest
   as Q2 backlog — do not keep sections the user cannot finish.
5. Scaffold the folder structure (see above). Generate many files with a Python
   script written to a `.py` file and run via terminal — DO NOT inline large nested
   dicts in `execute_code` (paren-matching errors on big literals are likely). Keep
   the generator script out of the deliverable folder (delete it after).
6. Update `README.md` to point into the field folders + give the Mon–Sun rotation
   and the Q2 unlock map.
7. Give the user a < 2 min "start now" action: open the field-1 first section file
   and do the first checklist item.

## Pitfalls
- **No context switching within a day** — the user's hard rule; the plan must make
  one field per day explicit, never two fields on the same day.
- **Broad fields are wrong for this user.** If a field is named after a whole
  discipline ("math", "biology", "physics"), split it into a specific sub-field.
- **Always end with a concrete start-now action**, not just the file tree.
- **Honest hour math.** Don't promise mastery of a whole discipline in 26 h; promise
  mastery of one specific slice, which is the point of the design.
- **Don't over-scope a field to its full source roadmap.** Expand every section of
  the public tree so nothing is lost, then cut the live curriculum to what the
  quarter's rotation cap can actually cover. The user pushes back on sections they
  cannot finish ("I only have 3 months"). List the remainder as a named Q2 backlog,
  never imply the whole tree fits.
- **Don't name the user's files after the source site.** No `roadmap.sh` in the
  tree; files are `<Field>FieldDoc.md`, `NN-section-name.md`, and optionally a
  field-named reference file.

## Reference example (Q1 fields this user used)
F1 linear algebra · F2 basic statistics · F3 molecular cell biology ·
F4 genetics · F5 classical mechanics · F6 technical English · F7 personal finance.
Each ~26 h; unlocks ML/data, biochem, E&M, technical reading, and economics in Q2.

