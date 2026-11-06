# Eval 3: Dry-Run with No File Change

**Input:**
- Target: `SKILL.md` (any existing file)
- Mode: `audit`
- Flag: `--dry-run`

**Expected:**
- No file written to disk. Target file byte-identical before and after.
- Output is a report: list of findings (anti-patterns present, Rule Checks failed, vague references, plain keywords).
- `Removed` row absent (audit mode does not modify).
- `Size before/after` absent (audit mode does not modify).
- Each finding cites the pattern row in `step-5` or the rule it violates.
- `VERIFIED`/`UNVERIFIED` markers present for every path, number, and command in the target.

**Pass criteria:**
- Target file unchanged: `git diff --stat <file>` empty or `md5sum` identical before/after.
- Report contains no `Removed` or `Size before/after` fields.
- Every finding is checkable: the reader can verify it by re-reading the target file.
