# Orca Emulator — iOS Simulator control

iOS Simulator control from inside Orca, with the live device view in Orca's
emulator pane. Use when driving a booted Apple Simulator on macOS: taps, gestures,
typing, hardware buttons, rotation, and the accessibility tree, or when an iOS
change needs simulator evidence. Build and install the app with `xcodebuild`
or `simctl` first.

For an Android device or emulator use [emulator-android.md](emulator-android.md).

Prefer Orca over raw `serve-sim` or direct `simctl` for simulator control inside
Orca; it handles device scoping, helper lifecycle, and worktree context.

## Load the version-matched guide

```text
ORCA skills get orca-emulator
```
