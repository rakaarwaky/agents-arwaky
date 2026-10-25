# Configure Codacy summary JSON schema

The full `.codacy/configure-codacy-summary.json` schema (before/after metrics, tool/pattern changes, file exclusions, security coverage, cloud verification, and the field reference) that Step 5a generates.

#### 5a. Generate summary JSON

Write `.codacy/configure-codacy-summary.json` with the before/after metrics, a detailed change log, and supporting context. Runtime values are in milliseconds (raw `durationMs` from the CLI).

**The `before` values come from Step 0** (the baseline captured before any changes — Cloud config for Track A, local config for Track B, or unconfigured for Track C). **The `after` values come from Step 4f** (the final tuned configuration). If no initial config existed (Track C), `before` values reflect an unconfigured state — use `null` for metrics that cannot be measured (e.g., runtime) and `0` for counts (patterns, tools, issues).

```json
{
  "summary": {
    "enabledPatterns": { "before": 1000, "after": 300 },
    "enabledTools": { "before": 34, "after": 15 },
    "issues": { "before": 7000, "after": 550 },
    "analysisRuntime": { "before": 240000, "after": 60000 }
  },
  "toolChanges": [
    {
      "toolId": "Biome",
      "action": "disabled",
      "reason": "Project uses ESLint9 with local config; Biome is redundant and produced 16K false positives in TypeScript",
      "patternsAffected": 232
    },
    {
      "toolId": "markdownlint",
      "action": "enabled",
      "reason": "New tool added for Markdown linting; README.md excluded per-tool to avoid inline HTML noise",
      "patternsAffected": 43
    }
  ],
  "patternChanges": [
    {
      "patternId": "Semgrep_python.lang.security.audit.xss.template-injection",
      "toolId": "Semgrep",
      "action": "disabled",
      "reason": "Wrong stack — pattern for Python; project is JavaScript-only",
      "delta": -45,
      "parameters": []
    },
    {
      "patternId": "Lizard_ccn-medium",
      "toolId": "Lizard",
      "action": "updated",
      "reason": "Raised threshold from 10 to 20 to match codebase complexity profile",
      "delta": -120,
      "parameters": [
        { "id": "threshold", "before": "10", "after": "20" }
      ]
    },
    {
      "patternId": "Semgrep_codacy.javascript.security.hard-coded-password",
      "toolId": "Semgrep",
      "action": "enabled",
      "reason": "New High Security pattern — detects hardcoded passwords; found 101 issues across 41 files for review",
      "delta": 101,
      "parameters": []
    }
  ],
  "fileExclusions": {
    "global": ["src/routeTree.gen.ts"],
    "perTool": {
      "markdownlint": ["README.md"]
    }
  },
  "securityCoverage": {
    "deduplication": [
      "Semgrep slack-webhook-url disabled — same concern covered by Semgrep detected-slack-webhook"
    ],
    "newCoverage": [
      "unsafe-dynamic-method (Critical, 5 issues)",
      "open-redirect-from-function (Critical, 4 issues)",
      "hard-coded-password (High, 101 issues)"
    ],
    "noisyButKept": [
      "Semgrep hard-coded-password (101 issues) — kept per security guardrail, file exclusions preferred over disabling"
    ]
  },
  "keyImprovements": [
    "Lizard complexity thresholds tuned to match mature React SPA — 576 fewer noise issues while keeping genuinely complex functions flagged",
    "6 new security patterns detecting open redirects, unsafe dynamic methods, hardcoded passwords, and React href injection (119 new findings)",
    "markdownlint added for Markdown quality",
    "Checkov expanded from 6 to 1358 IaC security patterns"
  ],
  "localConfigTools": [
    {
      "toolId": "ESLint9",
      "configFile": "eslint.config.js",
      "issueCount": 42,
      "note": "Issues from this tool are controlled by the project's ESLint config, not Codacy patterns. Edit eslint.config.js to reduce noise."
    }
  ],
  "codacyYaml": null,
  "importResults": null,
  "cloudVerification": null
}
```

**Field reference:**

**`summary`** — before/after metrics (same as before).

**`toolChanges`** — one entry per tool added or removed. Each entry:
- `toolId` — the tool identifier
- `action` — `"enabled"` (tool was added) or `"disabled"` (tool was removed)
- `reason` — why the tool was added or removed
- `patternsAffected` — number of patterns in the tool that was added/removed

**`patternChanges`** — one entry per individual pattern change. Each entry:
- `patternId` — the pattern identifier
- `toolId` — which tool this pattern belongs to
- `action` — `"enabled"`, `"disabled"`, or `"updated"`
- `reason` — why this change was made (auditability)
- `delta` — the change in issue count for this pattern, comparing INITIAL state (Step 0) vs FINAL tuned state (Step 4f). If the pattern was not enabled in the initial config, the delta is the full issue count from the tuned analysis (positive if newly enabled, 0 if disabled during tuning).
- `parameters` — parameter changes (empty array if not applicable)

Do NOT include individual pattern entries inside `patternChanges` for patterns that were added/removed as part of a whole tool change. Those are covered by the `toolChanges` entry. `patternChanges` is for surgical, individual pattern changes within a tool that remains enabled.

Do NOT include `"restored"` patterns here. Restoration (Step 4e) is an internal mechanism to ensure patterns from the baseline config that had Critical/High/Security results aren't lost by `init --auto`. It preserves what was already there — it's not a user-facing change.

**`fileExclusions`** — only lists **new** exclusions added during this tuning run. Exclusions already present in the baseline config are preserved automatically but not listed here (they are not changes).
- `global` — new global exclusion globs added during tuning
- `perTool.<toolId>` — new per-tool exclusion globs added during tuning

Omit `fileExclusions` entirely if no new exclusions were added.

**`securityCoverage`** — documents how security concerns are handled:
- `deduplication` — security patterns that were disabled because another pattern covers the same concern (list the kept pattern and the disabled one)
- `newCoverage` — new security patterns enabled that were NOT in the baseline config, with issue count
- `noisyButKept` — security patterns that are noisy but were kept active per the security guardrail

**`keyImprovements`** — array of 3–6 human-readable sentences summarizing the most impactful improvements. Focus on what changed and the quantitative impact. These should be suitable for presenting to the user as a summary.

**`localConfigTools`** — array of tools that have `useLocalConfigurationFile: true`. Each entry includes:
- `toolId` — the tool identifier
- `configFile` — path to the project's config file used by this tool
- `issueCount` — number of issues this tool produced in the tuned analysis
- `note` — human-readable explanation that noise from this tool is governed by the project's own config, not Codacy patterns

Empty array if no tools use local configuration files.

**`codacyYaml`** — string containing the generated `.codacy.yaml` file content if file exclusions were added (see Step 5c). `null` if no `.codacy.yaml` was generated.

**`importResults`** — `null` until Step 6 runs. If Cloud import is performed, this is populated with the results (see Step 6f for the schema).

**`cloudVerification`** — `null` unless Step 6e runs. Contains post-import Cloud verification results: whether reanalysis completed, issue counts before/after, patterns disabled on Cloud, and warnings. See Step 6e for the schema.

