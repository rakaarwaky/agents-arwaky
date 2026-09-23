---
name: add-docs
description: Adds docstrings, doc comments, JSDoc, types and PRD/ROADMAP/FRD/README/BACKLOG/AGENTS docs. Use when documenting Python, Rust, TS modules, or splitting spec from status backlog.
metadata:
  tags:
    - python
    - rust
    - typescript
    - docs
    - docstring
    - doc-comments
    - jsdoc
    - type-hints
    - prd
    - roadmap
    - frd
    - readme
    - backlog
    - agents-md
    - pep257
  related_skills:
    - cleanup-consolidate
    - fix-bypass
    - lint-arwaky
  triggers:
    - add docs
    - add doc comments
    - document public api
    - add docstring
    - add jsdoc
    - add type hints
    - add prd
    - add frd
    - add backlog
    - add backlog md
    - add feature backlog
    - add root roadmap
    - add roadmap
    - add readme
    - add package readme
    - add crate readme
    - add agents md
    - agents md template
    - port agents md
    - prd template
    - frd template
    - readme template
    - backlog template
    - roadmap template
    - split spec from status
    - move status out of frd
    - audit document invariants
---
# add-docs

> **Purpose**: Route every claim to the correct document, and ensure every public code item is documented.
> **Audience**: The AI agent executing documentation tasks.
> **Scope**: Python, Rust, and TypeScript modules; PRD, ROADMAP, FRD, README, BACKLOG, and AGENTS files.

The **aggregate** defines which document exists, where it lives, who reads it, and which claim belongs where.
Templates, section contracts, exemplars, and per-document craft rules live in [`references/`](references/).


| Document     | Location                          | Audience                     | Focus                                | Length       | Template                                                               |
| ------------ | --------------------------------- | ---------------------------- | ------------------------------------ | ------------ | ---------------------------------------------------------------------- |
| `PRD.md`     | Root workspace                    | Stakeholder, PM, Design, Eng | *What* &amp; *Why*                   | 50–500 lines | [references/HOW-TO-MAKE-PRD.md](references/HOW-TO-MAKE-PRD.md)         |
| `ROADMAP.md` | Root workspace (exactly one)      | Tech Lead, PM, Engineers     | *Index, policy, workspace condition* | 50–500 lines | [references/HOW-TO-MAKE-ROADMAP.md](references/HOW-TO-MAKE-ROADMAP.md) |
| `FRD.md`     | Each feature module/crate/pkg     | Engineer, QA, Tech Lead      | *How* (functionally)                 | 50–500 lines | [references/HOW-TO-MAKE-FRD.md](references/HOW-TO-MAKE-FRD.md)         |
| `BACKLOG.md` | Each feature dir, beside its spec | Engineer, QA, Tech Lead      | *What is true now*                   | 50–500 lines | [references/HOW-TO-MAKE-BACKLOG.md](references/HOW-TO-MAKE-BACKLOG.md) |
| `README.md`  | Root workspace                    | Developer (new/existing)     | *How to use/run*                     | 50–500 lines | [references/HOW-TO-MAKE-README.md](references/HOW-TO-MAKE-README.md)   |
| `AGENTS.md`  | Root workspace                    | The agent, every session     | *How to work here safely*            | 50–500 lines | [references/HOW-TO-MAKE-AGENTS.md](references/HOW-TO-MAKE-AGENTS.md)   |


**The Document Chain**:  
PRD → ROADMAP  → FRD → BACKLOG → README→ AGENTS

Each file answers exactly one audience's question. A claim in the wrong file is the defect this skill exists to prevent.
Doc comments on every public item are the sixth deliverable, in the language's native form.

---

## Invariants

Every rule is machine-checked by `aa docs check` (capability: `modules/check/src/capabilities_check_docs.py`, shared engine in `modules/shared/src/utility_doc_pack.py`).
A rule cannot drift from the gate. Cite the code, not this file, when pointing at a rule.
Each document's required section set is cross-checked against its reference's contract table, so a
row that stops being enforced is a test failure rather than a silent edit.


