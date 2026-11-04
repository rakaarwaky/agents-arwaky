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

You pick one of several local CLI tools or free REST APIs for the ASCII-art job at hand — no API keys required. Per-tool setup, flags, and worked examples live in `references/tools.md`.

## Global Rules

- **Default tool per need.** Pick the tool from the decision flow below; use pyfiglet before the asciified API, and install a missing tool before falling back to the next option (Global Rules: defaults, not menus).
- **Terminal-safe output.** Max width 60 chars/line, monospace-only, so output renders in fixed-width contexts.
- **Credit the artist.** When fetching pre-made art from the web, preserve artist signatures/initials.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Decision flow | (below) | One entry per tool need; end state: the tool + command is chosen. |
| Per-tool setup and usage | [`references/tools.md`](references/tools.md) | pyfiglet/asciified, cowsay, boxes, toilet, image-to-ASCII, pre-made art search, QR/weather, LLM-generated fallback palettes. |

## Decision Flow

1. **Text as a banner** → pyfiglet if installed, otherwise asciified API via curl
2. **Wrap a message in fun character art** → cowsay
3. **Add decorative border/frame** → boxes (can combine with pyfiglet/asciified)
4. **Art of a specific thing** (cat, rocket, dragon) → ascii.co.uk via curl + parsing
5. **Convert an image to ASCII** → ascii-image-converter or jp2a
6. **QR code** → qrenco.de via curl
7. **Weather/moon art** → wttr.in via curl
8. **Something custom/creative** → LLM generation with Unicode palette
9. **Any tool not installed** → install it, or fall back to next option

## Completion

- The output renders correctly in a monospace terminal at ≤ 60 chars/line.
