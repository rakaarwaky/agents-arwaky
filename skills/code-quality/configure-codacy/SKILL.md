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
- **Codacy Cloud CLI** (`codacy`) — needed to know if the repo is on Codacy Cloud and if so, fetch issues from the cloud-only tools. See `codacy-cloud-cli` for setup.

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
- [ ] Step 1: Discover repository stack
- [ ] Step 2: Initialize auto-tuned configuration
- [ ] Step 3: Run broad-config baseline analysis
- [ ] Step 4: Smart noise evaluation and tuning
- [ ] Step 5: Show local results
- [ ] Step 6: Cloud import (conditional)
- [ ] Step 7: Clean-up
```

### Step 0: Check environment and capture baseline

This step determines the starting point and captures the BEFORE metrics for the final summary. The flow depends on two conditions: whether the repo is on Codacy Cloud, and whether a local config already exists.

#### 0a. Create temp directory and check Codacy Cloud status

Create the temporary directory for intermediate analysis files:
```bash
mkdir -p .codacy/tmp
```

The Cloud CLI auto-detects provider, organization, and repository from the git remote origin URL — no need to derive these manually. All `codacy` commands below can be run without explicit `<provider> <org> <repo>` when inside the repo. For clarity, the examples use the explicit form; replace with auto-detected short form in practice.

**CLI output caveat:** Both `codacy` and `codacy-analysis` CLIs write progress lines (e.g., `- Fetching tools...`, `- Fetching issues...`) to stderr before the actual JSON output. When piping CLI output directly to `jq`, redirect stderr to avoid parse errors:

```bash
codacy repository --output json 2>/dev/null | jq '...'
```

Check Cloud status:
```bash
codacy repository --output json
```

If this succeeds, the repo is on Codacy Cloud. Also list enabled tools to identify cloud-only tools later:
```bash
codacy tools --output json 2>/dev/null | jq '[.[] | select(.settings.isEnabled == true) | {name, isClientSide}]'
```

If it fails (repo not on Codacy, no auth, or no Cloud CLI), note that cloud features will be skipped — the local workflow is fully self-contained. Set the invocation mode to local-only (see "Invocation modes" section).

#### 0b. Capture baseline (BEFORE reference)

Branch based on Cloud status and local config existence. The baseline captured here is the true BEFORE reference for the summary in Step 5.

**Track A — Repo is on Codacy Cloud (authoritative baseline):**

The Cloud configuration is the authoritative source. Use `init --remote` to fetch it.

**Important:** `init --remote` will fail if `.codacy/codacy.config.json` already exists. Always delete it first (the backup copy step happens before the delete):

```bash
# Delete any existing config first — init --remote refuses to overwrite
rm -f .codacy/codacy.config.json

# Fetch the current Cloud configuration
codacy-analysis init --remote <provider> <org> <repo>

# Store a copy for later merging and comparison
cp .codacy/codacy.config.json .codacy/tmp/codacy-remote-config.json

# Record BEFORE metrics
jq '[.tools[].patterns | length] | add' .codacy/codacy.config.json
jq '.tools | length' .codacy/codacy.config.json

# Run analysis with the Cloud config to capture the BEFORE issue landscape
codacy-analysis analyze --install-dependencies --output-format json --output .codacy/tmp/codacy-remote-results.json

