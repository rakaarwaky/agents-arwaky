# Mobile Target — Toolset and Workflow

QA workflow for Android apps on an AOSP emulator via `adb`.
See the [android-emulator-linux-gps skill](../../automation/android-emulator-linux-gps/SKILL.md)
for AVD setup, ABI selection, and headless operation.

## Prerequisites

- An AOSP/Android emulator is booted and connected (`adb devices` shows a device).
- The target APK is installed on the device.
- `adb` is on PATH.

## Explore rhythm

1. **Verify the app is installed and launches:**
   ```bash
   adb shell pm path <package>          # confirm APK is present
   adb shell monkey -p <package> -c android.intent.category.LAUNCHER 1
   ```

2. **Capture the accessibility tree:**
   ```bash
   adb shell uiautomator dump /sdcard/window_dump.xml
   adb pull /sdcard/window_dump.xml {output_dir}/screenshots/<n>-dump.xml
   ```
   Parse `bounds="[x1,y1][x2,y2]"` + `text=` / `content-desc=` to locate elements.

3. **Tap an element** (center of its bounds):
   ```bash
   adb shell input tap <cx> <cy>
   ```

4. **Type text:**
   ```bash
   adb shell input text "hello"
   ```

5. **Swipe (scroll, dismiss, navigate):**
   ```bash
   adb shell input swipe <startX> <startY> <endX> <endY> <duration_ms>
   ```

6. **Screencap** — save to local evidence dir:
   ```bash
   adb exec-out screencap -p > {output_dir}/screenshots/<n>.png
   ```

7. **logcat** — capture the app's runtime logs between actions:
   ```bash
   adb logcat -d --pid=$(adb shell pidof <package>) 2>&1 | tail -50
   ```
   `ANDROID_LOG_ERROR` lines and uncaught exceptions in logcat are high-value
   findings.

8. **Test back navigation:**
   ```bash
   adb shell input keyevent KEYCODE_BACK
   ```
   Verify the app returns to the expected screen.

9. **Rotation:**
   ```bash
   adb shell cmd display set-user-rotation 1   # 90°
   adb shell cmd display set-user-rotation 0   # reset
   ```

10. **Evidence** — save screenshots to `{output_dir}/screenshots/`, logcat captures
    to `{output_dir}/logs/`, uiautomator dumps to `{output_dir}/screenshots/`.

## Tips

- Test cold start separately from warm start (kill the app, re-launch).
- Verify permission dialogs are handled — granting vs denying each permission
  path.
- Rotate the screen on key flows — layout breakage in landscape is a common
  finding.
- `logcat` uncaught exceptions are Critical severity by default.
- Check touch targets are at least 48 dp (Material minimum).
- Test with TalkBack enabled — missing `content-desc` on interactive elements is
  an accessibility failure.
- Test background/foreground transitions — does the app lose scroll position or
  form state?
