# `GET /v1/models` response shape (OmniRoute / OpenAI-compatible)

Save the raw JSON to a scratch file before processing; it's ~1,600+ entries on a busy gateway.

## Fields per entry

- `id` — the routable id (what goes in a chat completion's `model` field).
- `root` — the model family with variant suffix stripped; many `id`s share one `root`.
  **Optional — absent on some entries.** Group with `m.get("root") or m["id"]`.
- `owned_by` — `provider` | `combo` | `node`. `combo` = the `auto/*` router aliases.
- `context_length`, `max_input_tokens`, `max_output_tokens`.
- `input_modalities` / `output_modalities` — `["text"]`, or `+ "image"` for vision.
- `capabilities` — `{tool_calling, reasoning, thinking, temperature, vision}` booleans.

Not every entry carries every field.

## Grouping keys

- **Vendor prefix** on `root`/`id`: `anthropic/`, `openrouter/`, `aihorde/`, and bare
  `claude-*` / `gpt-*` / `gemini-*` (the gateway's normalized vendor ids).
- **Exclusion prefix sets:**
  - `owned_by == "combo"` → `auto/*` router aliases.
  - `aihorde/*` → Stable Diffusion image models (not text).
  - Utility: `*/text-embedding-*`, `bge-m3`, `*rerank*`, ASR/transcribe `nova-*`,
    `chirp*`, `voxtral*`, `parakeet*`, TTS families.

## Variant suffixes to fold (one row per base family)

- `no-think/<model>` — same model, thinking disabled.
- `:free`, `:batch` — pricing-mode suffixes.
- `-low` / `-medium` / `-high` / `-xhigh` / `-max` / `-fast` — thinking-budget variants
  of the same base model.

## Where each source lives

- OpenRouter usage-rank: `https://openrouter.ai/api/v1/models?order=top-weekly` (public, no key).
- LMArena: `lmarena.ai/leaderboard/text` (client-rendered, no API — browser-scrape, see model-tier-list.md step 6).
- HuggingFace model cards: `huggingface.co/api/models?search=<name>` → `<repo>/raw/main/README.md` (vendor-reported numbers).
- BenchLM Data API: `data.benchlm.ai/v1` (Bearer key, independent composite score; free tier = current data only; see model-tier-list.md step 6 for working endpoints and the catalog/rankings-404 coverage-sparsity quirk).
