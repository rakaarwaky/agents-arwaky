---
name: llm-wiki
description: "Karpathy's LLM Wiki: build/query interlinked markdown KB."
when-to-use: Use when the user asks to create, build, or start a wiki, ingest a source into a wiki, ask a question about an existing wiki, or lint/audit/health-check a wiki.
argument-hint: "<init | ingest | query | lint> [wiki-path | source]"
version: 2.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [wiki, knowledge-base, research, notes, markdown, rag-alternative]
    category: research
    related_skills: [arxiv]
---

# Karpathy's LLM Wiki

Build and maintain a persistent, compounding knowledge base as interlinked
markdown files. Based on
[Andrej Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
Unlike traditional RAG (which rediscovers knowledge from scratch per query),
the wiki compiles knowledge once and keeps it current. Cross-references are
already there. Contradictions have already been flagged.

**Division of labor:** The human curates sources and directs analysis. The
agent summarizes, cross-references, files, and maintains consistency.

## Global rules

- **Orient every session before any operation.** Read `SCHEMA.md` +
  `index.md` + recent `log.md` entries first — see
  [`references/resuming-wiki.md`](references/resuming-wiki.md). Skipping this
  causes duplicates and missed cross-references.
- **`raw/` is immutable.** The agent reads but never modifies files in
  `raw/`. Corrections go in wiki pages, not in the source.
- **Always update `index.md` and `log.md`** after any operation — these are
  the navigational backbone. Skipping this makes the wiki degrade.
- **Page threshold.** Don't create pages for passing mentions — follow the
  Page Thresholds in `SCHEMA.md`. Every new page must link to at least 2
  other pages via `[[wikilinks]]`; isolated pages are invisible.
- **Tags come from the taxonomy** in `SCHEMA.md`. Add new tags to
  `SCHEMA.md` first, then use them — freeform tags decay into noise.
- **Confidence frontmatter.** For opinion-heavy, fast-moving, or
  single-source claims, set `confidence: medium` or `low`. Don't mark
  `high` unless well-supported across multiple sources.
- **Rotate the log.** When `log.md` exceeds 500 entries, rename it
  `log-YYYY.md` and start fresh. The agent should check log size during
  lint.
- **Handle contradictions explicitly** — don't silently overwrite. Note
  both claims with dates, mark in frontmatter, flag for user review.
- **Ask before mass-updating** — if an ingest would touch 10+ existing
  pages, confirm the scope with the user first.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Orient (every session) | [`references/resuming-wiki.md`](references/resuming-wiki.md) | Read `SCHEMA.md` + `index.md` + recent `log.md`; do this before ingesting, querying, or linting. |
| Init new wiki | Create directory structure + `SCHEMA.md` + `index.md` + `log.md` (templates in [`references/schema-templates.md`](references/schema-templates.md)) | Path from `$WIKI_PATH` env var (default `~/wiki`); ask the user what domain the wiki covers; write the three initial files; confirm ready. |
| Ingest | [`references/ingest.md`](references/ingest.md) | Capture raw source → discuss takeaways → check what exists → write/update pages (with cross-refs, provenance, confidence) → update nav → report changes. |
| Query | [`references/query.md`](references/query.md) | Read `index.md` → search for key terms (wikis with 100+ pages) → read relevant pages → synthesize → file valuable answers back to `queries/` or `comparisons/` → update `log.md`. |
| Lint | [`references/lint-checklist.md`](references/lint-checklist.md) | Full 13-point checklist: orphan pages, broken wikilinks, index completeness, frontmatter validation, stale content, contradictions, quality signals, source drift, page size, tag audit, log rotation, report findings, append to log. |
| Working with the wiki | [`references/working-with-wiki.md`](references/working-with-wiki.md) | Searching, bulk ingest, archiving, Obsidian integration, headless setup. |
| Obsidian headless | [`references/obsidian-headless.md`](references/obsidian-headless.md) | On headless machines, use `obsidian-headless` instead of the desktop app; syncs vaults via Obsidian Sync without a GUI. |
| Related tooling | [llm-wiki-compiler](https://github.com/atomicmemory/llm-wiki-compiler) | Node.js CLI that compiles sources into a concept wiki; Obsidian-compatible; use it for scheduled batch compile, this skill for agent-in-the-loop curation. |
