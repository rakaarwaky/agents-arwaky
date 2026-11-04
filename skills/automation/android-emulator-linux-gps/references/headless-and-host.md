# Headless UI poking and Deepin host facts

**Goal:** you can poke the Android UI without screenshots, and you know the Deepin host
facts that make the setup work.

## Headless UI poking (no screenshots needed)

`adb shell uiautomator dump` then read `/sdcard/window_dump.xml`; grep
`text=`/`content-desc=` + `bounds="[x1,y1][x2,y2]"` → `adb shell input tap cx cy`.
`adb shell monkey -p <pkg> -c android.intent.category.LAUNCHER 1` to launch.

## Deepin host facts

X11 session + kwin_x11, /dev/kvm group-accessible, `-gpu host` works, boots in ~27s.
`emulator -no-boot-anim` + `adb wait-for-device` + poll `getprop sys.boot_completed`.

## Completion

- The tapped element reacts (UI state changes, logcat shows the click) without any
  screenshot tooling.
- The AVD boots to `sys.boot_completed=1` on the host you are on.
