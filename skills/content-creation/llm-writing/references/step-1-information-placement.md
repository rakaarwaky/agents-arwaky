# LLM Writing — Step 1: Information Placement

Where each kind of information lives in the document. Design rules stay in `SKILL.md` Global Rules.

**Goal:** place every fact in exactly one location by its usage frequency, and omit what the reader can derive.

## Placement Table

| Info type | Location | Rule | Read when |
|-----------|----------|------|-----------|
| Needed on every task | Top of the text, or root doc (`AGENTS.md`, system prompt) | First cell ≤ 20 words. Put goal, commands, and hard constraints first | Always |
| Needed for one or more parts | Separate section or doc | Root lists it with a `Read when:` trigger; cell ≤ 20 words | When the section is not always needed |
| Derivable by the reader in one read | Omit | Do NOT restate obvious content or list every file | Never |

## Rules

- The root document is an index: one line per sub-doc with its `Read when:` trigger, never a restatement of the sub-doc content.
- A fact stated in two places fails the single-source-of-truth rule — one owner, the other becomes a reference by path or section name.
- Cells hold ≤ 20 words; move longer content to a code block or separate section.

## Completion

- Every fact has exactly one owner location.
- No section or doc without a `Read when:` trigger at the root.
- Nothing restated that the reader can derive in one read.
