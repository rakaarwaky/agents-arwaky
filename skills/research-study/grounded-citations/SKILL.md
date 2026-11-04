---
name: grounded-citations
description: Ground answers and documents in cited, verifiable sources.
when-to-use: Use whenever an answer or artifact rests on information you fetched rather than knew, and needs inline numbered citations plus a verifiable Sources block.
argument-hint: "<reset | add | list | render | verify | quote | ingest> [urls | id | path | draft] [--title | --accessed | --json | --ledger | --style | --only | --cited-in | --replace-in | --strict | --min-coverage | --evidence | --text | --from]"
metadata:
  tags:
    - Research
    - Citations
    - Grounding
    - Sources
    - Web
    - Reports
  related_skills:
    - arxiv
    - pdf
  category: research
---

# Grounded Citations

Every claim taken from an outside source gets an inline numbered citation and a
`Sources:` list, Perplexity-style. A ledger script owns the `url → [n]`
mapping so the numbers and URLs come from retrieval, never from memory — the
model only ever emits small integers it was handed.

For high-stakes work the same ledger doubles as a fact-checking chain:
verbatim quotes are attached to each source (rejected unless they literally
appear in the fetched page text), claims from model knowledge are flagged
`[unverified]`, and `verify --evidence` fails any draft whose cited sources
carry no evidence.

This skill covers answers in chat, written documents (markdown, PDF, docx,
slides), and research reports. It does not cover academic BibTeX pipelines.

## Global rules

- **No prerequisites beyond the standard toolset.** `scripts/sources.py` is
  stdlib-only Python 3. Retrieval comes from whatever is configured:
  `web_search`, `web_extract`, `browser_navigate`, or `terminal`.
- **Ledger location.** `$HERMES_HOME/cache/citations/ledger.json`
  (profile-aware). Override per task with `--ledger <path>` or
  `HERMES_CITATION_LEDGER`.
- **`add` is idempotent and URL-normalized** — the same page always returns
  the same id within a ledger, so ids stay stable across many
  search/extract rounds.
- **Inline citation form.** No space before the bracket; each id in its own
  brackets; max 3 ids per sentence; cite per sentence, not one dump at the
  end. Only ids the ledger returned — never invent an id or a URL. Claims
  from your own knowledge get no citation. Conflicting sources: present both
  readings, each with its own id. Quote exact figures, dates, and names as
  the source states them; flag gaps explicitly ("no source found for X")
  instead of smoothing them over.
- **Append the Sources block mechanically** with `sources.py render
  --cited-in <draft>` — never retype URLs by hand.
- **Skip inline citations** when the retrieval is incidental to another task
  — a quick syntax/version lookup mid-coding, casual conversation, creative
  writing. Mention a URL only if the user would plausibly want the link.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Ledger commands | `scripts/sources.py` — `reset`, `add <url> [--title T]`, `ingest results.json`, `quote <id> --text "..." --from page.txt`, `list [--json]`, `render [--style markdown\|plain\|footnotes\|bibtex\|evidence] [--only 1,3] [--cited-in draft.md] [--replace-in draft.md]`, `verify draft.md [--strict] [--min-coverage 0.6] [--evidence]` | The full command surface; resolve the pack root via the loop in `references/how-to-run.md`. |
| Run the script | [`references/how-to-run.md`](references/how-to-run.md) | The pack-root resolution loop that locates `sources.py` across `~/.hermes`, `~/.qwen`, `~/.config/opencode`, and `~/agents-arwaky` skill trees. |
| Procedure (①–⑥) | [`references/procedure.md`](references/procedure.md) | The 6-step workflow: reset → register at retrieval time → cite-while-drafting → render block → verify → chat answers. |
| Non-markdown targets | [`references/citation-formats.md`](references/citation-formats.md) | Placing the block in docx footnotes, LaTeX endnotes, deck source slide. |
| Citation wording / ledger mechanics | [`references/grounding-rationale.md`](references/grounding-rationale.md) | Read before changing citation wording or ledger mechanics. |
| Fact-checking mode | [`references/fact-checking-mode.md`](references/fact-checking-mode.md) | Attach verbatim quotes, flag `[unverified]` claims, cross-check disputed facts, `--evidence` gate. |
| Pitfalls | [`references/pitfalls.md`](references/pitfalls.md) | Registering after writing, renumbering mid-task, retyping URLs, snippet-citation, over-citing, parallel subagents, evidence-quote rules. |
| Verification | `python "$S" verify report.md --strict --min-coverage 0.5` | Green = every `[n]` in the draft exists in the ledger, the Sources block lists exactly the cited ids, and the cited share meets the threshold. Read warnings even on exit 0. |
