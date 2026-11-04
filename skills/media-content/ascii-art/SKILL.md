---
name: ascii-art
description: "ASCII art: text banners (pyfiglet), cowsay, boxes, image-to-ascii, QR codes, weather art."
when-to-use: "Use when the user wants ASCII art — text banners, character speech bubbles (cowsay), decorative borders (boxes), colored text (toilet), image-to-ASCII conversion, QR codes, weather art, or pre-made ASCII art from the web."
argument-hint: "[banner|cowsay|boxes|toilet|image-to-ascii|qr|weather|search] <text|image> [font|--flag]"
metadata:
  related_skills:
    - architecture-diagram
---

# ASCII Art

You pick one of several local CLI tools or free REST APIs for the ASCII-art job at hand — no API keys required. Per-tool setup, flags, and worked examples live in `references/tools.md`; the need-to-tool decision flow lives in `references/decision-flow.md`.

## Global rules

- **Default tool per need.** Pick the tool from the decision flow in `references/decision-flow.md`; use pyfiglet before the asciified API, and install a missing tool before falling back to the next option (defaults, not menus).
- **Terminal-safe output.** Max width 60 chars/line, monospace-only, so output renders in fixed-width contexts.
- **Credit the artist.** When fetching pre-made art from the web, preserve artist signatures/initials.
- **Completion.** The output renders correctly in a monospace terminal at ≤ 60 chars/line.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Need → tool decision | [`references/decision-flow.md`](references/decision-flow.md) | One entry per ASCII-art need; end state: the tool + command is chosen. |
| Per-tool setup and usage | [`references/tools.md`](references/tools.md) | pyfiglet/asciified, cowsay, boxes, toilet, image-to-ASCII, pre-made art search, QR/weather, LLM-generated fallback palettes. |