# Record BEFORE issue count and runtime
jq '.issues | length' .codacy/tmp/codacy-remote-results.json
jq '.metadata.durationMs' .codacy/tmp/codacy-remote-results.json
```

Fetch the Cloud issue overview — this gives per-pattern issue counts, false positive counts, and suggested actions across the entire repository without downloading every individual issue:
```bash
codacy issues -O -o json > .codacy/tmp/codacy-cloud-overview.json
```
This overview data is valuable for tuning decisions in Step 4: it shows which patterns produce the most issues on Cloud (the production truth), includes false positive rates per pattern, and generates suggested actions to reduce noise (identifying patterns accounting for 10%+ of all issues or 3x the average). The suggested actions include ready-to-run disable commands, adapted for coding standard or config-file constraints. Save it for later comparison.

Also check for cloud-only tools — tools enabled in Cloud but not available in the local Analysis CLI. Get the local CLI's supported tools via `codacy-analysis info`, then compare against the Cloud-enabled tools list above. Any Cloud-enabled tool not in the `info` output is cloud-only (e.g., SonarSharp, Codacy ScalaMeta Pro). If cloud-only tools exist and have issues, fetch them:
```bash
codacy issues --output json > .codacy/tmp/codacy-remote-cloud-results.json
```

**Track B — NOT on Cloud, but local `.codacy/codacy.config.json` exists:**

```bash
# Store a copy for later merging and comparison
cp .codacy/codacy.config.json .codacy/tmp/codacy-previous-config.json

# Record BEFORE metrics
jq '[.tools[].patterns | length] | add' .codacy/codacy.config.json
jq '.tools | length' .codacy/codacy.config.json

# Run analysis with the existing local config
codacy-analysis analyze --install-dependencies --output-format json --output .codacy/tmp/codacy-previous-results.json

# Record BEFORE issue count and runtime
jq '.issues | length' .codacy/tmp/codacy-previous-results.json
jq '.metadata.durationMs' .codacy/tmp/codacy-previous-results.json
```

**Track C — No Cloud, no local config:**

Record BEFORE as unconfigured: 0 patterns, 0 tools, 0 issues, `null` runtime. No analysis to run.

Save the BEFORE metrics from whichever track ran. The broad config metrics from Steps 2-3 are internal only — they are NOT reported to the user.

#### 0c. Cloud noise pre-evaluation (Track A only)

If the Cloud overview was fetched (`.codacy/tmp/codacy-cloud-overview.json` exists), analyze it now to identify patterns that are already known to be noisy based on Cloud production data. This saves time by pre-disabling known noise before running local analysis.

Start by checking the overview's **suggested actions** — the CLI already identifies patterns accounting for 10%+ of all issues or 3x the average per-pattern count and provides ready-to-run disable commands. Use these suggestions as the primary signal, then supplement with the criteria below.

Parse the overview's `patterns` array (each entry has `{id, title, total}`) and false positive counts:

```bash
# Issue counts per pattern
jq '[.overview.patterns[] | {id, title, total}] | sort_by(-.total)' .codacy/tmp/codacy-cloud-overview.json

