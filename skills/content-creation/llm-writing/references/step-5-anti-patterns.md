# LLM Writing — Step 5: Anti-Patterns, Template, Pre-Delivery Checklist

The fix table for common defects, the minimal document template, and the gate before delivery.

**Goal:** zero anti-patterns in the delivered text; template filled; every checklist row passes.

## Anti-Patterns

| Anti-pattern | Fix |
|---|---|
| Conversational tone ("Welcome!", "Let's dive in") | Delete |
| Idioms, metaphors, sarcasm | Replace with literal statements |
| Multi-paragraph "why" essays | State what and how. Add a 1-line Why only where non-obvious |
| Task buried after background | Move goal and hard constraints to the top |
| Unstated output format | State format, length, and structure of the expected output |
| External link without local summary | Summarize payload in a table. Link as supplement |
| Same fact in multiple places | Keep in one owner location. Reference it |
| Prose for structured data | Convert to table, YAML, or JSON |
| Vague references ("the script", "recently") | Use exact path, version, or date |
| Undefined acronym or project term | Define once in a Glossary table |
| Unverified command, path, or number | Run or check it. Else mark `UNVERIFIED` |
| Everything in ALL CAPS | Capitalize only `MUST`, `NEVER`, `ALWAYS`, `ONLY` |
| Table cells with paragraphs | Shorten to a phrase. Move long content to a code block or separate section |
| Restating what the reader can derive in one read | Keep only non-obvious facts and entry points |
| Unreplaced placeholders (`<TODO>`, `...`) | Fill in or write `UNKNOWN` |
| Silent conflict resolution | Ask the user which source is correct |

## Minimal Template

```markdown
# <Title>

## Purpose
<One line: task served and what the agent must do after reading>

## Context
| Item | Value |
|---|---|

## Steps
| Step | Action | Expected |
|---|---|---|

## Rules
| ID | Rule | Why | Check |
|---|---|---|---|

## Related
| Resource | Read when |
|---|---|
```

## Pre-Delivery Checklist

| Check | Pass condition |
|---|---|
| Fluff | Zero greetings, transitions, marketing phrases |
| Order | Purpose and hard constraints appear before details |
| Structure | Heading hierarchy has no skipped levels |
| References | Every path, name, number, and link matches the source |
| Commands | Every command ran, or is marked `UNVERIFIED` |
| Output | Expected output format is stated |
| Duplication | No fact stated twice |
| Rules | Every `MUST` / `NEVER` has a Check. Count ≤ 10 per text |
| Gaps | No placeholders. Unknowns marked `UNKNOWN` |
| Conflicts | All source conflicts resolved by the user |
| Relevance | Every section holds an actionable fact for the stated purpose. Delete the rest |

## Completion

- The anti-pattern table is swept top-to-bottom against the text; every hit is fixed.
- The minimal template is filled or every deviation is justified by the source material.
- All 11 checklist rows pass before the Output Contract report is sent.
