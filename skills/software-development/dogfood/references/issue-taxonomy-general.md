# Issue Taxonomy — General (all target types)

Shared severity levels and universal categories that apply to every target type.
Target-specific categories live in `issue-taxonomy-web.md`,
`issue-taxonomy-terminal.md`, `issue-taxonomy-desktop.md`, and
`issue-taxonomy-mobile.md`.

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
