---
name: popular-web-designs
description: 54 real design systems (Stripe, Linear, Vercel) as HTML/CSS.
when-to-use: "Use when the user wants a page styled like a known site — 'build a page that looks like Stripe/Linear/Vercel', a landing page, dashboard, or UI using a real design system's tokens and components."
argument-hint: "<site> [output.html]"
version: 1.1.0
author: Hermes Agent + Teknium (design systems sourced from VoltAgent/awesome-design-md)
license: MIT
platforms: [linux, macos, windows]
tags: [design, css, html, ui, web-development, design-systems, templates]
---

# Popular Web Designs

54 real-world design systems ready for use when generating HTML/CSS. Each
template captures a site's complete visual language: color palette, typography
hierarchy, component styles, spacing system, shadows, responsive behavior, and
practical agent prompts with exact CSS values.

## Global rules

- For the design *process and taste* (scoping a brief, producing variants,
  avoiding AI-design slop) use a dedicated design-process skill; pair it with
  this one when the user wants a thoughtfully-designed page styled after a known
  brand — the process skill drives the workflow, this one supplies the visual
  vocabulary.
- For a formal DESIGN.md token spec file (not a rendered artifact), use the
  `design-md` skill instead.
- **HTML generation.** Apply the chosen template's palette as CSS custom
  properties (`:root { --color-bg; --color-text; --color-accent; … }`), its
  typography stack, component specs, layout, and shadows into a single HTML
  file; the full pattern is in
  [`references/html-pattern.md`](references/html-pattern.md). Write the file
  with `write_file`.
- **Fonts.** Most sites use proprietary fonts unavailable via CDN; each
  template maps to a Google Fonts substitute that preserves the design's
  character (Geist, DM Sans, Source Sans 3, JetBrains Mono, Inter, Rubik, …).
  Follow the template's weight, size, and letter-spacing values closely — they
  carry more visual identity than the specific font face. Full mapping table:
  [`references/font-substitution.md`](references/font-substitution.md).
- Verification of rendered output should confirm visual accuracy against the
  template (colors, spacing, component fidelity).

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| 1. Pick a design | [`references/catalog.md`](references/catalog.md) | Full catalog of 54 templates grouped by category, plus "Choosing a Design" heuristics. |
| 2. Load it | `templates/<site>.md` | Design tokens + component specs + Hermes Implementation Notes (CDN font substitute, Google Fonts `<link>`, font-family stacks). |
| 3. Generate HTML | [`references/html-pattern.md`](references/html-pattern.md) | Skeleton HTML with CSS custom properties wired to the template's sections 2–6. |
| Font mapping | [`references/font-substitution.md`](references/font-substitution.md) | Proprietary → CDN substitute table and which templates have zero substitution loss. |
