---
name: pptx
description: Use this skill any time a .pptx file is involved in any way — as input, output, or both. This includes creating slide decks, pitch decks, or presentations; reading, parsing, or extracting text from any .pptx file (even if the extracted content will be used elsewhere, like in an email or summary); editing, modifying, or updating existing presentations; combining or splitting slide files; working with templates, layouts, speaker notes, or comments. Trigger whenever the user mentions 'deck', 'slides', 'presentation', or references a .pptx filename, regardless of what they plan to do with the content afterward. If a .pptx file needs to be opened, created, or touched, use this skill.
when-to-use: "Use whenever any .pptx file is involved — creating, reading, editing, combining, splitting, or working with templates, layouts, speaker notes, or comments — triggered by 'deck', 'slides', 'presentation', or a .pptx filename. Also use for structured programmatic work on .pptx decks via python-pptx (create from JSON spec, structured read-back, targeted text/chart/image edits, template filling, slide PNG rendering) and the legacy binary .ppt — convert it with `soffice --convert-to pptx old.ppt` first."
argument-hint: "thumbnail <file.pptx>|check-overlaps <unpacked_dir> [--fix]|detect-fonts <file.pptx>|render-slides <file.pptx> [--outdir <dir>] [--dpi N] [--cols N]|add-slide <unpacked_dir> <source> [--after <slide>]|delete-slide <unpacked_dir> [<slide>...] [--keep <slide>...]|replace-text <slide.xml> [--ph <type>|--match <text>] --text <new>|replace-nth-text <slide.xml> --find <text> --nth N --text <new>|resize-shape <slide.xml> [--ph <type>] [--width <in>] [--height <in>]|inspect-slide <unpacked_dir> [--theme] [--media]|clean <unpacked_dir>|media-grid <unpacked_dir>|search-templates <query>|create <deck.json> <out.pptx>|read <deck.pptx> [--outline|--notes|--images <dir>]|edit <deck.pptx> --replace-text <old> <new>|--chart-data <spec>|--swap-image <n> <name> <img>|--duplicate-slide <n>|--remove-slide <n>|--move-slide <from> <to>|--set-background <n> <hex>|--set-footer <n> <text>|--set-notes <n> <text>|from-template <tpl.pptx> <out.pptx> --values <vals.json>|render <deck.pptx> --outdir <dir>"
user-invocable: false
---

# PPTX Skill

Three workflows: raw XML unpack/edit/pack for templates, PptxGenJS for de novo
decks, and the python-pptx structured programmatic tooling (the latter merged in
from the former `powerpoint` skill).

## References

- `references/images.md` — image aspect-ratio rule, sources, options, sizing modes, and dimension calculations.
- `references/python-pptx.md` — python-pptx programmatic workflow: create/read/edit/from-template/render, quick reference, and edge-case pitfalls.

## Workflow Selection

| Situation | Action |
|-----------|--------|
| User attaches or references a `.pptx` template to edit | Read [editing.md](editing.md) — edit the template directly |
| No `.pptx` provided — create from scratch | Read [creating.md](creating.md) — use PptxGenJS templates |
| Programmatic create/read/edit via python-pptx (JSON spec, outline read-back, replace-text/chart-data/swap-image/duplicate/remove/move, template fill, slide PNG render) | Read `references/python-pptx.md` |
| Legacy binary `.ppt` file | Convert first: `soffice --convert-to pptx old.ppt`, then use a .pptx workflow |
| Read/analyze an existing presentation | See Reading Content below |

**When in doubt:** If ANY `.pptx` file is attached or mentioned, use the
editing workflow. The creating workflow is ONLY for when no existing
presentation exists at all. The python-pptx workflow is for structured,
script-driven operations on decks (including from-template brand decks)
rather than per-slide XML editing.

---

## Reading Content

```bash
# Text extraction
python -m markitdown presentation.pptx

# Visual overview
python scripts/thumbnail.py presentation.pptx

# Raw XML
python scripts/office/unpack.py presentation.pptx unpacked/

# Structured inspection (placeholders, text, images, media — USE THIS)
python scripts/inspect_slide.py unpacked/ --theme --media
```


