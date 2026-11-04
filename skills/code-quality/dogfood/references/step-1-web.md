# Web Target — Toolset and Workflow

Full web QA workflow using the `browser_*` toolset. This is the original dogfood
flow, preserved unchanged.

## Prerequisites

- Browser toolset: `browser_navigate`, `browser_snapshot`, `browser_click`,
  `browser_type`, `browser_vision`, `browser_console`, `browser_scroll`,
  `browser_back`, `browser_press`
- A target URL and testing scope from the user

## Explore rhythm

For each page or feature:

1. **Navigate:** `browser_navigate(url="...")`
2. **Snapshot:** `browser_snapshot()` — get the DOM / accessibility tree
3. **Console check:** `browser_console(clear=true)` — do this after every
   navigation and every significant interaction
4. **Visual + annotate:** `browser_vision(question="...", annotate=true)`
   — numbered `[N]` labels map to ref `@eN`
5. **Interact:** `browser_click(ref="@eN")`, `browser_type(ref="@eN", text="...")`,
   `browser_press(key="Tab")`, `browser_scroll(direction="down")`
6. **Verify:** re-check console + `browser_vision` for visual changes
7. **Evidence:** `browser_vision(question="...", annotate=false)` → save `screenshot_path`

## Tips

- Silent JS errors are among the most valuable findings — always check the console.
- Test form validation with invalid inputs (empty, too long, special chars, SQL injection patterns).
- Test keyboard navigation (Tab, Enter, Escape) for accessibility.
- Check empty states, 404 pages, and broken external links.
- Note layout issues visible in screenshots (overlapping elements, broken grids).
# Issue Taxonomy — Web

Web-specific category detail. Shared severity levels and universal categories

## Visual (web)
- (web) responsive design failures: layout breaks at mobile/tablet widths
- (web) broken images / missing media on specific routes
- (web) z-index issues: elements hidden behind others
- (web) text overflow or truncation in constrained containers

## Console (web)
- (web) uncaught JavaScript exceptions on core pages
- (web) failed network requests (4xx, 5xx) in the console
- (web) CORS errors, mixed-content warnings (HTTP on HTTPS)
- (web) deprecation warnings from frameworks or libraries

## Accessibility (web)
- (web) missing alt text on meaningful images
- (web) elements not reachable via keyboard navigation (Tab, Enter, Escape)
- (web) missing form labels or ARIA attributes
- (web) focus indicators missing or unclear
- (web) poor color contrast (fails WCAG AA)

## UX (web)
- (web) missing loading indicators (user doesn't know something is happening)
- (web) no feedback after user actions (button click with no visible result)
- (web) missing confirmation dialogs for destructive actions
- (web) confusing navigation or information architecture

## Content (web)
- (web) placeholder / dummy content in production ("Lorem ipsum")
- (web) broken or dead external links
- (web) outdated information on landing or pricing pages