# Patterns with potential false positives (count > 0)
jq '[.overview.patterns[] | select(.potentialFalsePositives > 0) | {id, title, total, potentialFalsePositives, falsePositiveRatio: ((.potentialFalsePositives / .total) * 100 | round)}] | sort_by(-.falsePositiveRatio)' .codacy/tmp/codacy-cloud-overview.json
```

**Identify noisy patterns using these criteria:**

1. **Wrong-language patterns** — cross-reference pattern IDs against the discovered stack (Step 1 runs next, but the Cloud tools list from Step 0a gives a rough language picture). Pattern IDs often contain the target language (e.g., `python.`, `java.`, `ruby.`). Mark patterns for languages clearly not in the project.

2. **Convention/style noise** — patterns with very high issue counts (top 5% by count) in categories like CodeStyle, Documentation, or Comprehensibility are likely convention mismatches. Mark these as candidates.

3. **High false-positive ratio patterns** — patterns where a significant proportion of issues are flagged as potential false positives (e.g., `potentialFalsePositives / total > 30%`) are strong candidates for pre-disabling. These patterns are producing results that Codacy's own heuristics consider unreliable. Store the false positive data for use in Step 4b rule 7, where patterns with high false-positive ratios get additional scrutiny during local verification.

4. **Never pre-disable Security patterns** — security patterns are never marked for pre-disabling regardless of count or false-positive ratio. They are handled in Step 4 with full context.

5. **Never pre-disable Critical/High severity patterns** — these require local verification before any action.

**Classify each noisy pattern into two lists:**

- **`cloudNoiseLocal`** — noisy patterns from tools supported by the local Analysis CLI. These will be removed from `.codacy/codacy.config.json` immediately after `init --auto` in Step 2.
- **`cloudNoiseCloudOnly`** — noisy patterns from cloud-only tools (identified in Step 0b). These will be disabled via Cloud CLI during Step 6 (import), only if the import is performed.

Store both lists for use in Steps 2 and 6. This is a pre-filter — Step 4 will perform deeper noise evaluation on the local analysis results.

### Step 1: Discover repository stack

Run discovery to understand the repository's languages, frameworks, and libraries:

```bash
codacy-analysis discover --output-format json --output .codacy/tmp/codacy-discover.json
```

Parse the output to understand:
- Languages present in the project
- Frameworks and libraries in use (e.g., React, Django, Spring Boot)
- This informs noise evaluation in Step 4 (e.g., knowing a project uses React means JSX-related patterns are relevant)

Note: The Codacy Cloud check already happened in Step 0.

### Step 2: Initialize auto-tuned configuration

First, remove the existing `.codacy/codacy.config.json` if any (the backup copy was already stored in Step 0):

```bash
rm -f .codacy/codacy.config.json
```

Initialize with the broadest useful pattern set, filtered by the discovered stack:

```bash
codacy-analysis init --auto "Critical,High,Warning,Minor,AllSecurity,ErrorProne,Performance,BestPractice,UnusedCode,Compatibility,Complexity,Comprehensibility,CodeStyle,Documentation"
```

This filter means:
- `Critical` — Codacy-recommended (default) Critical-severity patterns
- `AllSecurity` — ALL Security-category patterns (including non-defaults)
- Everything else — Codacy-recommended (default) patterns at High, Warning, and Minor severity across all categories

The intent is to start broad and cut in Step 4 based on actual analysis data.

**Apply Cloud noise pre-filter (Track A only):** If `cloudNoiseLocal` patterns were identified in Step 0c, remove them from the newly created config now. For each pattern in `cloudNoiseLocal`, find it in `.codacy/codacy.config.json` under its tool's `patterns` array and remove it. This avoids wasting local analysis time on patterns already known to be noisy from Cloud production data. Track these removals for the summary (they are pre-filter changes, reported in `patternChanges` with reason referencing Cloud data).

**Merge preserved configuration** from the baseline stored in Step 0:
- **Track A** (Cloud): Merge from `.codacy/tmp/codacy-remote-config.json`
- **Track B** (local config): Merge from `.codacy/tmp/codacy-previous-config.json`
- **Track C** (no prior config): No merge needed

For the applicable track:
1. Read the newly created `.codacy/codacy.config.json`
2. Merge the global `exclude` array from the stored config (merge, don't replace — the new config may have its own excludes)
3. For each tool that exists in both stored and new config, merge its per-tool `exclude` array
4. For tools where `useLocalConfigurationFile` was `true` in the stored config and the tool still exists, restore that setting along with the `localConfigurationFile` path

**Record broad-config metrics** (internal — not the BEFORE reference for the summary):
```bash
# Count enabled patterns across all tools in the broad config
jq '[.tools[].patterns | length] | add' .codacy/codacy.config.json

# Count enabled tools in the broad config
jq '.tools | length' .codacy/codacy.config.json
```

### Step 3: Run broad-config baseline analysis

Run analysis with the broad config to see the full issue landscape. This is an internal step for tuning decisions — the BEFORE reference for the user-facing summary comes from Step 0.

```bash
codacy-analysis analyze --install-dependencies --output-format json --output .codacy/tmp/codacy-baseline.json
```

Always use `--output <file>` to avoid broken JSON from stdout buffering.

**Record broad-config metrics** (used for tuning decisions in Step 4, not for the summary):
```bash
# Total issues in broad config
jq '.issues | length' .codacy/tmp/codacy-baseline.json

