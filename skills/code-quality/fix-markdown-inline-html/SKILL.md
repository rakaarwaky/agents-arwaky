---
name: fix-markdown-inline-html
description: Fixes Markdown files rejected as HTML, JSX, or MDX. Use when an editor or edit tool refuses a .md file, or markdownlint reports MD033 inline HTML.
metadata:
  tags:
    - markdown
    - mdx
    - html
    - inline-html
    - generics
    - md033
    - docs
    - rust
    - typescript
    - python
  related_skills:
    - author-skill-md
    - aes-docs
    - aes-lint-arwaky
  triggers:
    - editable only in code mode
    - contains html jsx or mdx
    - md033 inline html
    - markdownlint inline html
    - fix markdown html
    - unescaped angle bracket markdown
    - markdown file not editable
    - angle brackets in markdown
---

# fix-markdown-inline-html

**Rule:** A `.md` file must contain zero angle brackets outside code spans and
fenced blocks. Bare `<...>` is what makes a Markdown file look like HTML, JSX,
or MDX.

## The symptom

An editor or edit tool refuses the file and says something like:

```text
Editable only in code mode because this file contains HTML, JSX, or MDX.
```

The same content trips the linter:

```text
FRD.md:557:74 [markdownlint::MD033] Inline HTML [Element: dyn]
FRD.md:315:36 [markdownlint::MD033] Inline HTML [Element: String]
```

Read this as a content defect in the file, not as a tool limitation. The fix
belongs in the file, and the file then becomes editable normally.

## Why it happens

Three patterns account for nearly every case:

| Pattern | Example | Why it is flagged |
| --- | --- | --- |
| Unquoted generics | `Vec<String>`, `Option<FilePath>`, `Arc<dyn Trait>` | `<String>` parses as a tag |
| Bare comparison | `Completes in < 1s` | `< 1s and a >` looks like a tag |
| Placeholder text | `See <file> for details` | Looks like a tag |

The trap: a file can be 200 lines of correct backticked generics and still have
three bare ones. Backticking is not a stylistic choice here, it is the only
thing separating a valid document from a rejected one.

## The fix, in order of preference

1. **Wrap it in backticks** — `` `Vec<String>` ``, `` `Arc<dyn Trait>` ``.
   Correct for code, and it renders as code.
2. **Rewrite it as prose** — `under 1 s` instead of `< 1s`; `less than` instead
   of `<`. Preferred for a comparison, since a code span reads as code.
3. **Escape the brackets** — `\<String\>`. Last resort: the backslashes are
   visible in raw text and confuse the next reader.

Never "fix" it by converting the file to `.mdx`, and never by stripping the
angle brackets out of a type — that deletes information.

## Find them

```bash
python3 scripts/find_bare_angle_brackets.py <file-or-dir>
```

Exits `1` when it finds any, `0` when clean. It skips fenced blocks, tracks
inline code spans, and reports `line:column` so you can jump straight there.
Use it as a pre-commit gate:

```bash
python3 scripts/find_bare_angle_brackets.py --quiet docs/ || exit 1
```

Independent cross-check, when markdownlint runs in the project:

```bash
lint-arwaky-cli check <path> | grep MD033
```

## Fix loop

- [ ] Run the script over the file; it exits `1` with a `line:column` list.
- [ ] For each hit: backtick it, or rewrite it as prose.
- [ ] Re-run the script; it must now print `clean` and exit `0`.
- [ ] Confirm the edit tool accepts the file with no HTML/JSX/MDX warning.
- [ ] If the project runs markdownlint, confirm `MD033` is gone from its output.

Do not stop at "the tool let me edit it now" — a file can become editable while
still carrying a bare bracket that a later edit reintroduces. The script's exit
status is the criterion, not the tool's tolerance.

## Other Markdown violations in the same file

An `MD033` hit usually arrives alongside other findings. Once the brackets are
fixed, the same `lint-arwaky-cli check` pass will still report:

| Code | Meaning | Fix |
| --- | --- | --- |
| `MD013` | Line longer than 80 chars | Wrap prose; split long table cells |
| `MD060` | Table pipe style inconsistent | Align columns, or use `| --- |` compact style consistently |
| `MD022` | Heading not surrounded by blank lines | Insert a blank line below |
| `MD058` | Table not surrounded by blank lines | Insert blank lines above and below |
| `MD041` | First line is not a top-level heading | Add `# Title` at the top |

Fix all of them in the same pass. Leaving known violations in a file you just
opened for cleanup is how the next session inherits the same defect.
