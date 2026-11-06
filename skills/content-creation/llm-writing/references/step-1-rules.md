# LLM Writing — Overview

## Objective

| Field | Value |
|-------|-------|
| Goal | Create concise docs, or shorten existing docs, while keeping actionable facts. |
| Reader | AI agent with finite context and no prior organizational memory. |
| Success metric | Fewer tokens, clearer actions, zero AI slop, no lost facts. |
| Non-goal | Persuasion, warmth, entertainment, narrative, branding, fiction, or unrelated style issues. |

## Modes

| Mode | Output |
|------|--------|
| `create` | Goal, Trigger, Inputs, Steps, Outputs, Done. |
| `improve` | Diff, Removed, Size before/after. |

- `IF` `--dry-run` `THEN` write nothing; report diff.
- Before `improve` write, create `<path>.bak`; restore on validation failure, delete on pass.