| Code                                                                     | Rule                                                                                                                                                                                                           |
| ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `status-in-spec`                                                         | Spec and status never share a file. Specs promise; backlogs report.                                                                                                                                            |
| `spec-without-backlog` / `backlog-without-spec`                          | A spec and its backlog are a pair in the same directory.                                                                                                                                                       |
| `no-master-backlog` / `undefined-state-vocab` / `master-section-missing` | One root master owns the `State`/`Health` vocabulary, the status policy, the roll-up, in-flight branches and risk (`ROADMAP.md`; legacy root `BACKLOG.md` accepted during migration). |
| `state-vocab-restated`                                                   | Definitions live once. Feature files cite them, never repeat them.                                                                                                                                             |
| `done-without-evidence` / `unknown-state`                                | Every backlog claim is re-runnable: command + counts + commit hash, and what it excludes.                                                                                                                      |
| `duplicate-fr-id` / `orphan-fr-ref`                                      | Requirement IDs are unique, stable, and the only thing a backlog row may cite.                                                                                                                                 |
| `scenario-without-evidence` / `scenario-evidence-count`                  | Each test scenario in a spec has one evidence row: Automated / Proxy / Manual / Gap.                                                                                                                           |
| `backlog-columns` / `backlog-row-width`                                  | The Backlog table keeps its nine columns.                                                                                                                                                                      |
| `*-section-missing`                                                      | Each document carries the sections its audience needs. Section contracts are in the refs.                                                                                                                      |
| `dead-link` / `root-relative-link`                                       | Pointers resolve from the file that writes them, not only from the repo or skill root.                                                                                                                         |
| `unreferenced-file`                                                      | Every file under a skill's `references/`, `scripts/`, `assets/` is surfaced by SKILL.md.                                                                                                                       |
| `absolute-path` / `secret-in-docs`                                       | No machine-specific path and no credential literal in any document.                                                                                                                                            |
| `ci-command-drift`                                                       | AGENTS.md commands match CI verbatim or are labelled advisory.                                                                                                                                                 |
| `doc-length` / `doc-thin`                                                | Each document stays inside the size its audience can read.                                                                                                                                                     |


### The Unchecked Invariants (Language Rules)

The checker cannot parse code intent. Enforce these manually:

- **Doc comments explain *what* and *why*, never *how*** (the code shows how).
- **Python**: Public classes and functions need docstrings (PEP 257).
- **Rust**: Public items need `///` (plain `//` is invisible to `cargo doc`). Examples must compile.
- **TypeScript**: Public items need JSDoc.

---

## Diagnostic Tree

Ask these questions in order. The first "No" dictates your next action.

1. **Can a stakeholder understand this project's purpose in 30 seconds?**
   - *No* → Add `PRD.md` (what/why).
2. **Can a tech lead see every feature, shared policy, and workspace truth in one place?**
   - *No* → Add `ROADMAP.md` (index, definitions, status policy, roll-up, risk).
3. **Can an engineer implement this from the spec alone?**
   - *No* → Add `FRD.md` (how).
4. **Can a reader tell what is actually true today for one feature, and re-run the evidence?**
   - *No* → Add `BACKLOG.md` beside that feature's spec.
5. **Can a developer clone, build, and run in under 10 minutes?**
   - *No* → Add `README.md` (how to use).
6. **Can an agent work here safely without being told twice?**
   - *No* → Add `AGENTS.md` (how to work here).

---

## Repository Layout

```text
project-root/
├── PRD.md          # stakeholder alignment (what/why) — 1 per project
├── ROADMAP.md      # feature index, shared policy, workspace condition — 1 per project
├── README.md       # developer onboarding (how to use) — 1 per project
├── AGENTS.md       # operational guide (how the agent works here) — 1 per project
├── crates/
│   ├── feature-a/
│   │   ├── src/
│   │   ├── FRD.md     # engineering specs (how) — per feature crate
│   │   └── BACKLOG.md # feature real condition — beside its spec
│   └── feature-b/
│       ├── src/
│       ├── FRD.md
│       └── BACKLOG.md
```

