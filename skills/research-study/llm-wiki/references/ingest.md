# Ingest — LLM Wiki

When the user provides a source (URL, file, paste), integrate it into the
wiki:

① **Capture the raw source:**
- URL → use `web_extract` to get markdown, save to `raw/articles/`
- PDF → use `web_extract` (handles PDFs), save to `raw/papers/`
- Pasted text → save to appropriate `raw/` subdirectory
- Name the file descriptively: `raw/articles/karpathy-llm-wiki-2026.md`
- **Add raw frontmatter** (`source_url`, `ingested`, `sha256` of the body).
  On re-ingest of the same URL: recompute the sha256, compare to the stored
  value — skip if identical, flag drift and update if different. This is
  cheap enough to do on every re-ingest and catches silent source changes.

② **Discuss takeaways** with the user — what's interesting, what matters for
the domain. (Skip this in automated/cron contexts — proceed directly.)

③ **Check what already exists** — search `index.md` and use `search_files` to
find existing pages for mentioned entities/concepts. This is the difference
between a growing wiki and a pile of duplicates.

④ **Write or update wiki pages:**
- **New entities/concepts:** Create pages only if they meet the Page
  Thresholds in `SCHEMA.md` (2+ source mentions, or central to one source)
- **Existing pages:** Add new information, update facts, bump `updated`
  date. When new info contradicts existing content, follow the Update
  Policy.
- **Cross-reference:** Every new or updated page must link to at least 2
  other pages via `[[wikilinks]]`. Check that existing pages link back.
- **Tags:** Only use tags from the taxonomy in `SCHEMA.md`
- **Provenance:** On pages synthesizing 3+ sources, append
  `^[raw/articles/source.md]` markers to paragraphs whose claims trace to
  a specific source.
- **Confidence:** For opinion-heavy, fast-moving, or single-source claims,
  set `confidence: medium` or `low` in frontmatter.

⑤ **Update navigation:**
- Add new pages to `index.md` under the correct section, alphabetically
- Update the "Total pages" count and "Last updated" date in index header
- Append to `log.md`: `## [YYYY-MM-DD] ingest | Source Title`
- List every file created or updated in the log entry

⑥ **Report what changed** — list every file created or updated to the user.

A single source can trigger updates across 5–15 wiki pages. This is normal
and desired — it's the compounding effect.
