# PPTX QA Checklist

QA is required for every deck that ships. Your first render is almost never correct — approach QA as a bug hunt, not a confirmation step. If you found zero issues on first inspection, you weren't looking hard enough.

## Overlap Check & Auto-Fix (Before Packing)

Run this on the unpacked XML before packing — it catches overlapping text boxes instantly without needing a render, and `--fix` auto-applies text auto-shrink:

```bash
# Check and auto-fix (enables normAutofit on overlapping text shapes)
python scripts/check_overlaps.py unpacked/ --fix

# Check only (no modifications)
python scripts/check_overlaps.py unpacked/
```

The `--fix` flag adds `<a:normAutofit/>` to every text shape involved in an overlap or off-slide overflow. This makes PowerPoint auto-shrink text to fit the box. If issues remain after `--fix`, shorten text or resize shapes manually.

## Content QA

```bash
python -m markitdown output.pptx
```

Check for missing content, typos, wrong order.

**When using templates, check for leftover placeholder text:**

```bash
python -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|this.*(page|slide).*layout"
```

If grep returns results, fix them before declaring success.

## Automated Checks

Run these before visual inspection to catch common issues automatically:

```bash
python scripts/detect_fonts.py output.pptx
python scripts/office/unpack.py output.pptx unpacked/
python scripts/check_overlaps.py unpacked/ --fix
python scripts/clean.py unpacked/
python scripts/office/pack.py unpacked/ final_output.pptx --original output.pptx
```

Fix any issues these report before proceeding to visual QA.

## Visual QA

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

## Verification Loop

1. Generate slides → Convert to images → Inspect
2. Run `detect_fonts.py` and `check_overlaps.py`
3. **List issues found** (if none found, look again more critically)
4. Fix issues
5. **Re-verify affected slides** — one fix often creates another problem
6. Repeat until a full pass reveals no new issues

**Do not declare success until you've completed at least one fix-and-verify cycle.**
