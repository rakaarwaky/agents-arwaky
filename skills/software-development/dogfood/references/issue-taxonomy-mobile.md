# Issue Taxonomy — Mobile (Android)

Android-specific category detail. Shared severity levels and universal categories
live in `issue-taxonomy-general.md`.

## Visual (mobile)
- layout breakage in landscape; content clipped at small screen sizes
- touch target smaller than 48 dp (Material minimum) but still tappable
- images or assets fail to load on specific screens

## Console (mobile)
- `logcat` `AndroidRuntime` / `FATAL EXCEPTION` lines
- `ANR` traces (Application Not Responding)
- failed network requests (4xx, 5xx) during app operation

## Accessibility (mobile)
- missing `content-desc` on interactive elements
- touch targets too small for reliable tapping
- screen reader (TalkBack) announces wrong or empty labels

## UX (mobile)
- app re-asks permissions every cold start
- no offline state handling
- app backgrounded and re-entered loses scroll position or form state
- cold start shows blank screen longer than expected (slow first frame)
- permission dialog handling: granting vs denying each permission leads to
  the wrong state

## Functional (mobile)
- ANR (Application Not Responding) on main thread
- crash on rotation (state not saved / restored)
- back button skips screens or exits the app from a nested screen
- app misbehaves in split-screen / multi-window mode
- GPS / location permission not requested before first use
