---
name: aes
description: "AES docs, layers, rule fixes, and legacy migration."
when-to-use: "Use for any AES task: create or improve project documents (PRD, ROADMAP, FRD, BACKLOG, README, AGENTS, ARCHITECTURE, CONTRIBUTING, DESIGN, DATA), scaffold or audit AES layer files across Python/Rust/TypeScript, fix AES lint violations (AES1xx-AES7xx), or migrate a legacy codebase into the AES 7-layer architecture."
argument-hint: "<docs | layer | fix | migrate> <target> [flags]"
---

# AES Architecture

One umbrella for AES (Arwaky Engineering System) architecture work. Split by job: documents, layer scaffolding, rule fixes, migration. The Global Rules govern every job.

## Global Rules

- **Split spec from status:** PRD/FRD/DESIGN state intent; BACKLOG and ROADMAP state what is true now. Status words never appear in spec documents.
- **One document per reader:** root documents (PRD, ROADMAP, README, AGENTS, ARCHITECTURE, CONTRIBUTING) at workspace root; FRD/BACKLOG per feature folder; DESIGN per surface folder; DATA per shared folder.
- **One fact, one home:** each `references/<doc>/` set owns that document's shape — rules, exemplar, template, workflow. Read it; do not restate here.
- **Verify:** `lint-arwaky-cli docs <workspace>` passes; `lint-arwaky-cli scan <layer-path>` → 0 violations before moving to the next layer.
- **Layer order:** migrate bottom-up (taxonomy → contract → utility → capabilities → agent → surface → root); a layer starts only when the one below scans clean.
- **Shape ownership:** protocol/aggregate shape, structure, DI, wiring owned by the layer skill; migration routes; it does not restate layer shape.
- **Baseline first:** `lint-arwaky-cli scan .` before touching anything; violation count picks strategy (< 10: full, 10–50: phased, > 50: taxonomy-first).

## Jobs (labeled subsections)

### 1. Documents — project documentation
Scaffold and audit the ten AES project documents: PRD, ROADMAP, FRD, BACKLOG, README, AGENTS, ARCHITECTURE, CONTRIBUTING, DESIGN, DATA. Each document type has its own rules, exemplar, template, and workflow.

- **PRD/ROADMAP/FRD/BACKLOG:** what/why vs how/now; spec/status split enforced.
- **README:** how to use/run at workspace root.
- **AGENTS:** how to work here safely at workspace root.
- **ARCHITECTURE:** layer boundaries and allowed dependencies at workspace root.
- **CONTRIBUTING:** how to set up and ship a change at workspace root.
- **DESIGN:** visual & interaction contract per surface folder (six sections: Kind, Entry Points, Request Shape, States, Error States, Invariants, Change Checklist).
- **DATA:** what the shared layer manages per shared folder.
- **Improve vs make:** audit mode checks each document against its rules file and exemplar; make mode scaffolds from the template.

### 2. Layer — AES layer scaffolding
Scaffold AES layer files — agent orchestrators, capabilities, contracts, composition roots, surface commands/UI, taxonomy VOs, stateless utilities — across Python, Rust, TypeScript.

- **Layer chain:** contract → capabilities → agent, consumed by surface/root. One layer file implements one protocol/aggregate pair.
- **Language auto-detection:** resolve path, detect python/rust/typescript from files present; on mixed input, proceed with dominant language and name it in the report.
- **Routing:** dispatch to `reference/<layer>/<language>.md`; that HOW-TO owns workflow steps.
- **Mode create:** scaffold from the language HOW-TO template section.
- **Mode improve:** audit against language HOW-TO rules, list findings, apply fixes.
- **Safety:** default (no `--dry-run`) = autonomous; `--dry-run` = read-only report only.
- **Cross-language H2 order:** Rules → Template → Section Contract → Workflow → Review → Verify (identical across all 3 languages).

### 3. Fix — AES rule fixes
Fix AES lint violations flagged by `lint-arwaky-cli scan` or `lint-arwaky-cli report`.

- **One fact, one home:** each `references/step-N-AESxxx.md` carries the how-to-fix for its rule code; do not restate the same fix in two files.
- **Every reference ends with a Verify step** naming the exact command.
- **Turn progress gates:** run `lint-arwaky-cli report` at start (baseline) and end (delta). Positive delta = run not done.
- **Rule codes:** AES101–AES103 (naming), AES201–AES205 (orphans), AES301–AES305 (roles/layers), AES401–AES406 (imports), AES501–AES506 (quality), AES601–AES610 (structure/documents), AES701–AES706 (project structure).

### 4. Migrate — legacy to AES migration
Migrate a legacy Python/Rust/TypeScript codebase into the AES 7-layer architecture.

- **Phases 0–8:** audit baseline, then build each layer bottom-up, Phase 8 verify to zero.
- **Per-phase gate:** `lint-arwaky-cli scan <layer-dir>` → 0 before next layer; language compile is fallback only.
- **Done:** full scan exits 0, compile clean, tests green.

## References

| Topic | File | Purpose |
|-------|------|---------|
| PRD | `references/prd/rules.md`, `exemplar.md`, `template.md`, `workflow.md` | PRD document shape |
| ROADMAP | `references/roadmap/rules.md`, `exemplar.md`, `template.md`, `workflow.md` | ROADMAP shape |
| FRD | `references/frd/rules.md`, `exemplar.md`, `template.md`, `workflow.md` | FRD shape |
| BACKLOG | `references/backlog/rules.md`, `exemplar.md`, `template.md`, `workflow.md` | BACKLOG shape |
| README | `references/readme/rules.md`, `exemplar.md`, `template.md`, `workflow.md` | README shape |
| AGENTS | `references/agents/rules.md`, `exemplar.md`, `template.md`, `workflow.md` | AGENTS shape |
| ARCHITECTURE | `references/architecture/rules.md`, `exemplar.md`, `template.md`, `workflow.md` | ARCHITECTURE shape |
| CONTRIBUTING | `references/contributing/rules.md`, `exemplar.md`, `template.md`, `workflow.md` | CONTRIBUTING shape |
| DESIGN | `references/design/rules.md`, `exemplar.md`, `template.md`, `workflow.md` | DESIGN shape |
| DATA | `references/data/rules.md`, `exemplar.md`, `template.md`, `workflow.md` | DATA shape |
| Layer HOW-TOs | `reference/<layer>/<language>.md` | 18 layer/language HOW-TOs (agent/capabilities/contract/root/surface/taxonomy/utility × python/rust/typescript) |
| Test HOW-TOs | `reference/test/<language>.md` | Test-suite HOW-TOs for python/rust/typescript |
| AES fix steps | `references/step-0-setup.md` through `step-41-AES706.md` | Fix how-to per AES rule code |
| Python migration | `references/python-migration.md` | Python migration playbook phases 0–8 |
| Rust migration | `references/rust-migration.md` | Rust migration playbook phases 0–8 |
| TypeScript migration | `references/typescript-migration.md` | TypeScript migration playbook phases 0–8 |
| Lint rules | `references/lint-rules.md` | Shared lint rules and triage order |
