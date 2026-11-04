---
name: xlsx
description: Create, read, edit Excel .xlsx workbooks and CSVs.
when-to-use: "Use when creating, reading, editing, or recalculating Excel .xlsx workbooks and CSVs — styled multi-sheet reports, formulas, tables, charts, data validation, and CSV interop — with openpyxl."
argument-hint: "create <spec.json> <out.xlsx>|read <file.xlsx> [--sheets|--json|--csv|--formulas|--notes|--names] --sheet NAME [--data-only] [--encoding ENC] [--out PATH]|edit <file.xlsx> --set CELL=VALUE|edit --append ROWJSON|edit --add-table NAME:RANGE[:STYLE]|edit --table-append NAME=ROWJSON|edit --list-tables|edit --define-name NAME=REF|edit --delete-name NAME|edit --hyperlink CELL=URL[|TEXT]|edit --note CELL=TEXT[|AUTHOR]|edit --clear-note CELL|edit --protect [PASSWORD]|edit --unlock RANGE|edit --recalc|edit --copy-sheet SRC:NEW|edit --rename-sheet OLD:NEW|restructure <file.xlsx> --sheet NAME --insert-rows IDX[:N]|restructure --sheet NAME --delete-rows IDX[:N]|restructure --sheet NAME --insert-cols COL[:N]|restructure --sheet NAME --delete-cols COL[:N]|recalc <file.xlsx> [--out PATH] [--timeout N]|csv_to_xlsx <in.csv> <out.xlsx> [--sheet-name NAME] [--encoding ENC] [--delimiter DEL]|xlsx_to_csv <file.xlsx> <out.csv> [--sheet NAME] [--encoding ENC] [--delimiter DEL] [--data-only]"
version: 1.1.0
author: Nous Research
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [excel, spreadsheet, xlsx, csv, openpyxl, productivity]
    category: office
    related_skills: [docx, pdf, pptx]
---

# Xlsx Skill

Work with Excel .xlsx workbooks using Python and openpyxl: build
styled multi-sheet workbooks with formulas and charts, inspect or dump
existing files, edit cells and structure, and convert to/from CSV. All
helper scripts are argparse CLIs that print JSON and use explicit
UTF-8 I/O.

## Global rules

- **openpyxl does not calculate formulas.** Formula results appear only via `load_workbook(path, data_only=True)` and only when the file was previously saved by a real spreadsheet app; otherwise cached values are `None`. Add `--recalc` / `"full_calc_on_load": true` so Excel/LibreOffice recompute on open, then run `xlsx_recalc.py` headlessly if `soffice` is available.
- **Use `xlsx_restructure.py` for insert/delete operations on sheets with formulas, merges, tables, or filters** — it rewrites references across all sheets; plain `xlsx_edit.py` insert/delete does not shift references.
- **Sheet protection is not security.** `--protect` sets a standard xlsx sheet-protection hash that well-behaved apps honor; anyone can strip it by editing the zip's XML. Never present it as confidentiality or integrity protection.

## Routing

| Step | Reference | Purpose |
| --- | --- | --- |
| Commands, procedure, pitfalls, verification | [`references/usage.md`](references/usage.md) | When to Use, prerequisites, quick-reference command table, end-to-end procedure, PDF conversion, full pitfall list, and the post-edit verification checklist. |
| Reference-aware row/column insert/delete | [`references/restructuring.md`](references/restructuring.md) | Exact rewrite rules and honest limits for `xlsx_restructure.py` — what it shifts, what it cannot shift (charts, images, conditional-format rule formulas), and the JSON report it prints. |
