# Step 1 — Overview

## Objective

Minimum tokens, exact names, zero AI slop. Fix only: AI slop, concision, clarity.

## Mode dispatch


| Input       | Mode                                |
| ----------- | ----------------------------------- |
| `--create`  | Create: write a new doc first draft |
| `--improve` | Improve: edit in place              |


## Scope

1. **AI slop** — filler, hedging, boilerplate, restated introductions.
2. **Concision** — duplicate facts, nominalizations, padding.
3. **Clarity** — vague references, missing exact names, hidden actors.

## Boundary

- **In:** filler and hedging, boilerplate openers and summaries, duplicated facts, vague references, nominalizations, passive voice that hides the actor.
- **Out:** tone and voice, persuasion or branding, structure rewrites, fact or code changes, formatting, translation, grammar fixes that save no tokens and remove no ambiguity.
- A requested fix that is out of scope: log `CONFLICT: <request>` and stop.

