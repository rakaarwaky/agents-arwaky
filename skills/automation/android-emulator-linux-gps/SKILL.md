---
name: android-emulator-linux-gps
description: Use when running or installing Android apps on a Linux host with the AOSP emulator and spoofing GPS via adb emu geo fix, including AVD setup, x86 image ABI selection, and apkpure/apkcombo APK retrieval.
when-to-use: Use when the user wants the Android emulator on Linux, Deepin or X11 hosts, an AVD that boots headlessly, 32-bit ARM APK installation, Android GPS spoofing or mock location, or apkpure/apkcombo APK downloads without browser automation.
argument-hint: "<emulator | avd | gps | apk> [options] | <freeform task>"
metadata:
  tags: []
---

# Android emulator on Linux + GPS spoofing

You set up and drive the AOSP/Android SDK emulator on a Linux (Debian/Deepin) host,
install APKs, and spoof GPS. Prefer the AOSP emulator over Waydroid: Waydroid needs a
Wayland session (fails on X11-only Deepin) and has no host-side GPS hook (you can only
mock from inside Android with a dev app + `appops ... mock_location`), while the
`emulator` has a first-class GPS console command.

## Global rules

- **One APK, one ABI check first.** Before install, verify the image's
  `ro.product.cpu.abilist` covers the APK's `lib/` ABIs; x86_64 `google_apis` images
  translate arm64-v8a only, so 32-bit-ARM APKs need an x86 image.
- **Never run `avdmanager` and `emulator` with different AVD homes** — on Deepin they
  disagree by default; fix it once (see the avd reference) and keep the env override
  exported for the whole session.
- **Mock GPS is a loop, not a one-shot.** `last location` clears on each new `geo fix`;
  send the fix repeatedly (2s loop) while the app reads it.

## Routing

| Topic | Reference | Purpose |
| ----- | --------- | ------- |
| AVD setup & ABI | [`references/avd-and-abi.md`](references/avd-and-abi.md) | apt install, Deepin AVD-path gotcha, x86 vs x86_64 image choice. |
| APK retrieval | [`references/apk-retrieval.md`](references/apk-retrieval.md) | apkpure/apkcombo direct endpoints, `adb install-multiple`. |
| GPS spoofing | [`references/gps-spoof.md`](references/gps-spoof.md) | `adb emu geo fix` loop vs `add-test-provider`, permission grants. |
| Headless UI & host | [`references/headless-and-host.md`](references/headless-and-host.md) | `uiautomator dump` poking, Deepin host facts. |
