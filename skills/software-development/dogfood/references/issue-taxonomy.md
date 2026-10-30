# Issue Taxonomy

Use this taxonomy to classify issues found during dogfood QA testing.
Severity levels are shared across all target types. Categories include
target-specific ones — use the target-applicable set.

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

## Categories

Categories marked **(all)** apply to every target type. Target-specific
categories apply only to their target.

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
- (terminal) TUI garbling: misaligned columns, broken box-drawing, lost cursor after resize
- (mobile) layout breakage in landscape; content clipped at small screen sizes

### Accessibility (all)
Issues that prevent or hinder access for users with disabilities.
- Missing alt text on meaningful images
- Poor color contrast (fails WCAG AA)
- Elements not reachable via keyboard navigation
- Missing form labels or ARIA attributes
- Focus indicators missing or unclear
- Screen reader incompatible content
- (mobile) missing `content-desc` on interactive elements; touch targets too small

### Console (all)
Issues detected through runtime log output.
- Uncaught exceptions and unhandled promise rejections
- Failed network requests (4xx, 5xx)
- Deprecation warnings
- CORS errors
- Excessive console.log output left from development
- (terminal) stderr noise on success; non-zero exit code with no stderr message
- (mobile) `logcat` `AndroidRuntime` / `FATAL EXCEPTION` lines; `ANR` traces

### UX (all)
Issues where functionality works but the experience is poor.
- Confusing navigation or information architecture
- Missing loading indicators
- No feedback after user actions
- Inconsistent interaction patterns
- Missing confirmation dialogs for destructive actions
- Poor error messages that don't help the user recover
- (terminal) error messages that don't name the failing subcommand or suggest a fix
- (desktop) app not responding to the OS (spinner cursor) during long operations
- (mobile) app re-asks permissions every cold start; no offline state handling

### Content (all)
Issues with the text, media, or information on the surface.
- Typos and grammatical errors
- Placeholder / dummy content in production
- Outdated information
- Missing content (empty sections)
- Broken or dead external links
- Incorrect or misleading labels

### Terminal (terminal/TUI)
Issues specific to command-line and TUI applications.
- Wrong or missing exit codes (0 on failure, non-zero on success)
- `--help` / `--version` output incomplete or inaccurate
- Command hangs on piped / closed stdin instead of failing fast
- Signal handling: SIGINT / SIGTERM leaves the process running or corrupts state
- TUI assumes a minimum terminal size and breaks below it
- TUI cursor position lost after terminal resize
- Output uses non-portable escape sequences that break on common terminals
- Locale / `LANG` not respected; UTF-8 mojibake
- Config file not found error is cryptic; no `--config` flag documented

### Mobile (mobile/Android)
Issues specific to Android apps.
- ANR (Application Not Responding) on main thread
- Crash on rotation (state not saved / restored)
- Back button skips screens or exits the app from a nested screen
- Permission dialog handling: granting vs denying each permission leads to the wrong state
- Cold start shows blank screen longer than expected (slow first frame)
- App backgrounded and re-entered loses scroll position or form state
- Touch target smaller than 48 dp (Material minimum)
- Screen reader (TalkBack) announces wrong or empty labels
- App misbehaves in split-screen / multi-window mode
- GPS / location permission not requested before first use
