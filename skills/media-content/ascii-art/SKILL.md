---
name: ascii-art
description: "ASCII art: pyfiglet, cowsay, boxes, image-to-ascii."
when-to-use: "Use when the user wants ASCII art — text banners (pyfiglet), character speech bubbles (cowsay), decorative borders (boxes), colored text (toilet), image-to-ASCII conversion, QR codes, weather art, or pre-made ASCII art from the web."
argument-hint: "[banner|cowsay|boxes|toilet|image-to-ascii|qr|weather|search] <text|image> [font|--flag]"
metadata:
  tags:
    - ASCII
    - Art
    - Banners
    - Creative
    - Unicode
    - Text-Art
    - pyfiglet
    - figlet
    - cowsay
    - boxes
  related_skills:
    - excalidraw
---

# ASCII Art Skill

Multiple tools for different ASCII art needs. All tools are local CLI programs or free REST APIs — no API keys required.

Full per-tool instructions: `skill_view(name="ascii-art", file_path="references/tools.md")` covers pyfiglet, asciified API, cowsay, boxes, toilet, image-to-ASCII, pre-made art search, QR/weather utilities, and LLM-generated fallback art.

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
