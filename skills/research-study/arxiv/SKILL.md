---
name: arxiv
description: Search arXiv papers by keyword, author, category, or ID.
when-to-use: Use when the user asks to search arXiv papers by keyword, author, category, or ID, or to fetch a paper's metadata, abstract, or PDF.
argument-hint: "[\"QUERY\"] [--author NAME | --category CAT | --id ID] [--max N] [--sort relevance|date|updated]"
metadata:
  tags:
    - Research
    - Arxiv
    - Papers
    - Academic
    - Science
    - API
  related_skills:
    - pdf
    - grounded-citations
---

# arXiv Research

Search and retrieve academic papers from arXiv via their free REST API. No
API key, no dependencies — just curl. The API returns Atom XML; the helper
script or a parsing snippet gives clean output.

## Global rules

- **BibTeX generation.** After fetching metadata for a paper, generate a
  BibTeX entry; the full command lives in
  [`references/bibtex.md`](references/bibtex.md).
- **ID versioning.** `arxiv.org/abs/1706.03762` always resolves to the
  **latest** version; `arxiv.org/abs/1706.03762v1` points to a **specific**
  immutable version. When generating citations, preserve the version suffix
  you actually read to prevent citation drift. The API `<id>` field returns
  the versioned URL.
- **Withdrawn papers.** Papers can be withdrawn after submission: the
  `<summary>` field contains a withdrawal notice, metadata fields may be
  incomplete. Always check the summary before treating a result as a valid
  paper.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Search | `scripts/search_arxiv.py` — `python scripts/search_arxiv.py "topic" --max 10 --sort date`, `--author`, `--category cs.AI`, `--id 2402.03300` | Handles XML parsing; no dependencies (stdlib only). |
| Raw API (no script) | [`references/search-arxiv.md`](references/search-arxiv.md) | Full search syntax, boolean operators, sorting/pagination parameters, ready-to-paste parsing snippets. |
| Fetch by ID | `curl -s "https://export.arxiv.org/api/query?id_list=2402.03300"` (comma-separated for multiple) | Direct API access. |
| Read content | `web_extract(urls=["https://arxiv.org/abs/ID"])` for abstract; `web_extract(urls=["https://arxiv.org/pdf/ID"])` for full paper (PDF → markdown) | Use the `pdf` skill for local PDF processing and scanned pages. |
| BibTeX | [`references/bibtex.md`](references/bibtex.md) | Generate a BibTeX entry from fetched metadata. |
| Categories | [`references/common-categories.md`](references/common-categories.md) | Quick-reference table of common arXiv category codes and their fields. |
| Semantic Scholar | [`references/semantic-scholar.md`](references/semantic-scholar.md) | Assess impact / citations / related work via the Semantic Scholar API (JSON; pipe through `python -m json.tool`). |
| OCR / scanned pages | [`references/ocr-extraction.md`](references/ocr-extraction.md) — local mirror of `pdf` skill's procedure; try `web_extract` on a URL first, locally use pymupdf for text PDFs and marker-pdf for bulk OCR | For local PDF processing when the `pdf` skill's reference is not on this machine. |
