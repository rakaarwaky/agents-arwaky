---
name: pdf
description: "Create, read, merge, fill, and secure PDF files. Use when generating PDFs, extracting text/tables, building or filling AcroForm forms, merging/splitting/watermarking/stamping pages, encrypting or decrypting documents, or preparing official IRS tax forms."
when-to-use: "Use when generating reports/invoices as PDF, building or filling AcroForm forms (with layout linting and visual overlays), extracting text, tables, metadata, or form-field values, merging/splitting/rotating/watermarking/stamping pages, exporting pages as PNGs for visual review or OCR hand-off, managing metadata/attachments, or encrypting/decrypting with passwords. NOT for scanned/image-only PDFs (see references/ocr-extraction.md) and NOT for pixel-perfect HTML-to-PDF rendering (use a headless browser)."
argument-hint: "<create | make-form | lint-form | read | merge | split | fill | secure | watermark | stamp | page-image | meta> <in [out]>"
metadata:
  tags:
    - pdf
    - documents
    - forms
    - reportlab
    - pypdf
    - pdfplumber
    - acroform
    - tax-forms
  related_skills:
    - docx
    - xlsx
    - pptx
  category: office
  backends: [hermes, grok-build]
---

# PDF Skill

Create PDFs from structured specs, build and fill AcroForm forms (with layout linting and visual overlays), extract text/tables/metadata, merge/split/rotate/watermark/stamp pages, export page images, manage metadata and attachments, and encrypt/decrypt — using pypdf, reportlab, and pdfplumber. Scanned (image-only) PDFs contain no text layer: when a page is image-only, stop and follow `references/ocr-extraction.md` instead of pretending to extract text.

## Global rules

- **Scanned / image-only PDFs stop the pipeline** — export the pages with `pdf_page_image.py` at 300 dpi and follow `references/ocr-extraction.md` on the PNGs; do not report empty text as "no content", and do not fabricate text.
- **Inspect before touching** — run `pdf_read.py --meta` first; if `encrypted` is true, decrypt with `pdf_secure.py --decrypt` before any other operation. Rotation must be a multiple of 90.
- **Verify after every operation** — re-read with `pdf_read.py` (`--meta`, `--fields`, or a re-extract) and confirm the result before reporting success; for anything visual (watermarks, flattened forms, stamps), render and inspect with `vision_analyze`.

## Routing

| Step | Reference | Purpose |
| --- | --- | --- |
| Commands, procedure, pitfalls, verification | [`references/usage.md`](references/usage.md) | When to Use, bundled toolchains, prerequisites, quick-reference command table, end-to-end procedure, full pitfall list, and the post-operation verification checklist. |
| Building or filling AcroForms | [`references/forms.md`](references/forms.md) | Field-spec geometry, radio groups, `NeedAppearances` behavior, layout-lint rules, and the visual review loop. |
| A page is image-only | [`references/ocr-extraction.md`](references/ocr-extraction.md) | pymupdf-vs-marker decision table, `scripts/extract_pymupdf.py`, and `scripts/extract_marker.py --check` for disk headroom. |
| Text-in-existing-PDF by description | [`references/nano-pdf-editing.md`](references/nano-pdf-editing.md) | `nano-pdf edit f.pdf 3 "…"` — not for structural work. |
| IRS tax forms (2025) | [`references/tax-forms.md`](references/tax-forms.md), [`references/tax.md`](references/tax.md) | Required reading before filling any form in `forms/`; `tax.md` covers the preparation workflow. |
| Advanced rendering & tooling | [`references/rendering-and-advanced.md`](references/rendering-and-advanced.md) | pypdfium2 rendering, pdf-lib / pdfjs-dist JavaScript, qpdf / poppler flags, performance tuning, and troubleshooting. |

