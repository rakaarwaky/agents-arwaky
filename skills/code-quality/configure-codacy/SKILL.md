---
name: configure-codacy
description: Tailors Codacy configuration to a project — discovers its stack, enables the right tools and patterns, runs analysis, and reduces noise by disabling irrelevant patterns, tuning thresholds, and excluding files that should not be analyzed. Also tunes an existing Codacy Cloud repository directly on the cloud, without local analysis, when the repository already has a finished analysis. Produces a machine-readable summary of all changes. Use whenever the user wants to configure Codacy, reduce noise, fix false positives, enable or disable tools or patterns, tune code quality rules, deal with too many warnings, align Codacy with their project conventions, set up Codacy for the first time, or improve the signal of cloud issues.
when-to-use: "Configure Codacy for a project — local-first tuning via codacy-analysis-cli init/discover/analyze, noise reduction, pattern/tool enable/disable, thresholds, file exclusions, and optional Cloud import."
argument-hint: "[import] [force]  (invocation-mode flags parsed from arguments; no positional flags)"
license: MIT
metadata:
  author: Codacy
  version: 4.4.0
---

# Configure Codacy

> **Glossary:** See [glossary.md](references/glossary.md) for shared definitions of Codacy concepts (issues, findings, severity, coverage, tools, patterns, etc.).

## Scenario routing

| Situation | Workflow |
|-----------|----------|
| First-time setup, stack discovery, or local analysis-based tuning | Use the local-first workflow in this SKILL.md body (Steps 0–7 below) |
| Repository already on Codacy with a finished analysis; tune cloud config in place with no local analysis | Read [references/cloud.md](references/cloud.md) |

This skill tailors Codacy configuration to a project's actual stack and coding conventions. It discovers the repository's languages and frameworks, initializes a broad set of tools and patterns, runs analysis, then intelligently cuts noise — producing a clean, high-signal configuration with a full audit trail of what changed and why.

## Prerequisites

- **Codacy Analysis CLI** (`codacy-analysis`) with `discover` and `init --auto` support. If the CLI does not support these commands, update it running: `npm i -g @codacy/analysis-cli`. See `codacy-analysis-cli` for setup.
- **Codacy Cloud CLI** (`codacy`) — needed to know if the repo is on Codacy Cloud and if so, fetch issues from the cloud-only tools. Setup (install, auth, shared session) and the remote command reference live in the **Codacy Cloud CLI** section at the end of the `codacy-code-review` skill.

Both CLIs share credentials at `~/.codacy/credentials`, so a single login covers both.

## How configuration works

All configuration is done locally via `.codacy/codacy.config.json`. Edit the file, run analysis, see results instantly — no push or cloud reanalysis needed. Once tuned, the configuration can be imported to Codacy Cloud in one step.

The key principle: **start broad, then cut noise using data**. Initialize with maximum pattern coverage via `init --auto`, run analysis to see the full issue landscape, then use the severity/category distribution to decide what to disable or tune.


Read [the config format reference](../codacy-analysis-cli/references/config-format.md) for the full schema before editing — field names matter (e.g., the exclusion field is `exclude`, not `excludePaths`). To disable a pattern, remove it from the `patterns` array. To disable a tool, remove the entire tool entry.

**Organization standards take precedence.** If a pattern is enforced by a Coding Standard at the organization level, it cannot be changed at the repository level.

**Local config only.** The `.codacy/codacy.config.json` file is used exclusively for local analysis. Committing or pushing it to the repository has NO effect on Codacy Cloud analysis. To apply the configuration to Codacy Cloud, use the import command (`codacy tools ... --import`).

## Invocation modes

The skill supports three modes that control whether configuration is imported to Codacy Cloud after tuning:

- **Interactive (default):** After tuning and presenting results, prompt the user via `AskUserQuestion` whether to import the configuration to Codacy Cloud. This is the default when no arguments are provided.
- **Auto-import:** If the user's invocation arguments contain the word "import" (e.g., `/configure-codacy import configuration`, `/configure-codacy --import`), skip the import prompt and import automatically after presenting results. Useful for CI runs and automation.
- **Local-only:** If the repo is not on Codacy Cloud (determined in Step 0), never ask about importing. Present results and note that the config is ready for local analysis only.

