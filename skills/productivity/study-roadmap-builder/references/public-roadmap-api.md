---
metadata:
  hermes:
    tags:
      - learning
      - roadmap
      - web-scraping
    related_skills:
      - study-roadmap-builder
---

# Pulling public roadmap trees (roadmap.sh and similar JS apps)

## When to Use
When a study field's content should follow a public roadmap the user linked —
roadmap.sh, or any JS-rendered "AI roadmap" graph — and you need the full topic
tree to expand into the field's section folders.

## Core rule
Do NOT decompile the site's JavaScript bundles to find the data — that wastes a
lot of time. These apps load their roadmap through a small JSON API; fetch that
directly.

## roadmap.sh

The content is plain markdown, delivered by a public GET endpoint. The `data` field
is the full tree (`#` title, `##` sections, `###` subtopics, `-` concepts).

    # returns JSON: {_id, title, term, description, slug, data: <markdown>}
    curl -sL "https://roadmap.sh/api/v1-get-ai-roadmap/<slug>"

- `<slug>` is the last path segment of the URL, e.g.
  `https://roadmap.sh/ai/roadmap/linear-algebra-h4gkg` → slug `linear-algebra-h4gkg`.
- No auth / no API key for public slugs.
- Fetch from the shell or Python (`urllib.request`), parse with `json.loads`, then
  split `data` on `##` / `###` / `-` to build the per-section folders.

## Why direct API beats the alternatives
- `web_extract` / `fetch_readable` on the page URL returns almost nothing — the graph
  renders client-side from JS, so the HTML has no topic text.
- Decompiling the minified bundles to find the fetch endpoint works but is slow and
  brittle; the endpoint is trivially guessable from the versioned pattern
  (`/api/v1-get-<resource>/<slug>`).

## Pitfalls
- **Try the API before decompiling.** Grep the site's JS for `v1-` or `endpoint` only
  if a straight `curl` on the obvious API path 404s.
- **Do NOT name the user's files after the source site.** The user does not want
  `roadmap.sh` (or similar) appearing in their own study tree. Save the raw tree as
  `linear-algebra-reference.md` (field name only), or skip the reference file
  entirely and expand the content directly into the section checklists.
- **Trim to the reachable scope before writing section files.** The user studies
  one field per day in a 7-field rotation, so each field gets ~1 two-hour session
  per week (~12 sessions in a quarter). Cut the section list to what that can
  genuinely cover; list the remainder as a named Q2 backlog in the entry doc. The
  user actively pushes back on over-scoped plans ("I only have 3 months").
- **Parse the roadmap.sh tree in the correct order.** The markdown alternates
  leaf items and sub-topic labels: the sub-topic name (### line) comes AFTER its
  own leaf block. When you hit a `### X` line, the leaves collected since the
  previous `###` belong to `X`. Getting this backwards assigns concepts to the
  wrong sub-topic.
- Some slugs are user-owned/`private` and 404 to anonymous fetches; that's the signal
  to stop and ask the user, not to keep brute-forcing endpoints.
