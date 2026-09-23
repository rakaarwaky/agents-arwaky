# *ACL Paper Styles

This directory contains the latest LaTeX templates for *ACL conferences.

## Instructions for authors

Paper submissions to *ACL conferences must use the official ACL style
templates.

The LaTeX style files are available

- as an [Overleaf template](https://www.overleaf.com/latex/templates/association-for-computational-linguistics-acl-conference/jvxskxpnznfj)
- in this repository
- as a [.zip file](https://github.com/acl-org/acl-style-files/archive/refs/heads/master.zip)

Please see [`acl_latex.tex`](https://github.com/acl-org/acl-style-files/blob/master/acl_latex.tex) for an example.

Please follow the paper formatting guidelines general to *ACL
conferences:

- [Paper formatting guidelines](https://acl-org.github.io/ACLPUB/formatting.html)

Authors may not modify these style files or use templates designed for
other conferences.

## Instructions for publications chairs

To adapt the style files for your conference, please fork this repository and
make necessary changes. Minimally, you'll need to update the name of
the conference and rename the files.

If you make improvements to the templates that should be propagated to
future conferences, please submit a pull request. Thank you in
advance!

In older versions of the templates, authors were asked to fill in the
START submission ID so that it would be stamped at the top of each
page of the anonymized version. This is no longer needed, because it
is now possible to do this stamping automatically within
START. Currently, the way to do this is for the program chair to email
support@softconf.com and request it.

## Instructions for making changes to style files

- merge pull request in github, or push to github
- git pull from github to a local repository
- then, git push from your local repository to overleaf project 
    - Overleaf project is https://www.overleaf.com/project/5f64f1fb97c4c50001b60549
    - Overleaf git url is https://git.overleaf.com/5f64f1fb97c4c50001b60549
- then, click "Submit" and then "Submit as Template" in overleaf in order to ask overleaf to update the overleaf template from the overleaf project 

## Prerequisites

A TeX distribution with `pdflatex` (or `lualatex`) and `bibtex`; alternatively
an Overleaf account using the linked template.

## Quick Start

```bash
pdflatex acl_latex.tex && bibtex acl_latex \
  && pdflatex acl_latex.tex && pdflatex acl_latex.tex
```

Or open `acl_latex.tex` directly in Overleaf (link under Instructions for authors).

## Architecture

`acl.sty` implements the *ACL layout; `acl_latex.tex` and `acl_lualatex.tex` are
complete starter documents for the two engines; `acl_natbib.bst` is the
bibliography style; `custom.bib` and `anthology.bib.txt` are sample references.

## Project Structure

| Path | Role |
|------|------|
| `acl_latex.tex` / `acl_lualatex.tex` | Starter paper (pdfLaTeX / LuaLaTeX) |
| `acl.sty` | The ACL style — authors may not modify it |
| `acl_natbib.bst` | Bibliography style |
| `custom.bib`, `anthology.bib.txt` | Sample bibliography data |
| `formatting.md` | Local copy of the formatting notes |

## Available Scripts

No scripts — compile the starter `.tex` with your TeX engine (see Quick Start).

## Configuration

Preamble options live in `acl_latex.tex` (review mode, anonymity); pick the
engine by choosing `acl_latex.tex` vs `acl_lualatex.tex`. Style files stay
unmodified.

## Testing

A clean compile with zero LaTeX errors, then a pass against the paper
formatting guidelines linked under Instructions for authors (page limits,
anonymity, required fields).

## Contributing

Template improvements go upstream: fork `acl-style-files`, open a pull
request (see Instructions for publications chairs); propagate to Overleaf
per Instructions for making changes to style files.

## License

Official *ACL style-file distribution; terms follow the upstream
`acl-style-files` repository.


## Prerequisites

- See parent skill `SKILL.md` for host prerequisites.
- `python3` ≥ 3.10

## Quick Start

See the skill root `SKILL.md` Quick Start.

## Architecture

Delegates to the parent skill architecture (see `SKILL.md`).

## Project Structure

```
<dir>/
  README.md   # this file
  …           # content owned by this folder
```

## Available Scripts

See commands embedded above and the parent skill `scripts/`.

## Configuration

No environment variables specific to this folder. Parent skill config applies.

## Testing

Parent skill tests cover this area (see skill root).

## Contributing

See the parent skill `SKILL.md` Contributing notes.

## License

Same license as the parent skill / repository.
