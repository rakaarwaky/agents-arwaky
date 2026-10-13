---
name: lint-arwaky-structure-rule-design
description: "Add lint-arwaky AES7xx structure rules. Self-lint-safe."
version: 1.0.0
author: Hermes
license: MIT
metadata:
  tags: [aes, lint-arwaky, structure-rules, self-lint, design]
  related_skills: [aes-lint-arwaky]
  triggers:
    - add structure rule
    - extend AES701
    - new AES7xx check
    - folder layout rule
    - self-lint rule
---

# Lint-Arwaky Structure-Rule Design

> **Purpose**: Design and ship a new/extended folder-structure rule (AES7xx) in
> `lint-arwaky` without breaking the repo's own self-lint gate.
>
> **Audience**: Agents modifying `crates/structure-rules` + `crates/shared/src/structure_rules/`.
>
> **Scope**: The design-before-code workflow, the self-lint baseline-audit gate, and the
> scoping decisions that keep the rule silent on the repo's own conforming layout.
> Not: writing the rule's actual auditor code (that is `aes-lint-arwaky`'s fix territory).

## When to Use

- You are adding or extending a folder-structure rule (AES7xx) in `lint-arwaky` — e.g.
  a new AES701 sub-check that audits the shared folder's own layout.
- The repo's self-lint gate (`lint-arwaky-cli check .`) runs structure rules on the
  `lint-arwaky` tree itself, so a new structure check must be scoped to stay silent on the
  conforming layout the repo already has.

Do not use for: fixing an existing AES violation in an *external* codebase (that is
`aes-lint-arwaky`), or writing the rule's auditor code without first deciding its scope.

## Core constraint: the linter enforces itself

`lint-arwaky-cli check .` runs structure rules on the **lint-arwaky repo's own folder
layout**. A new AES7xx rule that fires on the repo's current layout breaks the self-lint
the moment it lands. So every new structure rule must be **silent on the conforming
workspace** the repo already has, or you ship a red self-lint in the same PR that adds it.

This is the reason the design step comes before any code. The code is mechanical; the
scoping decision is where the rule gets it wrong.

## Workflow

1. **Read the existing structure machinery first.** The five auditors live in
   `crates/structure-rules/src/capabilities_*_auditor.rs`; shared VOs, constants, and the
   parse helpers live in `crates/shared/src/structure_rules/`. The protocol seam
   (`IStructure…Protocol`) is where the auditor answers the request. Understand which
   seam your new check belongs to before writing — a check about `shared/` belongs to
   `IStructureSharedPurityProtocol` (AES701), a check about feature folders to
   `IStructureFeatureHealthProtocol` (AES702), etc. Usually no new seam is needed; the
   check is a new helper inside an existing auditor. When the decision is ambiguous,
   follow the user's direction: the AES7xx family is layered feature-first — a check that
   keys on whether a *feature* folder owns a `shared/src/<feature>/` mirror belongs to
   AES702 (feature-health), NOT AES701 (shared-purity) even though it touches the shared
   tree. AES701 audits the shared folder's own purity; AES702 audits feature-folder health.
   Raka placed the shared-mirroring check under AES702 on exactly this reasoning: the
   feature folder is checked first, then parity on the shared folder.

2. **Define the violation types as constants** in
   `crates/shared/src/structure_rules/taxonomy_structure_rules_constant.rs` under the
   owning rule's section (e.g. `SHARED_PURITY_VIOLATION_…` for AES701). One constant per
   violation type string; the string is stable and machine-readable, the message is prose.

3. **Add any new parse helpers** to
   `crates/shared/src/structure_rules/utility_structure_parsers.rs`. These perform **no
   rule decisions** — they walk, label, and return data (`Vec<String>`, sets, counts).
   Reuse the existing folder-inventory helpers (`inventory`, `feature_dirs`, `member_dirs`)
   rather than re-walking; the AES702 feature-folder gate
   (`has_capabilities || has_orchestrator`) is the one you will usually want to share.