Additionally, the **force** flag controls Coding Standard handling during import:

- **Force disabled (default):** If the import encounters Coding Standard conflicts (409 errors), **do NOT automatically retry with `--force`**. Instead, present the conflicts to the user via `AskUserQuestion` and let them decide whether to unlink the Coding Standards.
- **Force enabled:** If the user's invocation arguments contain the word "force" (e.g., `/configure-codacy import force`), automatically retry with `--force` when Coding Standard conflicts occur.

Parse the invocation arguments at the very start. Set internal flags that Step 6 will reference:
- If args contain "import" → auto-import mode
- If args contain "force" → force mode (allows automatic Coding Standard unlinking)
- Else → interactive mode (may become local-only if Step 0 finds the repo is not on Cloud)

## Tailored configuration workflow

```
Configuration Progress:
- [ ] Step 0: Check environment and capture baseline
- [ ] Step 1–3: Discover, initialize, and analyze (local) — see references/local-tuning.md
- [ ] Step 4: Smart noise evaluation and tuning
- [ ] Step 5: Show local results
- [ ] Step 6: Cloud import (conditional) — see references/cloud-import.md
- [ ] Step 7: Clean-up — see references/cloud-import.md
```

### Step 0: Check environment and capture baseline

Cloud status check, BEFORE baseline capture (Tracks A/B/C), and the Cloud noise pre-evaluation (0a–0c) live in [references/baseline-capture.md](references/baseline-capture.md), split out to keep this SKILL.md under ~200 lines. Run it before Step 1–3; it sets the invocation mode, the BEFORE metrics, and the `cloudNoiseLocal` / `cloudNoiseCloudOnly` lists that later steps consume.
### Step 1–3: Discover, initialize, and analyze (local)

Stack discovery (`codacy-analysis discover`), auto-tuned initialization with the broad pattern filter plus the Cloud noise pre-filter and preserved-config merge, and the broad-config baseline analysis with issue-distribution parsing live in [references/local-tuning.md](references/local-tuning.md), split out to keep this SKILL.md under ~200 lines. Run them in order before Step 4.

### Step 4: Smart noise evaluation and tuning

The noise-evaluation and tuning decision framework (noise floor, pattern-level priorities, file-level exclusions, tool-level evaluation, lost-pattern recovery, and the validation pass) lives in [references/noise-evaluation.md](references/noise-evaluation.md), split out to keep this SKILL.md under ~200 lines. Apply it against the broad-config baseline results from Step 3 before saving the tuned config.

### Step 5: Show local results

#### 5a. Generate summary JSON

Write `.codacy/configure-codacy-summary.json` with the before/after metrics, a detailed change log, and supporting context. The full schema, field reference, and example document live in [references/summary-json-schema.md](references/summary-json-schema.md), split out to keep this SKILL.md under ~200 lines.

#### 5b. Present local results

Display a clear before/after summary to the user:

1. **Metrics table** — enabled patterns, enabled tools, total issues, and runtime (before vs after, with reduction %). The "before" is the baseline from Step 0. If no prior config existed (Track C), note "No prior configuration" in the before column.
2. **Tool changes** — tools added or removed, with reasons
3. **Top pattern changes by impact** — the `patternChanges` entries with the largest `|delta|`, sorted descending
4. **New security coverage** — new security patterns that were not in the baseline config
5. **Security deduplication** — any security patterns that were deduplicated (which was kept, which was disabled)
6. **Key improvements** — the `keyImprovements` array from the summary JSON, presented as a bulleted list
7. **Warnings** — failed tools, Semgrep parsing errors, tools with 0 files matched, any other issues encountered
8. **Local config file limitations** — for tools with `useLocalConfigurationFile: true`, note that their issues are controlled by the project's own config file (e.g., `.eslintrc`, `.rubocop.yml`), not by Codacy's managed patterns. Noise from these tools can only be reduced by editing the project's own config. List each such tool and the number of issues it produced, so the user knows where to look if they want further noise reduction.