# Total runtime in milliseconds
jq '.metadata.durationMs' .codacy/tmp/codacy-baseline.json
```

**Parse the issue distribution** — this is the basis for all tuning decisions:

```bash
# Issues grouped by pattern (noise detection)
jq '[.issues | group_by(.patternId) | .[] | {patternId: .[0].patternId, toolId: .[0].toolId, severity: .[0].severity, category: .[0].category, count: length}] | sort_by(-.count)' .codacy/tmp/codacy-baseline.json

# Issues by severity
jq '.issues | group_by(.severity) | map({severity: .[0].severity, count: length})' .codacy/tmp/codacy-baseline.json

# Issues by category
jq '.issues | group_by(.category) | map({category: .[0].category, count: length})' .codacy/tmp/codacy-baseline.json

# Top 20 files by issue count
jq '[.issues | group_by(.filePath) | .[] | {filePath: .[0].filePath, count: length}] | sort_by(-.count) | .[0:20]' .codacy/tmp/codacy-baseline.json

# Per-tool results
jq '.toolResults | map({toolId, status, issueCount, durationMs, filesAnalyzed})' .codacy/tmp/codacy-baseline.json
```

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

### Step 6: Cloud import (conditional)

#### 6a. Check Cloud status

If the repo is NOT on Codacy Cloud (from Step 0): skip this step entirely. Note in the results: "The configuration is ready for local analysis. To use it on Codacy Cloud, first add the repository to Codacy."

#### 6b. Determine import behavior

Based on invocation mode (see "Invocation modes" section):

1. **Auto-import mode** (user invoked with "import" argument): Proceed directly to 6c.
2. **Interactive mode** (default): Use `AskUserQuestion` to ask the user: "Want to update these configurations in Codacy Cloud?" If the user declines, skip to Step 7.
3. **Local-only mode**: Already handled in 6a (skipped).

#### 6c. Cloud-only tools noise evaluation

Only if cloud-only tools had issues fetched in Step 0 (`.codacy/tmp/codacy-remote-cloud-results.json` exists):

Apply the same noise evaluation framework from Step 4 to the cloud-fetched issues. For each noisy pattern from a cloud-only tool:
- Check if its parameters can be tweaked to return fewer results → `codacy pattern <toolName> <patternId> --parameter key=value`
- If not tweakable → try to disable it: `codacy pattern <toolName> <patternId> --disable`
- If disable fails (Coding Standard enforcement) → note it for the results

#### 6d. Import local config

```bash
codacy tools --import .codacy/codacy.config.json -y
```

If the import encounters Coding Standard conflicts (409 errors — patterns/tools enforced at org level cannot be overridden):

1. **If force mode is enabled** (user invoked with "force" argument): Automatically retry with `--force`:
   ```bash
   codacy tools --import .codacy/codacy.config.json --force -y
   ```
   Note in the results that `--force` was used and which Coding Standards were unlinked.

2. **If force mode is NOT enabled** (default): Do **NOT** automatically retry with `--force`. Instead:
   - Report which tools/patterns could not be changed due to Coding Standard enforcement
   - List the specific Coding Standards that are blocking the changes
   - Use `AskUserQuestion` to ask the user: "The import was partially blocked by Coding Standards [list names]. Would you like to unlink these Coding Standards and retry with --force? This will sever the link between this repository and the organization-level standards."
   - If the user accepts → retry with `--force`
   - If the user declines → keep the partial import as-is and note the blocked changes in the results

**NEVER unlink Coding Standards without explicit user consent or the "force" invocation flag.**

**Important:** The `.codacy/codacy.config.json` file is for local use only. Committing or pushing it to the repository has NO effect on Codacy Cloud. The import command is the only way to sync local config to Cloud.

#### 6e. Post-import Cloud verification

After a successful import (or partial import), trigger reanalysis and wait for Cloud results to verify the configuration works as expected in the Cloud environment. Cloud analysis may differ from local analysis (different tool versions, containerized execution, file visibility).

**1. Trigger reanalysis and wait for completion:**

Use `--reanalyze-and-wait` to trigger reanalysis, poll automatically (every 10 seconds, up to 20 minutes), and get a delta report of issue changes by pattern, severity, and category:

```bash
codacy repository --reanalyze-and-wait -o json > .codacy/tmp/codacy-reanalysis-delta.json
```

This replaces manual polling. The CLI captures a baseline before reanalysis, waits for completion, and reports the full delta. If it times out after 20 minutes, it reports what it knows and exits — note the timeout in warnings and proceed without full Cloud verification.

**2. Fetch fresh Cloud overview and evaluate:**

Once reanalysis is complete (check the delta report), get the updated issue overview:
```bash
codacy issues -O -o json > .codacy/tmp/codacy-post-import-overview.json
```

Compare the post-import overview against the pre-import overview (`.codacy/tmp/codacy-cloud-overview.json`). For each pattern in the new overview, sorted by issue count (highest first):

- If a pattern has a **high issue count** and is **not** in the Security category and **not** Critical/High severity → it is a candidate for Cloud-side disabling
- Apply the same noise framework from Step 4b (wrong-language, convention mismatch, deduplication) using Cloud data
- For patterns that should be disabled, use the Cloud CLI:
  ```bash
  codacy pattern <toolId> <patternId> --disable
  ```
- If a disable fails due to Coding Standard enforcement, note it in warnings
- Also disable any patterns in the `cloudNoiseCloudOnly` list from Step 0c that were deferred for this moment

**4. Record Cloud verification results:**

Track all Cloud-side pattern changes in the summary under a new `cloudVerification` field:
```json
{
  "cloudVerification": {
    "reanalysisCompleted": true,
    "issuesBefore": 375,
    "issuesAfter": 280,
    "patternsDisabled": [
      {
        "patternId": "markdownlint_MD033",
        "toolId": "markdownlint",
        "reason": "Convention mismatch — 150 inline HTML issues in documentation files",
        "issueCount": 150
      }
    ],
    "warnings": []
  }
}
```

If reanalysis timed out or Cloud verification was skipped, set `reanalysisCompleted: false` and note the reason in warnings.

#### 6f. Show Cloud import results

Update the `importResults` field in `.codacy/configure-codacy-summary.json` with the import outcome:

```json
{
  "importResults": {
    "status": "success | completed_with_errors | failed",
    "toolsConfigured": 10,
    "toolsEnabled": ["markdownlint"],
    "toolsDisabled": ["PMD"],
    "errors": [
      {
        "toolId": "ESLint9",
        "error": "Conflict (409)",
        "detail": "Unable to update Project Tool Patterns, repository is using a Configuration File"
      },
      {
        "toolId": "PMD",
        "error": "Conflict (409)",
        "detail": "Cannot disable a tool that is enabled by a standard"
      }
    ],
    "warnings": [
      "7 Semgrep pattern parsing errors (non-blocking)",
      "Agentlinter: 0 files matched — no agent config files in this SPA"
    ],
    "codingStandards": ["AI Policy", "Our Default + SOC2"],
    "forceUsed": false
  }
}
```

**`importResults` field reference:**
- `status` — `"success"` if all tools imported without errors, `"completed_with_errors"` if some tools failed but others succeeded, `"failed"` if the import command itself failed
- `toolsConfigured` — number of tools successfully configured
- `toolsEnabled` — tools that were newly enabled in Cloud (were disabled before)
- `toolsDisabled` — tools that were disabled in Cloud (were enabled before) — may be empty if Coding Standard prevents disabling
- `errors` — array of per-tool errors, each with `toolId`, `error` (HTTP status or error type), and `detail` (the error message from the CLI)
- `warnings` — array of non-blocking warnings (analysis errors, tools with 0 files, etc.)
- `codingStandards` — names of Coding Standards linked to the repository (from Step 0), or empty array if none
- `forceUsed` — whether `--force` was used to unlink a Coding Standard

Present the import results to the user:
- What was updated successfully
- What couldn't be changed (Coding Standard enforcement) — list each error with its detail
- Cloud-only tool pattern changes (from 6c)
- Whether `--force` was used and what that implies

### Step 7: Clean-up

Remove the temporary directory and all intermediate files:

```bash
rm -rf .codacy/tmp
```

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