4. **Wire the check into the owning auditor** (`capabilities_*_auditor.rs`) by calling
   your new private helper from the auditor's `audit_*` method, after the existing
   sub-checks. Push `StructureFinding::new(code, violation_type, file, message)` rows
   and attach `with_reason(why, fix)` so the report names both the cause and the remedy.

5. **Baseline-audit the repo against the proposed rule semantics BEFORE writing the
   auditor code.** This is the step that catches a mis-scoped rule. Run a manual
   equivalent of the new check over the repo's own tree and enumerate exactly which
   folders/files would fire. See the decision table below.

6. **Resolve every firing in the same PR or defer it deliberately.** If the repo's own
   layout would fire the new rule, either (a) restructure the repo to conform in the same
   PR, or (b) narrow the rule's scope so the conforming layout is legal, or (c) add an
   explicit exemption constant with a documented reason. Shipping the rule while leaving
   the self-lint red is a merge blocker.

7. **Add contract tests** in `crates/structure-rules/tests/contract_structure_rules.rs`.
   Each new violation type gets a *fires* case and a *stays-silent* case, using the
   tempfile + `has(&findings, code, violation_type)` pattern already in that file. Update
   the `conforming_workspace_reports_no_findings` test: it must still be empty under the
   new rule, which is the proof the rule is silent on a conforming layout.

