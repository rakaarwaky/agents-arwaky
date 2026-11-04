---
name: baoyu-infographic
description: "Infographics: 21 layouts x 21 styles (信息图, 可视化)."
when-to-use: "Use when the user asks for an infographic, visual summary, or information graphic — they provide content (text, file, URL, topic) and optionally layout, style, aspect ratio, or language. Triggers include 信息图, 可视化, 高密度信息大图."
argument-hint: "<topic> [layout] [style] [aspect] [language]"
---

# Baoyu Infographic

You create infographics by combining two free dimensions — **layout**
(information structure, 21 options) and **style** (visual aesthetics, 21
options) — into one `image_generate` prompt over the user's content, preserving
the source data verbatim.

## Global Rules

- **Defaults.** Layout default `bento-grid`, style default `craft-handmade`;
  keyword shortcuts and recommended combinations are owned by
  [`references/recommendations.md`](references/recommendations.md).
- **Options and galleries.** Named options (layout, style, aspect, language)
  and the full 21×21 galleries:
  [`references/options.md`](references/options.md).
- **Output layout.** Every run writes to
  `infographic/{topic-slug}/` — slug rules and the file tree are owned by
  [`references/output.md`](references/output.md).
- **Data integrity.** Preserve source data faithfully — no summarization or
  rephrasing ("73% increase" stays "73% increase").
- **Strip secrets.** Remove credentials, API keys, tokens, or secrets from
  every output file.
- **Style consistency.** Apply one style definition across the entire
  infographic; never mix styles.
- **Completion.** `prompts/infographic.md` is assembled, `image_generate`
  returned an image, and the step 7 summary (topic, layout, style, aspect,
  language, output path) was reported.

## Routing

| Step         | Reference                                                                                       | Purpose                                                                                     |
| ------------ | ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Workflow      | [`references/workflow.md`](references/workflow.md)                                             | The seven steps in full: analyze → structure → recommend → confirm → prompt → generate → report. |
| Analysis      | [`references/analysis-framework.md`](references/analysis-framework.md)                         | Instructional-design analysis of the source material.                                        |
| Options       | [`references/options.md`](references/options.md)                                               | Named options, the 21 layout and 21 style galleries, and how to combine them.                |
| Recommendations | [`references/recommendations.md`](references/recommendations.md)                             | Recommended layout×style combinations and keyword shortcuts (auto-select).                    |
| Content       | [`references/structured-content-template.md`](references/structured-content-template.md)      | The `structured-content.md` file format.                                                     |
| Prompt        | [`references/base-prompt.md`](references/base-prompt.md)                                      | The base prompt template all generated prompts are built on.                                 |
| Output        | [`references/output.md`](references/output.md)                                                 | Output directory layout, slug/conflict rules, and the final summary.                          |
| Layouts       | [`templates/layouts/`](templates/layouts/bento-grid.md)                                     | 21 layout definitions (one file per layout).                                                 |
| Styles        | [`templates/styles/`](templates/styles/craft-handmade.md)                                   | 21 style definitions (one file per style).                                                   |
