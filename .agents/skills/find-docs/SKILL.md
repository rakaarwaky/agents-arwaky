---
name: find-docs
description: Fetches library docs and examples via ctx7. Use when asking API syntax, config, migration, usage.
metadata:
  tags: []
---

# Documentation Lookup

Two transports, same two-step workflow (resolve an ID, then query). Use whichever
the current harness has:

| Transport | Use when | Steps |
|-----------|----------|-------|
| **MCP tools** | `resolve-library-id` / `query-docs` are available (e.g. `mcp__context7__*`) | Call the tools directly — no shell, no install |
| **ctx7 CLI** | No MCP server in this harness, or you want docs without restarting | `npx ctx7@latest library …` then `npx ctx7@latest docs …` |

Never silently fall back to training data: if both transports fail, say that
Context7 was unavailable and flag the answer as unverified.

## Step 1: Resolve the library ID

```bash
# MCP: resolve-library-id(libraryName="Next.js", query="app router middleware setup")
npx ctx7@latest library "Next.js" "How to set up app router with middleware"

```text

Skip this step only when the user already gave an ID in `/org/project` or
`/org/project/version` form.

Use the official library name with proper punctuation ("Next.js" not "nextjs",
"Customer.io" not "customerio"). If results look wrong, try alternate spellings
(`next.js`) before changing the query. Always pass a `query` — it is required and
directly affects ranking; form it from the user's intent, and never include
secrets, credentials, or proprietary code (it is sent to the Context7 API).

Each result carries: library ID (`/org/project`), name, description, code-snippet
count, source reputation (High/Medium/Low/Unknown), benchmark score (100 = best),
and available versions.

**Selecting among matches:** prioritize the exact name the user asked for, then
official/primary packages over community forks, then documentation coverage
(more snippets), then higher benchmark score. If the user mentioned a version
("React 19"), prefer a version-specific ID. If several are equally plausible,
say so and proceed with the most relevant; if none are, state that and suggest a
query refinement rather than guessing.

## Step 2: Query the documentation

```bash
# MCP: query-docs(libraryId="/vercel/next.js", query="app router middleware setup")
npx ctx7@latest docs /vercel/next.js "How to add authentication middleware to app router"

```text

Be specific, and keep one concept per query. If the question spans several
concepts (routing *and* auth *and* caching), resolve once then make a separate
call per concept — unless the question is about how they interact, in which case
one combined query is right. Describe what to look up in the docs, not the task.

| Quality | Example |
|---------|---------|
| Good | `"How to set up authentication with JWT in Express.js"` |
| Good | `"React useEffect cleanup function with async operations"` |
| Bad (too vague) | `"auth"`, `"hooks"` |
| Bad (too broad) | `"routing and auth and caching in Next.js"` |

Results contain titled, language-tagged code snippets and prose "info" snippets
with breadcrumb context. Cite the library ID you used, quote code verbatim where
relevant, and name the version when it matters.

## Limits and failures

- **At most 3 calls per question** (across resolve + query). If you still lack an
  answer, use the best result and say what is missing.
- **Quota errors** ("Monthly quota reached", "quota exceeded"): tell the user
  their Context7 quota is exhausted, suggest `npx ctx7@latest login` (or an MCP
  re-auth) for higher limits, and only then answer from knowledge — labelled as
  possibly outdated.
- **Auth errors:** set `export CONTEXT7_API_KEY=…` (get a key at
  https://context7.com/dashboard); most calls work without it.

## Common mistakes

- Library IDs need the `/` prefix — `/facebook/react`, not `facebook/react`.
- Running `docs` first — it fails without a valid ID resolved in step 1.
- One-word queries, or multi-topic queries that dilute ranking.
- Passing sensitive data in `query`.
- Reporting a docs-derived answer as current without naming the library ID/version.

## Related

- `context7-cli` — install `ctx7`, `ctx7 setup` MCP wiring for Claude Code /
  Cursor / OpenCode, and `ctx7 skills …` registry management.