8. **Update the doc chain in the same PR**: `RULES_AES.md` (add the violation-type rows
   to the owning rule's table), the owning crate's `FRD.md` (one new requirement, six
   fields per AES601), and its `BACKLOG.md` (new row, In Progress → Done). A structure
   rule with no doc-pair update fires AES702/AES703 on the repo itself.

9. **Run the self-lint gate** (`lint-arwaky-cli check .` + `docs .` + `scripts/gates.sh`)
   on the PR head. It must report 0 before merge.

## Decision table — resolving the baseline firings

When the baseline audit (step 5) shows the repo's own layout firing the new rule:

| Firing shape | What it usually means | Resolution |
| ------------ | --------------------- | ---------- |
| A member folder that is **surface-dominated** (all `surface_*`/`root_*`, no `capabilities_*`/`agent_*`) has a `shared/` counterpart that a feature-only mirroring rule would call an orphan | The folder is a utility-surface layer, not a feature — its shared module holds root wiring, not a contract module | Widen the orphan check to accept both feature **and** utility-surface folders, or exempt utility-surface shared modules by name |
| A member folder with **no** AES-named files at all (pure TS package, CLI surface) appears in the feature-folder walk | It is not a feature by the AES702 gate, so it owes nothing | Exclude it — the gate already does this; confirm the helper uses `has_capabilities \|\| has_orchestrator` |
| A `shared/<x>/` subfolder matches no member folder | Genuine orphan (a shared module whose feature was deleted, or a naming slip) | Fire the orphan finding; this is the rule's purpose |
| Loose `taxonomy_*`/`utility_*` kernel files sit directly in `shared/src/` with no `common/` subfolder | The kernel files are not grouped | Fire a missing-common finding **only when** such loose files exist; an empty shared module is not a defect |

## Pitfalls

- **Skipping the baseline audit is the #1 way a structure rule ships red.** The auditor
  code is trivial to write; the scoping decision is what breaks self-lint. Always run the
  manual equivalent over the repo's own tree and enumerate firings before committing to a
  scope. (The linter audits itself — `check .` includes structure rules — so an
  unscoped rule fires on the repo the rule was written into.)
- **A feature-folder-only orphan check mis-fires on utility-surface shared modules.**
  In `ARCHITECTURE.md` the `dispatcher` and `mcp-server` layers are utility surfaces: their
  `shared/<name>/` folders hold root composition wiring, not a feature contract module.
  A mirroring rule that only knows feature folders would call those shared subfolders
  orphans. Widen the legal-set to feature + utility-surface folders (a member folder whose
  files are all `surface_*`/`root_*`) before shipping.
- **An empty `shared/<x>/` subfolder is a defect, not a clean case — for *new* rules you
  write.** Do not let the mirroring check read "folder exists" as satisfied; require the
  subfolder to actually carry at least one source file, or an empty mirror passes the
  rule vacuously. (Counter-case that cost time this session: the AES702
  `feature_missing_shared_subfolder` check that Raka scoped as ONE violation type
  deliberately reads "immediate subdirectory named after the feature exists" and accepts
  an empty subfolder as satisfied. That is the user's explicit scope — do not "improve" it
  into a non-empty requirement; the rule here is the absence of the subfolder, not what's
  inside it.)
- **Do not create a new protocol seam for a sub-check.** A new check on an existing
  folder kind (e.g. subfolder presence inside `shared/`) is a new helper inside the
  owning auditor; the seam is per rule group, not per sub-check. A new seam is only
  justified when the check reads a different input shape than the group's request.
- **The doc chain is part of the rule.** A structure rule that adds a violation type but
  not the `RULES_AES.md` row + FRD requirement + BACKLOG row will fire AES601/AES702
  against the repo in the same run. Update docs in the same PR as the code.
- **Naming: member folders use `-`, shared subfolders use `_`.** `cli-commands` maps to
  `cli_commands`. Any mirroring check must translate the member-folder name to the module
  name (`replace('-', "_")`) before comparing, or every dashed feature folder reads as a
  missing subfolder.

- **The FP gate (`workspaces-good == 0`) is the real tripwire for new rules, not the
  self-lint.** `check .` (self-lint) tells you the repo is clean, but it says nothing
  about the `workspaces-good` fixture the FP gate asserts is violation-free. Before
  committing, run `lint-arwaky-cli scan workspaces-good` and confirm the new rule
  contributes **0** findings there; `workspaces-good` is a flat-kernel fixture that can
  newly fire a mirroring rule, and it carries latent AES601 doc-parity defects that a
  freshly built binary surfaces. If the gate goes red, the fix is either migrating the
  fixture to a mirroring layout (scope it; it is not the structure-rules PR's job) or
  confirming the findings are pre-existing doc defects unrelated to the new rule. Never
  let a fixture-migration change ship inside a rule-addition PR unless Raka asks for it.

- **Freshly build the CLI before trusting any scan count — cached binaries lie.** The
  main clone's `target/release/lint-arwaky-cli` predates recently-added doc-rules (AES601
  method-existence), so an old binary reports 0 where a current build reports dozens.
  Run `CARGO_INCREMENTAL=0 cargo build --release --bin lint-arwaky-cli` in the worktree
  before scanning, and re-scan at both the main path and the worktree path (the doc-linter
  caches by absolute path, so the same binary can give different counts on the same
  fixture content depending on where it lives).

## Verify

```bash
# Self-lint gate on the PR head — must be 0
lint-arwaky-cli check .
lint-arwaky-cli docs .

# FP gate on the workspaces-good fixture — must be 0 AND the new rule must contribute 0
# (confirm pre-existing AES601/quality fixture defects are not attributed to your rule)
lint-arwaky-cli scan workspaces-good --format json

bash scripts/gates.sh

# The owning crate's structure tests, including the conforming-workspace case
CARGO_INCREMENTAL=0 cargo nextest run -p structure-rules-lint-arwaky
```

Manual:

- [ ] Baseline audit over the repo's own tree ran **before** the auditor code was written.
- [ ] Every firing the baseline audit produced is resolved (restructured, scoped out, or
      explicitly exempted) in the same PR.
- [ ] `conforming_workspace_reports_no_findings` still passes — the rule is silent on a
      legal layout.
- [ ] Each new violation type has a fires + stays-silent contract test pair.
- [ ] `RULES_AES.md` + the owning crate's FRD + BACKLOG updated in the same PR.
- [ ] `lint-arwaky-cli check .` and `docs .` report 0 on the PR head.
- [ ] `lint-arwaky-cli scan workspaces-good` shows the new violation type at 0; any other
      findings are confirmed pre-existing (doc-parity / quality), not the new rule's.
- [ ] No fixture-migration files (shared subfolders under `workspaces-good/*/shared/src/`)
      are part of the rule-addition commit.
