# Step 1 — Overview

## Objective

Minimum tokens, exact names, zero AI slop. Fix only: AI slop, concision, clarity.

## Mode dispatch

| Input | Mode |
|-------|------|
| `--create` + task and source files | Create: write a new doc from the step-3 skeleton, rules R1–R4 from the first draft. |
| `--improve`, an existing path, inline text, or no flag | Improve: edit in place, apply steps 2–4. |

## Scope boundary

- **In:** filler and hedging, boilerplate openers and summaries, duplicated facts, vague references (`it`, `the config`, `several`), nominalizations, passive voice that hides the actor.
- **Out:** tone and voice, persuasion or branding, structure rewrites, fact or code changes, formatting, translation, grammar fixes that save no tokens and remove no ambiguity.
- A requested fix that is out of scope: log `CONFLICT: <request>` and stop.

