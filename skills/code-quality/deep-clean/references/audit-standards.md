# Structural Audit Standards

Run the strict maintainability audit (the "code-judo" ambition) over the change. Altitude
and quality findings that land in the RISKY tier are escalated here before tiering is
finalized. Tone and output prioritization: [`review-tone.md`](review-tone.md).

## Non-Negotiable Audit Standards

0. **Be ambitious about structural simplification.** Do not stop at "this could be a bit
   cleaner." Look for opportunities to reframe the change so whole branches, helpers, modes,
   conditionals, or layers disappear. If a path deletes complexity rather than rearraging it,
   push hard for that path.
1. **Do not let a change push a file from under 1k lines to over 1k lines** without a very
   strong reason. Prefer extracting helpers, subcomponents, or modules; only waive with a
   compelling structural reason and a still-organized file.
2. **Do not allow random spaghetti growth.** Be highly suspicious of new ad-hoc conditionals,
   scattered special cases, or one-off branches in unrelated flows. Treat "weird if statements
   in random places" as a design problem; prefer a dedicated abstraction, helper, state
   machine, policy object, or separate module.
3. **Bias toward cleaning the design, not just accepting working code.** If behavior stays
   the same while structure becomes meaningfully cleaner, push for the cleaner version.
   Prefer simplifications that remove moving pieces altogether over refactors that spread
   the same complexity around.
4. **Prefer direct, boring, maintainable code over hacky or magical code.** Treat brittle,
   ad-hoc, or "magic" behavior as a code-quality problem. Flag thin abstractions, identity
   wrappers, or pass-through helpers that add indirection without clarity.
5. **Push hard on type and boundary cleanliness** where they affect maintainability. Question
   unnecessary optionality, `unknown`/`any`, or cast-heavy code when a clearer type boundary
   exists; prefer explicit typed models or shared contracts.
6. **Keep logic in the canonical layer and reuse existing helpers.** Call out feature logic
   leaking into shared paths or implementation details leaking through APIs; prefer canonical
   utilities over bespoke one-offs.
7. **Treat unnecessary sequential orchestration and non-atomic updates as design smells** when
   the cleaner structure is obvious. Flag independent work serialized for no reason, and
   related updates that leave state half-applied.

## Primary Audit Questions

For every meaningful change, ask:

- Is there a code-judo move that makes this dramatically simpler?
- Can this be reframed so fewer concepts, branches, or helper layers are needed?
- Does this improve or worsen the local architecture?
- Did the diff add branching complexity where a better abstraction should exist?
- Did a previously cohesive module become more coupled, more stateful, or harder to scan?
- Is this logic in the right file and layer?
- Did this change push a file or component past a healthy size boundary?
- Are there repeated conditionals that signal a missing model or missing helper?
- Is the implementation direct and legible, or does it lean on special cases and incidental
  control flow?
- Is this abstraction earning its keep, or just a wrapper?
- Did the diff introduce casts, optionality, or ad-hoc object shapes that obscure the real
  invariant?
- Is this logic in the canonical layer, or did the diff leak details across a boundary?
- Is this orchestration more sequential or less atomic than it needs to be?

## What to Flag Aggressively

- A complicated implementation where a cleaner reframing could delete whole categories of
  complexity.
- Refactors that move code around but fail to reduce the number of concepts a reader must
  hold.
- A file crossing 1000 lines due to the change, especially if the new code could be split
  out.
- New conditionals bolted onto unrelated code paths.
- One-off booleans, nullable modes, or flags that complicate existing control flow.
- Feature-specific logic leaking into general-purpose modules.
- Generic "magic" handling that hides simple structure.
- Thin wrappers or identity abstractions that add indirection without simplifying anything.
- Unnecessary casts, `any`, `unknown`, or optional params that muddy the real contract.
- Copy-pasted logic instead of extracted helpers.
- Narrow edge-case handling in the middle of an already busy function.
- Refactors that pass tests but make the code less modular or less readable.
- "Temporary" branching that will become permanent debt.
- Bespoke helpers where the codebase already has a canonical utility.
- Logic added in the wrong layer/package when it has a clear canonical home.
- Sequential async flow where obviously independent work could stay simpler with parallel
  execution.
- Partial-update logic that leaves state less atomic than necessary.

## Preferred Remedies

- Delete a whole layer of indirection rather than polishing it.
- Reframe the state model so conditionals disappear instead of getting centralized.
- Change the ownership boundary so the feature becomes a natural extension of an existing
  abstraction.
- Turn special-case logic into a simpler default flow with fewer exceptions.
- Extract a helper or pure function.
- Split a large file into smaller focused modules.
- Move feature-specific logic behind a dedicated abstraction.
- Replace condition chains with a typed model or explicit dispatcher.
- Separate orchestration from business logic.
- Collapse duplicate branches into a single clearer flow.
- Delete wrappers that do not meaningfully clarify the API.
- Reuse the existing canonical helper instead of a near-duplicate.
- Make type boundaries more explicit so control flow gets simpler.
- Move the logic to the package/module/layer that already owns the concept.
- Parallelize independent work when that also simplifies orchestration.
- Restructure related updates into a more atomic flow when partial state would be harder to
  reason about.

Do not settle for "maybe rename this" when the real issue is structural, or for a merely
cleaner version of the same messy idea when a much simpler one is plausible.

## Approval Bar

Do not approve merely because behavior seems correct. The bar is:

- no clear structural regression
- no obvious missed opportunity to make the implementation dramatically simpler when such a
  path is visible
- no unjustified file-size explosion
- no obvious spaghetti growth from special-case branching
- no obviously hacky or magical abstraction that makes the code harder to reason about
- no unnecessary wrapper/cast/optionality churn obscuring the real design
- no clear architecture-boundary leak or avoidable canonical-helper duplication
- no missed opportunity for an obvious decomposition that would materially improve
  maintainability

Presumptive blockers (the author must justify clearly):

- the change preserves a lot of incidental complexity when a plausible code-judo move would
  delete it
- the change pushes a file from below 1000 lines to above 1000 lines
- the change adds ad-hoc branching that tangles an existing flow
- the change solves a local problem by scattering feature checks across shared code
- the change adds an unnecessary abstraction, wrapper, or cast-heavy contract that makes the
  design more indirect
- the change duplicates an existing helper or puts logic in the wrong layer when there is a
  clear canonical home

If those conditions are not met, leave explicit, actionable feedback and push for a cleaner
decomposition.