---

## QA (Required)

**Assume there are problems. Your job is to find them.**

Your first render is almost never correct. Approach QA as a bug hunt, not a confirmation step. If you found zero issues on first inspection, you weren't looking hard enough.

### Overlap Check & Auto-Fix (Before Packing)

**Run this on the unpacked XML before packing** — it catches overlapping text boxes instantly without needing a render, and `--fix` auto-applies text auto-shrink:

```bash
# Check and auto-fix (enables normAutofit on overlapping text shapes)
python scripts/check_overlaps.py unpacked/ --fix

# Check only (no modifications)
python scripts/check_overlaps.py unpacked/
```

The `--fix` flag adds `<a:normAutofit/>` to every text shape involved in an overlap or off-slide overflow. This makes PowerPoint auto-shrink text to fit the box. If issues remain after `--fix`, shorten text or resize shapes manually.

### Content QA

```bash
python -m markitdown output.pptx
```

Check for missing content, typos, wrong order.

**When using templates, check for leftover placeholder text:**

```bash
python -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|this.*(page|slide).*layout"
```

If grep returns results, fix them before declaring success.

### Automated Checks

Run these before visual inspection to catch common issues automatically:

```bash
python scripts/detect_fonts.py output.pptx
python scripts/office/unpack.py output.pptx unpacked/
python scripts/check_overlaps.py unpacked/ --fix
python scripts/clean.py unpacked/
python scripts/office/pack.py unpacked/ final_output.pptx --original output.pptx
```

Fix any issues these report before proceeding to visual QA.

### Visual QA

You've been staring at the code and will see what you expect, not what's there. 

Convert slides to images, then look for:

- Overlapping elements (text through shapes, lines through words, stacked elements)
- Text overflow or cut off at edges/box boundaries
- Decorative lines positioned for single-line text but title wrapped to two lines
- Source citations or footers colliding with content above
- Elements too close (< 0.3" gaps) or cards/sections nearly touching
- Uneven gaps (large empty area in one place, cramped in another)
- Insufficient margin from slide edges (< 0.5")
- Columns or similar elements not aligned consistently
- Low-contrast text (e.g., light gray text on cream-colored background)
- Low-contrast icons (e.g., dark icons on dark backgrounds without a contrasting circle)
- Text boxes too narrow causing excessive wrapping
- Leftover placeholder content
- **Style consistency** — does every slide feel like it belongs to the same deck?

For each slide, list issues or areas of concern, even if minor.

Read and analyze these images:
1. /path/to/slide-01.jpg (Expected: [brief description])
2. /path/to/slide-02.jpg (Expected: [brief description])

### Verification Loop

1. Generate slides → Convert to images → Inspect
2. Run `detect_fonts.py` and `check_overlaps.py`
3. **List issues found** (if none found, look again more critically)
4. Fix issues
5. **Re-verify affected slides** — one fix often creates another problem
6. Repeat until a full pass reveals no new issues

**Do not declare success until you've completed at least one fix-and-verify cycle.**

---

## Converting to Images

Convert presentations to individual slide images for visual inspection:

```bash
# Preferred — auto-calculates DPI from slide dimensions, with ODP fallback
python scripts/render_slides.py output.pptx

# Or with a custom output directory and DPI
python scripts/render_slides.py output.pptx --outdir slides/ --dpi 200
```

This creates `slide-01.jpg`, `slide-02.jpg`, … plus a combined
`contact-sheet.jpg` in the output directory (default: same folder as the
input).

**Fallback** (if render_slides.py dependencies aren't available):

```bash
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

---

## Images

Image handling rules (aspect ratio, sources, options, sizing modes, dimension calculations) live in `references/images.md`.

---

## Dependencies

**All-in-one install:**

```bash
pip install "markitdown[pptx]" Pillow pdf2image python-pptx numpy defusedxml
npm install -g pptxgenjs
```

**System packages** (pre-installed in the Docker image):
- LibreOffice (`soffice`) — PDF conversion (auto-configured via `scripts/office/soffice.py`)
- Poppler (`pdftoppm`) — PDF to images
- fontconfig (`fc-list`) — font detection