#### 5c. Generate `.codacy.yaml` for Cloud file exclusions

File exclusions in `.codacy/codacy.config.json` only apply to local analysis. Codacy Cloud does not support importing file exclusions via the API or CLI. To apply file exclusions on Codacy Cloud, they must be defined in a `.codacy.yaml` file committed to the repository root (see [Codacy configuration file](https://docs.codacy.com/repositories-configure/codacy-configuration-file/)).

**If any new file exclusions were added during tuning** (global or per-tool), generate a `.codacy.yaml` file:

1. Read the existing `.codacy.yaml` from the repo root (if it exists) to preserve any existing configuration
2. Merge the new exclusions with any existing `exclude_paths` and per-engine `exclude_paths`
3. Write the updated `.codacy.yaml` to the repo root

The `.codacy.yaml` format uses Java glob syntax:
```yaml
---
exclude_paths:
  - "src/routeTree.gen.ts"
  - "vendor/**"
engines:
  markdownlint:
    exclude_paths:
      - "CHANGELOG.md"
  stylelint:
    exclude_paths:
      - "assets/vendor/**"
```

**Engine name mapping:** The engine names in `.codacy.yaml` may differ from the tool IDs in `.codacy/codacy.config.json`. Use the tool ID in lowercase as the engine name (e.g., `ESLint9` → `eslint9`, `Semgrep` → `semgrep`, `markdownlint` → `markdownlint`). If unsure, the tool ID in lowercase is the safe default.

4. Store the full content of the generated `.codacy.yaml` as a string in the `codacyYaml` field of the summary JSON
5. Present to the user:
   - Note that file exclusions cannot be imported to Codacy Cloud via API
   - The `.codacy.yaml` file has been created/updated in the repo root
   - The user should commit and push this file to apply the exclusions on Codacy Cloud
   - Codacy Cloud always reads `.codacy.yaml` from the default branch

If no new file exclusions were added, skip this step and leave `codacyYaml` as `null`.

### Step 6: Cloud import (conditional) — and Step 7: Clean-up

Cloud import (Cloud status check, import behavior per invocation mode, cloud-only tools noise evaluation, `codacy tools --import` with Coding Standard conflict handling, post-import reanalysis verification, and import results) and clean-up of the temporary directory live in [references/cloud-import.md](references/cloud-import.md), split out to keep this SKILL.md under ~200 lines. Apply the Security guardrail below to any Cloud-side pattern changes.

## Per-tool tuning tips

Tool-specific noise-reduction rules live in [references/per-tool-tuning.md](references/per-tool-tuning.md) (Semgrep language filtering, Lizard thresholds, ESLint9 local config, markdownlink/Stylelint handling). That section is intentionally separated out so the SKILL.md body stays under ~200 lines; apply it during Step 4 (noise evaluation and tuning).

## Security guardrail

> **Every security concern must be covered by at least one active pattern.** This is a hard rule with no exceptions.

The guardrail operates at the **concern level**, not the individual pattern level. If two tools both detect "hardcoded secrets," disabling the less precise one is acceptable because the concern remains covered. However, if a security concern (e.g., SQL injection, XSS, path traversal, hardcoded secrets) would lose ALL active pattern coverage, the disable must be reverted.

When a security pattern is noisy and cannot be deduplicated:
- **Exclude specific files** where it triggers false positives (e.g., test fixtures, mock data)
- **Leave the false positives** for the user to triage in Codacy Cloud (they can ignore individual instances with a reason)
- **Never remove the last pattern covering a security concern** — it must stay active to catch real vulnerabilities in future code

For Critical/High severity patterns in non-Security categories, apply the same caution: prefer file exclusion over pattern disabling. Only disable these if they are clearly for the wrong stack (e.g., a Java Critical pattern in a pure Python project).