Same shape for Python `modules/<feature>/` and TypeScript `packages/<feature>/`.
Cross-cutting rows live in the root master `ROADMAP.md` (legacy root `BACKLOG.md` still accepted), not in a feature backlog.

---

## Workflow

1. **Resolve the repo-root anchor first.** `aa docs check` (and every module it loads) resolves the repo root at **import time** by walking up for `config/manifest.json` (`modules/shared/src/utility_paths.py`). If that anchor is missing — a refactored worktree where `config/` was moved, or the audit running out of `modules/shared` — the gate dies with `RuntimeError: agents-arwaky root not found` **before a single finding is produced**. Restore the anchor (`git checkout HEAD -- config/`) or set `AGENTS_ARWAKY_ROOT` to a checkout that has `config/manifest.json` before trusting any audit run. A gate that crashed is not a clean pass.
2. **Analyze**: List feature modules and public items. Run `aa docs check <path>`. The findings are your work list.
3. **Draft PRD**: Write root `PRD.md` per [references/HOW-TO-MAKE-PRD.md](references/HOW-TO-MAKE-PRD.md).
4. **Draft Roadmap**: Write root `ROADMAP.md` per [references/HOW-TO-MAKE-ROADMAP.md](references/HOW-TO-MAKE-ROADMAP.md) (index, definitions, policy, risk).
5. **Draft FRDs**: Write `FRD.md` in each feature dir per [references/HOW-TO-MAKE-FRD.md](references/HOW-TO-MAKE-FRD.md). Move any status found here to step 5.
6. **Draft Feature Backlogs**: Write one `BACKLOG.md` per feature, beside its spec, per [references/HOW-TO-MAKE-BACKLOG.md](references/HOW-TO-MAKE-BACKLOG.md).
7. **Draft README**: Write root `README.md` per [references/HOW-TO-MAKE-README.md](references/HOW-TO-MAKE-README.md).
8. **Draft AGENTS**: Write root `AGENTS.md` per [references/HOW-TO-MAKE-AGENTS.md](references/HOW-TO-MAKE-AGENTS.md).
9. **Document Code**: Add doc comments to all public items, then add type annotations to all signatures.
10. **Verify**: Run `aa docs check <path> --strict`. Then run each touched reference's `Verify` block. Finally, verify the code surface.

---

## Verification

### Machine Checks

```bash
aa docs check .                 # invariant audit of every document
aa docs check . --strict        # warnings become errors — the minimum bar
aa docs check . --include-subtrees   # also audit vendor/ and internal/ submodules
```

A pass means no claim sits in the wrong file, no pointer is broken, and no `Done` row is unevidenced.

### Human Checks

A machine pass does not mean the documents are good. Falsifiable goals, honest exclusions, and a 10-minute Quick Start still need a reader.

### Code Surface Checks

```bash
cargo doc --open                            # Rust public surface
npx tsc --noEmit                            # TypeScript signatures
python -c "import <module>"                 # Python importability + docstrings

# Check for missing doc comments at the file level
for f in crates/*/src/lib.rs packages/*/src/index.ts; do
    head -1 "$f" | grep -qE '^(///|/\*\*)' || echo "NO DOC: $f"
done
```

---

## Doc Comment Conventions

### Python (PEP 257)

**Rules**: One module-level docstring. `Args` and `Returns` on every public function. Never restate the signature in prose.

```python
"""Value objects for import rules."""

class ImportRuleVO:
    """An import rule: a path pattern and the message it reports.

    Attributes:
        pattern: Glob matched against a repo-relative path.
        message: Human-readable violation text.
    """

    def check(self, path: str) -> bool:
        """Return whether *path* violates this rule.

        Args:
            path: Repo-relative file path to test.

        Returns:
            True when the path matches the rule's pattern.
        """
```

### Rust

**Rules**: Convert `//` to `///` (plain comments are invisible to `cargo doc`). Add a summary line. Explain *why* for logic over 10 lines. Add `# Example` for non-obvious usage. Types on every parameter and return.

