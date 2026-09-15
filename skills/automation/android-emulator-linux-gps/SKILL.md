---
name: android-emulator-linux-gps
description: Use when running Android apps on Linux with spoofable GPS.
metadata:
  tags: []
---

# Android emulator on Linux + GPS spoofing

## Why AOSP emulator, not Waydroid
Waydroid needs a Wayland session (fails on X11-only Deepin) and has NO host-side GPS
hook — you can only mock from inside Android with a dev app + `appops ... mock_location`.
The AOSP/Android SDK emulator has a first-class GPS console command, so prefer it.

## Install (Debian/Deepin, apt)
`sudo apt-get install -y openjdk-17-jdk unzip cpio lxc` then commandlinetools-linux from
dl.google.com into `$SDK/cmdline-tools/latest`, `yes | sdkmanager --licenses`, and
`sdkmanager platform-tools emulator "system-images;<api>;google_apis;<abi>"`.

### AVD path gotcha (Deepin/UnityTOS)
`avdmanager` writes AVDs to `$HOME/.config/.android/avd`, but `emulator` only looks in
`$HOME/.android/avd` → "Unknown AVD name". Fix: move the `.avd`+`.ini` into
`~/.android/avd`, patch `path=`/`path.rel=` in `<name>.ini`, and export
`ANDROID_AVD_HOME=$HOME/.android/avd`. Never symlink `~/.android` into itself.
Also set `disk.dataPartition.path=<avddir>/userdata-qemu.img` in `config.ini` (default
`<temp>` wipes installed apps every boot).

## ABI trap — the one that costs the most time
x86_64 `google_apis` images translate **arm64-v8a only**. Many Indonesian/universal APKs
(Flutter apps on apkpure: `config.armeabi_v7a.apk`) ship **32-bit ARM only** →
`INSTALL_FAILED_NO_MATCHING_ABIS: Failed to extract native libraries, res=-113`.
Adding `hw.cpu.abilist32`/`ro.product.cpu.abilist32` to config.ini does NOT help.

**Fix: install an x86 (32-bit) image**, which has built-in ARM translation:
`system-images;android-30;google_apis;x86` → `ro.product.cpu.abilist=x86,armeabi-v7a,armeabi`.
Check first: `unzip -l <split>.apk | grep -oE 'lib/[a-z0-9_-]+/' | sort -u`.

## Getting an APK without fighting Cloudflare
apkpure/apkcombo web pages are JS+CF gated, but their direct endpoints work with plain
curl + a browser UA + Referer:
- `https://d.apkpure.com/b/XAPK/<pkgid>?version=latest` → XAPK (zip: base+split apks + manifest.json)
- `https://d.apkpure.com/b/APK/<pkgid>?version=latest` → base APK only (fails if splits required)
- apkcombo: HTML contains `https://apkcombo.com/d?u=<base64>` → base64-decode for real URL
Install: unzip, then `adb install-multiple base.apk config.<abi>.apk config.<lang>.apk config.<dpi>.apk`.
Verify with `adb shell dumpsys package <pkg> | grep -E 'versionName|primaryCpuAbi'`.

## Headless UI poking (no screenshots needed)
`adb shell uiautomator dump` then read `/sdcard/window_dump.xml`; grep
`text=`/`content-desc=` + `bounds="[x1,y1][x2,y2]"` → `adb shell input tap cx cy`.
`adb shell monkey -p <pkg> -c android.intent.category.LAUNCHER 1` to launch.

## GPS spoof — the actual deliverable
Two independent mechanisms; know which one works:
1. **Console `geo fix <lon> <lat>`** (lon FIRST) — `adb emu geo fix ...` needs no telnet
   auth token. Verified: `dumpsys location` shows
   `last location=Location[gps -6.175402,106.827159 hAcc=100.0 ... mock]`. Only updates
   while something requests GPS (`ProviderRequest[ON]` in `dumpsys location`), and
   `last location` is cleared on each new `geo fix`, so send repeatedly (2s loop) while
   the app reads it.
2. **`cmd location providers add-test-provider gps`** → `SecurityException: not allowed to
   perform MOCK_LOCATION` unless `appops set com.android.shell android:mock_location allow`
   first. `adb root` makes it WORSE (uid 0 also denied).
Also needed: `settings put secure location_mode 3` + `cmd location set-location-enabled
true` + `pm grant <pkg> ACCESS_FINE_LOCATION` (skips the runtime permission dialog).

Helper script pattern: `~/bin/gps-set.sh <lon> <lat> [--route]` (try `adb emu`, fall back
to telnet+`~/.emulator_console_auth_token`) and `~/bin/android.sh [avd|stop]`.

## Deepin host facts
X11 session + kwin_x11, /dev/kvm group-accessible, `-gpu host` works, boots in ~27s.
`emulator -no-boot-anim` + `adb wait-for-device` + poll `getprop sys.boot_completed`.
