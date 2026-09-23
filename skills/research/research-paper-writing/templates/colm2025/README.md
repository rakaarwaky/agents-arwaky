# CoLM 2025 Template

Template and style files for CoLM 2025 (Conference on Language Modelling)
submissions, shipped with the research-paper-writing skill.

## Prerequisites

- A TeX distribution with `pdflatex` and `bibtex` (TeX Live or MiKTeX)
- Optional: a PDF viewer, to compare your build against the reference PDF

## Quick Start

```bash
pdflatex colm2025_conference.tex
bibtex  colm2025_conference
pdflatex colm2025_conference.tex
pdflatex colm2025_conference.tex
```

## Architecture

`colm2025_conference.tex` is the starter manuscript. It loads
`colm2025_conference.sty` for the venue layout, cites through
`colm2025_conference.bst`, and may `\input` `math_commands.tex` for shared math
macros. The bundled package copies keep builds reproducible.

## Project Structure

| Path | Role |
|------|------|
| `colm2025_conference.tex` | Starter paper — replace with your content |
| `colm2025_conference.sty` | Venue style (do not edit) |
| `colm2025_conference.bst` | Bibliography style |
| `colm2025_conference.bib` | Sample bibliography |
| `math_commands.tex` | Optional math macro library |
| `fancyhdr.sty`, `natbib.sty` | Bundled package copies for reproducible builds |
| `colm2025_conference.pdf` | Compiled reference of the template |

## Available Scripts

No scripts ship with this template — compilation is `pdflatex` + `bibtex` as
shown under Quick Start.

## Configuration

Everything is preamble-level: anonymity and review options live in
`colm2025_conference.tex`, packages are pinned by the bundled `.sty`/`.bst`
copies. There is no runtime configuration file.

## Testing

A clean compile with zero LaTeX errors, a resolved bibliography, and a page
count matching the venue limits is the acceptance test; diff your output
against `colm2025_conference.pdf` for layout regressions.

## Contributing

Take venue updates from the official CoLM 2025 distribution, recompile the
starter end-to-end, and keep the file table above in sync with the directory.

## License

Style and bibliography files follow the CoLM 2025 template's original terms;
the starter manuscript text is yours to replace.
