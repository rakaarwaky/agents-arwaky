# General QA Rules (all target types)

Shared evidence protocol, categorize rules, and report requirements that apply to
every target type. The 5-phase pipeline lives in `workflow.md`. Per-target
toolsets live in `web.md`, `terminal.md`, `desktop.md`, and `mobile.md`.

## Output directory layout

```
{output_dir}/
├── screenshots/       # Visual evidence (web, desktop, mobile)
├── transcripts/       # Terminal output (terminal/TUI)
├── logs/              # Console / logcat / stderr captures
└── report.md          # Final report
```

## Evidence protocol

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
3. **Classify** using the issue taxonomy section of the matching per-target
   reference file (`web.md`, `terminal.md`, `desktop.md`, or `mobile.md`).
   Severity and category are target-aware.

## Categorize rules

1. Review all collected issues.
2. De-duplicate — merge the same bug manifesting in different places.
3. Assign final severity and category.
4. Sort: Critical → High → Medium → Low.
5. Count by severity and category for the executive summary.

## Report requirements

Generate the final report using `../templates/dogfood-report-template.md`. Save
to `{output_dir}/report.md`. The report must include:

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

# Issue Taxonomy — General (all target types)

Shared severity levels and universal categories that apply to every target type.

## Severity Levels

### Critical
The issue makes a core feature completely unusable or causes data loss.

**Examples (all targets):**
- Application crashes or shows a blank white page / black terminal / ANR
- Form submission or command execution silently loses user data
- Authentication is completely broken
- Payment flow fails and charges the user without completing the order
- Security vulnerability (XSS, exposed credentials in console or logs)
- Uncaught exception in `logcat` (mobile) or fatal panic (terminal)

### High
The issue significantly impairs functionality but a workaround may exist.

**Examples:**
- A key button or command does nothing (but retrying or refreshing fixes it)
- Search returns no results for valid queries
- Form validation rejects valid input
- Critical content is missing or garbled
- Navigation leads to a 404 or wrong screen
- TUI renders as a wall of unformatted text (layout broken at common terminal sizes)
- Terminal command hangs on non-interactive stdin instead of failing fast
- App does not return to the expected screen on back navigation (mobile)

### Medium
The issue is noticeable and affects user experience but doesn't block core functionality.

**Examples:**
- Layout misaligned or overlapping on certain screen sections
- Images or assets fail to load
- Slow performance (visible delays > 3 seconds)
- Form field lacks validation feedback
- Console / logcat warnings that suggest deprecated or misconfigured features
- Inconsistent styling between similar screens
- TUI colors or alignment break under specific TERM values or in a specific terminal emulator
- Desktop app window restores at wrong size or position on relaunch

### Low
Minor polish issues that don't affect functionality.

**Examples:**
- Typos or grammatical errors in text content
- Minor spacing or alignment inconsistencies
- Placeholder text left in production ("Lorem ipsum")
- Favicon missing; `--version` output missing in `--help`
- Console info/debug messages that shouldn't be in production
- Subtle color contrast issues that don't fail WCAG requirements
- Touch target smaller than 48 dp (mobile) but still tappable
- TUI missing a help hint or keyboard-shortcut legend

## Categories (universal)

These categories apply to every target type.

### Functional (all)
Issues where features don't work as expected.
- Buttons / links / commands that don't respond
- Forms that don't submit or submit incorrectly
- Broken multi-step flows
- Incorrect data displayed
- Features that work partially

### Visual (all)
Issues with the visual presentation.
- Layout problems (overlapping elements, broken grids)
- Broken images or missing media
- Styling inconsistencies
- Responsive / responsive-rewindowing design failures
- Z-index issues
- Text overflow or truncation

### Accessibility (all)
Issues that prevent or hinder access for users with disabilities.
- Missing alt text on meaningful images
- Poor color contrast (fails WCAG AA)
- Elements not reachable via keyboard navigation
- Missing form labels or ARIA attributes
- Focus indicators missing or unclear
- Screen reader incompatible content

### Console (all)
Issues detected through runtime log output.
- Uncaught exceptions and unhandled promise rejections
- Failed network requests (4xx, 5xx)
- Deprecation warnings
- CORS errors
- Excessive console.log output left from development

### UX (all)
Issues where functionality works but the experience is poor.
- Confusing navigation or information architecture
- Missing loading indicators
- No feedback after user actions
- Inconsistent interaction patterns
- Missing confirmation dialogs for destructive actions
- Poor error messages that don't help the user recover

### Content (all)
Issues with the text, media, or information on the surface.
- Typos and grammatical errors
- Placeholder / dummy content in production
- Outdated information
- Missing content (empty sections)
- Broken or dead external links
- Incorrect or misleading labels


