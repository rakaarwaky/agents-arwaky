# Publish Procedure (design reference)

Extracted from `SKILL.md` Step 6d so the main body stays compact. Read this file when running the `/design` skill with `--publish`.

Run this step only when `publish` is `true`. Otherwise skip it, leave `published_url` empty, and report the local path only. The design document may be confidential; never upload it anywhere the user did not ask for.

Publish **after** 6b (so any user answers are already in the file). The local `<design_doc_file>` stays the source of truth. Publish is a copy, not a rewrite of that file.

Title: the document's first `#` heading. If there is none, use a short phrase from the user's `/design` argument.

**Do not hardcode integration tool names or argument shapes.** Discover them at runtime, then call only a name and schema you just retrieved. Tool names change. Guessing a stale name is a failed publish.

Discovery order (use the first mechanism that exists in this session):
1. The MCP discovery tool (`search_tool` or equivalent) with a capability query.
2. `grok-mcp ls --query "<capability>"` (see the `mcp` skill if it is loaded).
3. Whatever other tool catalog this session exposes.

Capability queries (intent, not a name):
- Notion: create a new page whose body is markdown.
- Notion parent: search or fetch a page if the user named one.
- Gist fallback: create a **secret/private** gist from a markdown file.

For each match, read that tool's **current** input schema and fill it from the title and the contents of `<design_doc_file>`. Prefer a private/workspace page over a public one. If the user named a Notion parent, discover a search/fetch tool the same way, resolve the parent, then pass whatever parent field the create schema asks for. If they did not name a parent, omit parent fields unless the schema requires one.

1. Try Notion. If discovery finds no create-page tool, or the call errors or times out, treat Notion as unavailable.
2. Then try a secret gist via a discovered gist tool. If none exists, use the host gist CLI if present (secret/private flag). Never create a public gist.
3. Store the returned URL as `published_url`. If both fail, leave it empty, keep the local path, and say so in the Final Report. Do not fail the design run.
4. Do not publish a second time in the same run. If this step already produced a URL, reuse it.

When `publish` is `true`, this step is mandatory whenever the write-review loop produced a final document.
