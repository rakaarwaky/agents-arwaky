# Deliverable Structure — Study Roadmap Builder

Produce a filesystem structure, not one giant file. The user iterates on
it:

```
Study/Q1/
├── README.md                  # index: Mon–Sun rotation table + Q2 unlock map + rules
└── NN-field-name/             # one folder per specific field
    ├── <Field>FieldDoc.md     # why-this-slice, resources, 2-h template, section map, exit test
    └── NN-section-name.md     # one FLAT file per reachable section, no sub-folder
```

- `<Field>FieldDoc.md` (e.g. `LinearAlgebra.md`, `BasicStatistics.md`) =
  overview + section table + exit test + a "what you actually finish this
  quarter" honest-pacing note. Name it after the field, not the source
  site.
- Each `NN-section-name.md` = that section's subtopics AND every concept
  under them, each as a `- [ ]` tick box, followed by a small
  **Plan / RESOURCE / PROJECT TASK / Notes** block the user can fill.
  These are FLAT files in the field folder — no sub-folder, no `plan.md`
  inside a sub-folder.
- Section count = what actually fits in the quarter (see the rotation-cap
  rule in SKILL.md Global rules). Drop the stretch tier from the live
  curriculum; name the remainder as the Q2 backlog in the field doc.

An older layout used `WEEK01..WEEK12/` sub-folders and, later, one
sub-folder per section. Both are superseded. The flat-per-section-file
layout is current. If you find a field still in the old shape, migrate it
when you touch it.

## The 2-hour session (3-part block, current template)

The user has moved from the earlier 4-part timed template to a simpler
3-part structure:

```
1. Input: learn the day's content (read, watch, work examples).
2. Solve problems on that topic until you can reproduce the method from memory.
3. Write an essay on what you learned.
```

Do not restore the old timed format (0:00–0:05 goal, 0:05–1:00 input,
1:00–1:50 practice, 1:50–2:00 write) or the "2–3 English sentences + 1 gap"
output format — the user explicitly rejected both. Use this 3-part shape in
all new and edited files.

Pitfall: don't write empty template shells — fill the solve step with
field-specific content. A future session should be able to open a section
file and start immediately.
