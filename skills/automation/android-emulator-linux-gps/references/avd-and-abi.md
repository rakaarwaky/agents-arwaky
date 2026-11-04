# AVD setup and ABI selection

**Goal:** you can install the AOSP emulator on Debian/Deepin, create an AVD that boots
headlessly, and pick an image ABI that actually runs the target APK.

## Install (Debian/Deepin, apt)

`sudo apt-get install -y openjdk-17-jdk unzip cpio lxc` then commandlinetools-linux from
dl.google.com into `$SDK/cmdline-tools/latest`, `yes | sdkmanager --licenses`, and
`sdkmanager platform-tools emulator "system-images;<api>;google_apis;<abi>"`.

## AVD path gotcha (Deepin/UnityTOS)

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

## Completion

- The emulator boots headless (`emulator -no-boot-anim` + `adb wait-for-device` + poll
  `getprop sys.boot_completed`).
- The installed image's `ro.product.cpu.abilist` covers the APK's `lib/` ABIs — re-check
  with `adb shell dumpsys package <pkg> | grep -E 'versionName|primaryCpuAbi'` after
  install.
