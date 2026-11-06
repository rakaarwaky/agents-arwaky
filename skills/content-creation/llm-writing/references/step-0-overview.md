# LLM Writing — Step 0: Overview

## Objective


| Field          | Value                                                       |
| -------------- | ----------------------------------------------------------- |
| Goal           | Text an AI agent acts on correctly with no prior context    |
| Reader         | AI agent, finite context window, zero organizational memory |
| Success metric | Fewest tokens that still let the agent act without guessing |
| Non-goal       | Persuasion, warmth, entertainment, narrative explanation    |

## W1–W7 Phase Map

| Phase | Step file                                         | Purpose                                         |
| ----- | ------------------------------------------------- | ----------------------------------------------- |
| W1    | `references/step-1-modes.md`                      | Mode selection: create or improve               |
| W2    | `references/step-2-information-placement.md`      | Where each fact lives; cell-width rule          |
| W3    | `references/step-3-rules-constraints.md`          | Keyword syntax, rule-row format, constraint budget |
| W4    | `references/step-4-size-cold-read.md`             | Size tiers, cold-read test                      |
| W5    | `references/step-5-system-patterns.md`            | System elements: diagram, dependency map, etc.  |
| W6    | `references/step-6-anti-patterns.md`              | Anti-pattern sweep; fix or log every hit        |
| W7    | `references/step-7-output-contract.md`            | Report: fields, verification, completion        |

## Read-when Routing

- Editing an existing file → start at step-1 (`improve` mode)
- Creating a new file → start at step-1 (`create` mode)
- Unsure where a fact belongs → step-2 placement table
- Unsure about a keyword → step-3 keywords
- Text over size limit → step-4 size tiers
- Describing systems or workflows → step-5 system patterns
- Pre-delivery sweep → step-6 anti-patterns
- Before sending output → step-7 output contract



