# Docx Pitfalls Reference

- **Tokens split across runs.** Word often fragments text into several runs. The replace helpers collapse matched runs (replacement inherits the first run's formatting); running `docx_edit.py normalize` first reduces fragmentation for all later edits.
- **Revision coverage.** `docx_revisions.py` resolves run-level insertions and deletions (the overwhelming majority). Paragraph-mark and table-row revisions, format-change records, and moves are detected by `--revisions` but not auto-resolved — see `revisions-and-comments.md` and hand those to Word.
- **Comment threading.** Replies and "resolved" status live in `commentsExtended.xml`, which this skill ignores; comments it adds are plain top-level comments.
- **Field results are computed by Word.** `toc`, `page-numbers`, and the `toc`/`footer_page_numbers` spec options write *field codes*. Word/LibreOffice populates the actual entries and numbers when the file is opened (Word may prompt to update fields); python-docx never computes them, so placeholder text shows until then.
- **Validation is a health check, not schema validation.** `docx_validate.py` verifies the zip, required parts, relationship targets, image magic bytes, and referenced styles. It is NOT XSD validation — a file can pass and still contain XML Word dislikes.
- **Style names must exist.** Applying a style that isn't defined in the document raises `KeyError`. Built-ins like `Heading 1`, `List Bullet`, `List Number`, `Table Grid` exist in the default template; custom styles must be declared in the create spec first.
- **Numbered lists restart.** `List Number` relies on Word's default numbering; separate lists in one document may continue numbering instead of restarting. Warn users needing precise multi-list numbering.
- **Cell writes replace formatting.** `set-cell` uses `cell.text = ...`, which resets runs in that cell to plain formatting.
- **Encoding.** All JSON specs/values files are read as UTF-8 explicitly; never rely on locale defaults when writing your own glue code.
- **Don't unzip-and-sed the XML.** Edit through the scripts (or python-docx); raw text substitution in `document.xml` corrupts files easily. Use `patch`/`write_file` only for the JSON inputs, never on the `.docx` itself.
