# General QA Workflow (all target types)

Shared pipeline, evidence protocol, and reporting rules that apply to every
target type. Per-target toolsets live in `web.md`, `terminal.md`,
`desktop.md`, and `mobile.md`.

## Output directory layout

```
{output_dir}/
├── screenshots/       # Visual evidence (web, desktop, mobile)
├── transcripts/       # Terminal output (terminal/TUI)
├── logs/              # Console / logcat / stderr captures
└── report.md          # Final report
```

## Phase 1: Plan

1. Create the output directory structure above.
2. Identify the testing scope from user input.
3. Build a rough test plan based on target type:
   - **web** — landing page, navigation links, key user flows (sign up, login,
     search, checkout), forms, empty states, 404s, edge cases.
   - **terminal / TUI** — `--help` output, each subcommand, invalid arguments,
     pipe behavior, TUI rendering at multiple terminal sizes, signal handling
     (SIGINT, SIGTERM), non-interactive mode (stdin closed / `</dev/null`).
   - **desktop** — app launch, each menu item, toolbars, dialogs, drag-and-drop,
     file open/save flows, accessibility tree coverage, error dialogs.
   - **mobile** — cold start, each screen, navigation (back button, in-app nav),
     form input, touch targets, screen rotation, permission dialogs,
     background/foreground transitions.

## Phase 3: Collect Evidence

For every issue found, regardless of target type:

1. **Capture the evidence:**
   - web / desktop / mobile → screenshot saved to `{output_dir}/screenshots/`
   - terminal / TUI → transcript saved to `{output_dir}/transcripts/`
2. **Record the details:**
   - **Location** — URL (web), command + args (terminal), app + window + element
     index (desktop), device + package + screen (mobile)
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Evidence path (screenshot or transcript)
   - Runtime log lines if relevant (console errors, logcat, stderr)
3. **Classify** using `references/issue-taxonomy-general.md` plus the target-specific
   file (`issue-taxonomy-web.md`, `issue-taxonomy-terminal.md`,
   `issue-taxonomy-desktop.md`, or `issue-taxonomy-mobile.md`). Severity and category are
   target-aware — the taxonomy has target-specific categories in addition to the
   shared ones.

## Phase 4: Categorize

1. Review all collected issues.
2. De-duplicate — merge the same bug manifesting in different places.
3. Assign final severity and category.
4. Sort: Critical → High → Medium → Low.
5. Count by severity and category for the executive summary.

## Phase 5: Report

Generate the final report using `templates/dogfood-report-template.md`. Save to
`{output_dir}/report.md`. The report must include:

1. **Executive summary** — total issue count, breakdown by severity, target type,
   testing scope
2. **Per-issue sections** — location, severity/category badges, description, repro
   steps, expected vs actual, evidence reference (`MEDIA:<screenshot_path>` for
   images, inline code block for transcripts), runtime log lines
3. **Summary table** — all issues, sorted by severity
4. **Testing coverage** — what was tested, what was not, any blockers
5. **Notes** — observations and recommendations specific to the target type

## Shared tips (all targets)

- Always capture evidence *before* moving on to the next step — state is gone once
  you leave.
- Test with both valid and invalid inputs — validation bugs are the most common
  findings.
- Test edge cases: empty inputs, very long inputs, special characters, rapid
  repeated actions.
- De-duplicate before reporting — the same bug often surfaces in multiple places.
