# LLM Writing — Output Contract

Deliverable shape emitted at the end of every run, in order:

1. **Deliverable** — the written/rewritten/audited text, or the proposed diff for `--dry-run`.
2. **Open items** — every `UNKNOWN` / `UNVERIFIED` / `CONFLICT:` entry found during the run.
3. **Removed** (improve mode only) — facts or sections removed from the existing file, with reason.
4. **Verification** — list of commands run and their exit codes; paths/names/numbers checked against source.

Rules:
- Every unknown value is written `UNKNOWN`; never invented.
- Commands not run are `UNVERIFIED`; `VERIFIED` only after running.
- Disagreements between sources are logged as `CONFLICT:`; never chosen silently.
- No file is modified under `--dry-run`.
