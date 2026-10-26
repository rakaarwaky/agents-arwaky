# Local tuning — Steps 1–3

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

