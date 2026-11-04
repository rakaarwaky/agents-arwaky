# Infographic — Output Layout

**Goal:** every run writes a predictable file tree under one topic slug.

## Directory Layout

```
infographic/{topic-slug}/
├── source-{slug}.{ext}
├── analysis.md
├── structured-content.md
├── prompts/infographic.md
└── infographic.png
```

## Slug Rules

- Slug: 2-4 words kebab-case from the topic.
- Conflict: if the directory exists, append `-YYYYMMDD-HHMMSS`.

## Core Principles

- Preserve source data faithfully — no summarization or rephrasing (but
  **strip any credentials, API keys, tokens, or secrets** before including
  in outputs).
- Define learning objectives before structuring content.
- Structure for visual communication (headlines, labels, visual elements).

## Pitfalls

1. **Data integrity is paramount** — never summarize, paraphrase, or alter
   source statistics. "73% increase" must stay "73% increase", not
   "significant increase".
2. **Strip secrets** — always scan source content for API keys, tokens, or
   credentials before including in any output file.
3. **One message per section** — each infographic section should convey one
   clear concept. Overloading sections reduces readability.
4. **Style consistency** — the style definition from the references file
   must be applied consistently across the entire infographic. Don't mix
   styles.
5. **image_generate aspect ratios** — the tool only supports `landscape`,
   `portrait`, and `square`. Custom ratios like `3:4` should map to the
   nearest option (portrait in that case).

## Completion

- The output directory exists with all five artifacts.
- No source credentials, keys, or tokens appear in any output file.
