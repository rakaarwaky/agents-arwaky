# Issue Taxonomy — Web

Web-specific category detail. Shared severity levels and universal categories
live in `issue-taxonomy-general.md`.

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
