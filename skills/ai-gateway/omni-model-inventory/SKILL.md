---
name: omni-model-inventory
description: Build a model tier list from a local LLM gateway catalog.
metadata:
  tags:
    - ai-gateway
    - model-catalog
    - tierlist
---

# Local LLM Gateway Model Inventory & Tier Lists

Build a model inventory or tier list from a local gateway's `/v1/models` catalog. The gateway in play is OmniRoute (`localhost:7777`, OpenAI-compatible); the workflow is generic to any OpenAI-compatible local gateway.

## When to Use

- The user wants a **tier list** / capability ranking of the models available on a local LLM gateway.
- The user asks "what models do I actually have" / "list or rank the models" for OmniRoute or any OpenAI-compatible gateway.
- The user supplies a **specific shortlist of model names** (often prefixed with a gateway-provider slug like `yjs/...` or `myagnes/...`) and wants the tier list scoped to just that shortlist, not the whole catalog. Verify every name against the catalog before tiering — a provider-prefixed slug is the *provider connection* name plus the *root* model name, so match on the `root`, not the prefixed `id`.
- You need the full gateway catalog as input to decide which model or `auto/*` combo to use for a task.
- A referenced model-list file is garbled or never arrived and you must fall back to the authoritative catalog.
- The user asks whether the tiers rest on **real benchmark data**, or names a ranking source (OpenRouter, LMArena / "Arena LLM", lmsys, etc.) to check — see the "Benchmark sources" step; that question means the tiers need a data provenance, not just capability reasoning.

**Standing user spec for this task:** output a markdown table with columns exactly `Model | Tier | Cocok untuk` (third column is Indonesian, "suitable for"); tier scale S→A→B→C→D; an exclusion note up top; and write the file to a path the user can find (Desktop/Documents), not just stdout. Research, don't guess — when the model list the user referenced is garbled or missing, say so and pull the authoritative catalog from the gateway rather than fabricating one from partial names.

## Procedure

1. **Pull the live catalog.** `curl -s $OMNIROUTE_URL/v1/models -H "Authorization: Bearer $OMNIROUTE_KEY"`. Save the JSON to a scratch file — 1,000+ entries is too big to eyeball inline. If a referenced file is unreadable/never arrived, state it and use this as the source of truth.

2. **Group by `root`, not `id`.** Each entry has `id` (routable) and `root` (model family; many ids share one root). `root` is **absent on some entries** — group with `m.get("root") or m["id"]` or a bare `m["root"]` raises. The per-root count reveals the variant explosion to dedupe next.

3. **Drop out-of-scope entries:**
   - `owned_by == "combo"` → the `auto/*` router aliases (best-coding, pro-reasoning, ...), which are router entries, not models.
   - Image-model prefixes (e.g. `aihorde/*` Stable Diffusion) — not text models.
   - Utility models: embeddings (`*/text-embedding-*`, `bge-m3`), rerankers, ASR/transcribe (`nova-*`, `chirp*`, `voxtral*`, `parakeet*`), TTS.

4. **Dedupe variant suffixes per base model family** — one row per base model, not per variant. Fold away: `no-think/<model>` (same model, thinking off), `:free` / `:batch`, and thinking-budget suffixes `-low`/`-medium`/`-high`/`-xhigh`/`-max`/`-fast`.

5. **Tier the base models S→D by capability.** This is the judgment step — reason about each family's real capability, don't alphabetize. State the tier scale and exclusions in a short header.
   - If the user asked for a **specific shortlist**, tier only those models and label the tier scale as *relative within that set* — a top tier inside a small/open-weights shortlist is still below the gateway's flagship models in absolute terms; say so in a note so the tiers don't get misread.
   - If the user asks whether the tiers rest on real benchmark numbers, don't bluff — capability-based tiers are a heuristic, not cited data. Pull real numbers where they exist (see "Benchmark sources" step) and split the table into "model with a public benchmark score" vs "heuristic only", citing the source for each.

