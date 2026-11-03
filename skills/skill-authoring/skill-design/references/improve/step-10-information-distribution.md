# Improve — Step 10: Information distribution

Before editing any fact, route it with the test below. A fact that has more than one home is a bug; one home per fact (Global Rules). This is the check that catches a definition file that should have been split into the Global Rules + step files that use it.

### The test

For each fact, ask one question: **how many steps read this fact during a single invocation?**

- **More than one step (or all steps)** → `SKILL.md` Global Rules. Cross-step policy, signal definitions, invariants, record formats.
- **Exactly one step** → that step's reference file. Commands, field shapes, per-action rules, stop conditions, worked examples.
- **Neither — the fact is a shared definition used by several pipeline skills** (the trace pipeline's `signals` definitions, `report-format` shapes, …) → it is a shared reference, not owned by any one step. In this pack the shared definition is inlined into the consuming skill's step file (as in the trace-pipeline skill `skill-traces`, which carries one `step-3-read-report.md`, `step-4-apply.md`, and `step-5-verify.md` covering all three modes); the standalone shared file is deleted, not kept. A standalone `references/<name>.md` linked from several consumers is legitimate only when the fact genuinely has no per-skill step home — which in this pack means a new shared pipeline has not yet been created.

### Rules

- **Learned mistake (do not repeat).** When inlining a shared definition into a consuming skill's step file, the step file that gains the content must name the file it absorbed by reference, and the standalone file must be deleted in the same edit. The mistake that produced this rule: the trace skill's `signals.md`, `report-format.md`, and `apply-rules.md` were inlined into `step-1`, `step-3`, and `step-4` respectively, but the three standalone files were left on disk and still linked from `SKILL.md` — creating second copies. The check that catches it: after inlining, grep the skill's `SKILL.md` and step files for the deleted filename; every hit is a dangling link and a second copy, and the edit is incomplete until both are removed.
- A Global Rules bullet that fully defines a signal, action type, or invariant is the home for it; a step file that repeats that definition in full is the second copy. Point at the bullet, do not restate it.
- A step file may reference the Global Rules bullet by name; it does not restate the bullet's content.
- The shared-reference case (third rule above) is the only situation where a non-step `references/<name>.md` is legitimate in a Pattern B pipeline; name it in the `SKILL.md` Routing table and link it from the step that consumes it.
