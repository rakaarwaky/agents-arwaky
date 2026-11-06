# Wiki Schema

## Domain
General knowledge base — interlinked markdown notes.

## Conventions
- File names: lowercase, hyphens, no spaces (e.g., `transformer-architecture.md`)
- Every wiki page starts with YAML frontmatter
- Use `[[wikilinks]]` to link between pages (minimum 2 outbound links per page)
- When updating a page, always bump the `updated` date
- Every new page must be added to `index.md` under the correct section
- Every action must be appended to `log.md`
- Provenance markers: on pages synthesizing 3+ sources, append `^[raw/articles/source-file.md]` at the end of paragraphs whose claims come from a specific source

## Frontmatter
```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query | summary
tags: [taxonomy tags]
sources: [raw/articles/source-name.md]
confidence: high | medium | low
contested: true
contradictions: [other-page-slug]
---
```

## raw/ Frontmatter
Raw files in `raw/` are immutable — read-only. Corrections go in wiki pages, not in `raw/`.

## Directory Layout
- `SCHEMA.md` — this file
- `index.md` — navigational backbone, list of all pages
- `log.md` — action log
- `raw/` — immutable source material
- `_archive/` — retired pages
- `_meta/` — wiki metadata
