# PPTX Workflow Selection

Three workflows: raw XML unpack/edit/pack for templates, PptxGenJS for de novo decks, and the python-pptx structured programmatic tooling.

## When to use which

| Situation | Action |
|-----------|--------|
| User attaches or references a `.pptx` template to edit | Read `references/editing.md` — edit the template directly |
| No `.pptx` provided — create from scratch | Read `references/creating.md` — use PptxGenJS templates |
| Programmatic create/read/edit via python-pptx (JSON spec, outline read-back, replace-text/chart-data/swap-image/duplicate/remove/move, template fill, slide PNG render) | Read `references/python-pptx.md` |
| Legacy binary `.ppt` file | Convert first: `soffice --convert-to pptx old.ppt`, then use a .pptx workflow |
| Read/analyze an existing presentation | See Reading Content below |

**When in doubt:** If ANY `.pptx` file is attached or mentioned, use the editing workflow. The creating workflow is ONLY for when no existing presentation exists at all. The python-pptx workflow is for structured, script-driven operations on decks (including from-template brand decks) rather than per-slide XML editing.

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

## Converting to Images

Convert presentations to individual slide images for visual inspection:

```bash
# Preferred — auto-calculates DPI from slide dimensions, with ODP fallback
python scripts/render_slides.py output.pptx

# Or with custom target resolution
python scripts/render_slides.py output.pptx --output_dir slides/ --width 1920 --height 1080
```

This creates `slide-1.png`, `slide-2.png`, etc. in a folder named after the input file.

**Fallback** (if render_slides.py dependencies aren't available):

```bash
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

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
