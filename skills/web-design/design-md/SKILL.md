---
name: design-md
description: Author/validate/export Google's DESIGN.md design-token spec files.
when-to-use: "Use when the user wants a DESIGN.md design-token spec file — authoring, linting, diffing, or exporting to Tailwind or W3C DTCG JSON; also for WCAG contrast validation on color palettes."
argument-hint: "lint|diff|export|spec [--format <fmt>] DESIGN.md"
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [design, design-system, tokens, ui, accessibility, wcag, tailwind, dtcg, google]
    related_skills: [popular-web-designs, architecture-diagram]
---

# Design-MD

DESIGN.md is Google's open spec (Apache-2.0, `google-labs-code/design.md`) for
describing a visual identity to coding agents. One file combines:

- **YAML front matter** — machine-readable design tokens (normative values)
- **Markdown body** — human-readable rationale, organized into canonical sections

Tokens give exact values. Prose tells agents *why* those values exist and how to
apply them. The CLI (`npx @google/design.md`) lints structure + WCAG contrast,
diffs versions for regressions, and exports to Tailwind or W3C DTCG JSON.

## Global rules

- For purely visual inspiration or layout examples, use `popular-web-designs`
  instead; this skill is for the formal spec file itself.
- File anatomy example (front matter + canonical sections), token types and
  formats, component property whitelist: [`references/anatomy.md`](references/anatomy.md).
- Authoring flow and lint / diff / export CLI commands, exit codes, and the
  Windows `designmd` alias: [`references/workflow.md`](references/workflow.md).
- Full lint rule reference (9 rules as of CLI 0.3.0) and common pitfalls:
  [`references/pitfalls.md`](references/pitfalls.md).
- Spec source of truth: `google-labs-code/design.md` (Apache-2.0); CLI
  `@google/design.md` on npm; generated DESIGN.md files take the user's
  project license.

## Routing

| Step        | Reference                                        | Purpose                                                                                   |
| ----------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------- |
| Understand  | [`references/anatomy.md`](references/anatomy.md) | File structure, token types, canonical section order, canonical example file.             |
| Act         | [`references/workflow.md`](references/workflow.md) | Authoring a new DESIGN.md; lint / diff / export / spec commands with exact CLI syntax.    |
| Troubleshoot| [`references/pitfalls.md`](references/pitfalls.md) | Lint rules in detail, YAML quoting, section order, dotted-path token refs, Windows gotcha. |
