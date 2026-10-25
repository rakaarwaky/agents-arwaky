# Powerpoint Pitfalls Reference

- **Run splitting**: PowerPoint fragments paragraph text into runs at spell-check and edit boundaries. `--replace-text` first merges adjacent runs whose formatting is identical, so matches split across such runs are replaced with formatting fully preserved. Only when a match spans *genuinely differently-formatted* runs is the paragraph rewritten with the first run's formatting — verify those slides after replacement.

- **Chart slides cannot be duplicated**: each chart relationship embeds a separate XLSX workbook part; cloning that graph reliably is not supported, so `--duplicate-slide` refuses chart slides cleanly instead of corrupting the deck. Rebuild the chart on a new slide instead. External-hyperlink and image/media rels are carried over; layout and notes rels are recreated fresh.

- **Chart ops are a wrapper**: python-pptx replaces the whole dataset; `"ops"` round-trips existing plot data through `replace_data`, and changing chart *type* is not possible.

- **Reordering is XML-level**: python-pptx has no supported reorder API. `--move-slide` manipulates `<p:sldIdLst>` directly; safe for ordinary decks but re-read the deck afterward to confirm.

- **Copying slides between decks is unsupported** — duplication works only within one deck, where layouts and masters are shared.

- Footer/slide-number enablement copies the placeholder from the slide's layout; on layouts without those placeholders, `--set-footer` fails with a clear message (add a textbox instead).

- Hyperlinks apply to whole runs; `--hyperlink` links every run containing the given text on that slide.

- The default python-pptx template is 4:3; the create script sets 16:9 unless the spec says otherwise. Custom templates keep their own size.

- Layout indexes vary by template. For brand templates, list layout names first: `pptx_read.py template.pptx --outline` (`layouts_available`).

- `slide.shapes.title` is None on blank layouts — the create script handles this, but remember it when writing ad-hoc python-pptx code.

- Always pass `encoding="utf-8"` when writing spec files; tokens like `{{city}}` may be filled with non-ASCII values.