```rust
/// Orchestrates <name-feature>.
///
/// Execution order:
/// 1. Load rules  2. Scan paths  3. Report violations  4. Apply fixes
pub struct ImportOrchestrator {
    mandatory: Arc<dyn IImportMandatoryProtocol>,
}

/// Check whether *path* violates this rule.
///
/// # Arguments
///
/// * `path` - File path to check
///
/// # Returns
///
/// `true` if the path matches the rule
///
/// # Errors
///
/// Returns `Err` if `path` is empty
///
/// # Example
///
/// ```
/// let rule = ImportRuleVO::new("*.test.ts", "Test file");
/// assert!(rule.check("foo.test.ts"));
/// ```
pub fn check(&self, path: &str) -> Result<bool, Error> {
    // ...
}
```

### TypeScript (JSDoc / TSDoc)

**Rules**: One-liner at the top of every module. `@param` and `@returns` on every public method. Use named `interface` or `type` aliases for complex shapes instead of inline objects.

```ts
/** Value objects for import rules. */

/** An import rule: a path pattern and the message it reports. */
export class ImportRuleVO {
  /**
   * @param pattern - Glob matched against a repo-relative path.
   * @param message - Violation text reported to the user.
   */
  constructor(private readonly pattern: string, private readonly message: string) {}

  /**
   * Report whether a path violates this rule.
   *
   * @param path - Repo-relative file path to test.
   * @returns True when the path matches the pattern.
   */
  check(path: string): boolean {
    return minimatch(path, this.pattern);
  }
}
```

---

## Pre-flight Checklist

- [ ] `aa docs check <path> --strict` exits 0.
- [ ] Every required document exists in the correct directory.
- [ ] Every `Done` backlog row cites a re-run command, a commit hash, and its exclusions.
- [ ] Documents serve their exact audience (no cross-contamination).
- [ ] Public code items carry doc comments, and surface checks (`cargo doc`, `tsc`, `import`) are clean.
- [ ] Every touched reference file had its specific `Verify` block executed.

---

## Common Mistakes (Anti-Patterns)

The invariant codes above cover the machine-checkable ones. These need a reader:

**Structural**

- ❌ **One document for all audiences**: Split by audience. Each file answers one question.
- ❌ **FRD at the project root**: It belongs with the feature code, beside its backlog.
- ❌ **Feature backlog carrying workspace rows or restating root policy**: Cross-cutting rows and State/Health definitions live once in `ROADMAP.md` (root master).
- ❌ **PRD carrying SQL schemas or API detail**: The PRD audience cannot read them. Move to FRD.

**Cadence and code surface**

- ❌ **Documents "write &amp; forget"**: Re-run `aa docs check` each sprint. Drift is silent.
- ❌ **`//` instead of `///` in Rust**: Plain comments are invisible to the doc generator.
- ❌ **Missing module docstrings or undocumented parameters**: The generated API surface stays incomplete.

**Checker false-freights to dodge when authoring specs** (these bite at draft time, before you run the gate):

- ❌ **The word "implemented" in a spec file.** `status-in-spec` matches `\b(impl|un)plemented\b` case-insensitively across the *whole* FRD/PRD — so the reference template's `| As Implemented / As Intended |` column and any `implemented` cell header/cell are auto-flagged. Name the column `impl / intended` and use `impl` for the cell. (Same class: `shipped`/`released in v…`, checkbox items, status markers `✅/❌`, progress `%` all trip it.)
- ❌ **Scenario-evidence rows without a table header.** `check_scenarios` counts evidence via a markdown-table parser that needs a `| Scenario | … |` header + `|---|` separator line; a headerless block of `| … |` rows parses as **0 rows** and reports `0 evidence row(s)` even when the rows are present. Always emit the header row; keep exactly one row per spec scenario, in spec order.
- ❌ **Scenario bullets containing `<`.** The scenario counter skips any spec bullet whose text contains `<` (placeholder convention), so that scenario needs no evidence row — don't write one, or the count is off by one. Rename `<placeholder>` prose to avoid the silent skip.