6. **Benchmark sources, when asked** (only needed if the user challenges the tiers or names a ranking site):
   - **OpenRouter** (`https://openrouter.ai/api/v1/models?order=top-weekly`) — public, no key, but the rank is **usage volume** (who people call most), not quality. It is a popularity proxy, not a benchmark — say that explicitly if you use it.
   - **LMArena / "Arena LLM"** (`lmarena.ai/leaderboard/text` — redirects to `arena.ai/leaderboard`) — real Elo from head-to-head human voting, and the right source to cite for a quality tier list. It's a client-side rendered table with no public API or `__NEXT_DATA__` payload — scrape it with the browser tool: navigate, scroll to the bottom in a loop until the row count stops growing (virtualized/paginated table), then dump `document.querySelectorAll('td')` to a workspace file and parse rows of 7 cells (`rank, rank-spread, model+lab, score±err, votes, price, context`). Many small/open-weights models on a personal gateway are *absent* from Arena (too few votes to chart); absence is not evidence of low quality — mark those rows "no public Arena data" instead of guessing.
   - **HuggingFace model cards** (`huggingface.co/api/models?search=<name>` to find the canonical repo, then fetch `<repo>/raw/main/README.md`) — this is the **primary** source for per-model vendor-reported benchmark numbers (SWE-bench Verified, GPQA Diamond, AIME, Terminal-Bench, LiveCodeBench, etc.), usually in a markdown or inline-HTML table in the README. When the user asks for "accurate benchmark data from the internet" (not just a popularity proxy), this is where the actual numbers live, not OpenRouter/Arena. Extract the table with the matching benchmark column, cite the exact repo URL per row, and **never invent a number the card doesn't print** — if the card only links out to a blog/external docs page for its numbers, or the table is an image (e.g. a "Benchmark Appendix" PNG), mark that row "needs vendor-source verification" instead of guessing a value. Some gated vendor orgs (e.g. meta-llama) 401 on direct fetch — retry via a community mirror repo (e.g. `unsloth/...`) for the README only. Vendor-reported numbers can overstate real-world quality — cross-check any surprising vendor score against an independent source (Arena Elo, BenchLM) before trusting it for a tier; note the discrepancy when it exists. An empty HF `search` result does not mean the model has no documentation — some vendors (e.g. InclusionAI) only publish via OpenRouter, not HuggingFace; fall back to the OpenRouter `/api/v1/models` full listing's `description` field for that model's architecture/specs before concluding "no public docs".
   - **BenchLM Data API** (`data.benchlm.ai/v1`, Bearer token, free tier = current data only, 1000 reads/month) — the only **independent composite benchmark** ("BenchAlign" score 0–100, multi-source) of the three. Endpoints: `GET /rankings/current` (top ~25, no query params — adding `limit`/`surface` params 400s), `GET /models?limit=100&offset=N` (catalog paginates at max 100/page up to offset 10000; ~889 models total as of Oct 2026), `GET /models/{slug}/rankings/current` (per-model overall/agentic/coding surface scores + ranks + evidence status). Catalog `query` param is the only accepted filter arg (`?query=agnes`); `q`/`search`/`name`/`term` all 400. A model can be in the catalog yet return 404 on its own rankings endpoint ("no current published BenchAlign ranking") — that's coverage sparsity, not a bug. **Pitfall: a large/flagship-sounding model can rank far below its size suggests on the independent composite** (e.g. a 550B model landing mid-pack) — always treat BenchLM rank as a sanity check on vendor claims, and flag the gap explicitly rather than silently dropping either source.
   - Cross-reference the shortlist against all four; anchor the tiering off independent scores (Arena Elo, BenchLM BenchAlign) where present, vendor model-card numbers as the per-model quality signal, usage rank as a secondary signal — and always state which source a tier rests on, so the user can see provenance per row.
   - Always emit a short "key findings / what changed from a heuristic pass" section when this is a second pass replacing an earlier capability-based table — the user's trust hinges on seeing exactly which models moved tier and *why*, with the citing source per row, not just a new table.

7. **Emit the user's spec table:** columns `Model | Tier | Cocok untuk`, one row per surviving base model.

8. **Close with the combo shortcut.** One line: most day-to-day use shouldn't hand-pick a model — `auto/best-coding` / `auto/pro-coding` route it. Then write the file and state its path.

## Benchmark sources beyond OpenRouter/Arena/HF (used when a third, independent score is needed)

**BenchLM Data API** (`data.benchlm.ai/v1`) — composite "BenchAlign" score 0–100, the only independent multi-source ranking of the three. Free tier: current data only, 1,000 reads/month, 30 req/min. See step 6's BenchLM entry for working endpoints, the pagination/query-param quirks, and the "catalog has the model but its own rankings endpoint 404s" coverage-sparsity case.

## Pitfalls

- **`root` is optional** — the #1 runtime error here is `KeyError: 'root'` when grouping; always `m.get("root") or m["id"]`.
- **Scope creep from the raw catalog** — ~1,600 entries collapse to ~60 base text model families. Skip the dedupe/exclusion step and you emit an unusable wall of variants. Always do steps 3–4 before tiering.
- **Never fabricate the inventory** from a garbled/partial attachment — pull from the gateway.
- **Inference vs management auth split** — `/v1/` accepts a narrow `self:usage` key; `/api/` needs the dashboard session or a `manage`-scope key. A 401/AUTH_001 from `/api/` with the inference key is expected, not a bug to chase, when all you need is `/v1/models`.
- **A shortlist uses provider-prefixed slugs** (`yjs/gpt-oss-20b`, `myagnes/agnes-3.0-flash`) that don't match the catalog's `id`/`root` exactly — match on the suffix/root, not the full prefixed string, or most names will falsely report "not found".
- **Never present a capability-based tier as benchmark data.** If the user asks "is this based on accurate benchmark data", own it: say plainly it's heuristic unless you've actually pulled Arena/OpenRouter/BenchLM numbers, and then cite which models did or didn't have public data — split the table into "model with an independent benchmark score" vs "vendor-number only" vs "heuristic only", not one merged table that hides provenance.
- **Vendor-reported benchmark numbers are self-published, not ground truth.** A model card's SWE-bench/GPQA/AIME table reflects the vendor's own harness and prompt setup; a smaller open-weights model can beat a larger "flagship" on one vendor benchmark while ranking far lower on an independent composite. When a vendor number and an independent score (Arena Elo, BenchLM BenchAlign) point to different tiers, surface the conflict explicitly in the "key findings" section rather than silently picking one — the user's trust depends on knowing a number's provenance (self-reported vs. independent).
- **Cross-source absence ≠ low quality, but ≠ data either.** A model missing from LMArena (too few votes to chart) or BenchLM (catalog sparsity, or 404 on its own rankings endpoint) has *no* public independent number — mark that row "no independent benchmark data" explicitly, never fill the gap by extrapolating from model size or vendor claims.

## Reference

`references/omniroute-models-shape.md` — the concrete `/v1/models` response shape and the full dedupe suffix list.
