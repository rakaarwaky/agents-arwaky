# LLM Writing — Step 1: Information Placement

Where each kind of information lives in the document. Design rules stay in `SKILL.md` Rules.

**Goal:** place every fact in exactly one location by its usage frequency, and omit what the reader can derive.

## Placement Table

| Info type | Location | Rule | Read when |
|-----------|----------|------|-----------|
| Needed on every task | Top of text, or root doc (`AGENTS.md`, system prompt) | Cell ≤ 20 words. Goal, commands, hard constraints first | Always |
| Needed for one or more parts | Separate section or doc | Root lists it with `Read when: <trigger>`; cell ≤ 20 words | Section is not always needed |
| Derivable in one read | Omit | `NEVER` restate obvious content or list every file | Never |
| Human-only content | Separate file, marked `Read when: human` | AI-facing rules first; human sections after the marker | Reader is mixed AI and human |

"Human-only content": README sections, `AGENTS.md` passages aimed at human readers. Move to a separate file or mark the section `Read when: human` so the agent skips it.

## Rules

- Root document is an index: one line per sub-doc with its `Read when:` trigger; `NEVER` restate the sub-doc content.
- A fact stated in two places fails Rule R4 — one owner, the other becomes a reference by path or section name.
- "One read" = one file read or one command output, as stated in `step-1` context.

## Completion

- Every fact has exactly one owner location.
- No section or doc without a `Read when:` trigger at the root.
- Nothing restated that the reader can derive in one read.
- Human-only content is isolated and marked.
- Every table cell holds ≤ 20 words (Eval 2).
