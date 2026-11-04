---
name: docx
description: Create, read, edit, template, and review Word .docx files with python-docx CLIs: text, styles, tables, images, {{token}} templates, tracked changes, comments, TOC, and page-number fields.
when-to-use: "Use when generating, reading, editing, or templating Word .docx files — reports, letters, contracts — including tracked changes, comments, TOC, and page-number fields."
argument-hint: "create <spec.json> <out.docx>|read <file.docx> [--text|--structure|--styles|--images <dir>|--revisions]|edit replace <file.docx> --find <old> --replace <new>|edit set-cell <file.docx> --table N --row N --col N --text <text>|edit insert <file.docx> --index N --text <text>|edit delete <file.docx> --index N|edit style <file.docx> --index N --style <name>|edit normalize <file.docx>|edit toc <file.docx> --index N|edit page-numbers <file.docx>|template <tpl.docx> <values.json> <out.docx> [--strict]|revisions list <file.docx>|revisions accept-all <file.docx>|revisions reject-all <file.docx>|revisions accept <file.docx> --id N|revisions reject <file.docx> --id N|comments list <file.docx>|comments add <file.docx> --target <text> --text <comment>|comments delete <file.docx> --id N|validate <file.docx>"
version: 1.1.0
author: Nous Research
license: MIT
platforms: [linux, macos, windows]
metadata:
    tags: [word, docx, documents, office, templates, revisions, comments, redline, xml]
    category: office
    related_skills: [pdf, xlsx, pptx]
    backends: [hermes, grok-build]
---

# Docx Skill

Create, read, edit, and template Microsoft Word `.docx` files with
python-docx via small CLIs. It handles text, styles, lists, tables,
images, headers/footers, `{{token}}` templating, tracked changes
(list/accept/reject), comments (list/add/delete), TOC and page-number
fields, and package health checks. It does not render documents itself
(PDF needs LibreOffice — see Converting to PDF in `references/usage.md`)
or edit legacy `.doc`.

## Global rules

- **Run every helper through `scripts/`; never sed or unzip-edit the XML.** Raw text substitution in `document.xml` corrupts files easily — use the provided scripts (see `references/xml-editing.md` for the toolchain).
- **Verify after every produce-or-edit action.** Re-read the output with `docx_read.py --text`/`--structure`, and run `docx_validate.py` after any revision, comment, or field surgery (checklist in `references/usage.md`).
- **Always `normalize` before find-replace on Word-edited documents.** Word fragments text into runs; `docx_edit.py normalize` merges equal-format adjacent runs so later matches succeed.
- **Template redlining requires reading `references/xml-editing.md` first.** The raw-XML toolchain under `scripts/xml-toolchain/` is for direct OOXML access only; edit the template in place, never recreate it.

## Routing

| Step | Reference | Purpose |
| --- | --- | --- |
| Commands + procedure | [`references/usage.md`](references/usage.md) | Prerequisites, quick-reference command table, end-to-end procedure, Converting to PDF, and the post-edit verification checklist. |
| Raw-XML toolchain | [`references/xml-editing.md`](references/xml-editing.md) | Unpack/repack, redlining, `.dotx` templates, tracked changes via LibreOffice. |
| Tracked changes + comments | [`references/revisions-and-comments.md`](references/revisions-and-comments.md) | Revision types, acceptance flow, comment threading, and which edge cases to hand to Word. |
| Edge-case behaviors | [`references/pitfalls.md`](references/pitfalls.md) | Run fragmentation, revision coverage limits, field results, validation semantics, style numbering, cell formatting, and encoding. |
