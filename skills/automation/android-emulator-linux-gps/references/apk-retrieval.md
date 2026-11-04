# Getting an APK without fighting Cloudflare

**Goal:** you can fetch base/split APKs from apkpure or apkcombo with plain curl and
install them onto the emulator.

apkpure/apkcombo web pages are JS+CF gated, but their direct endpoints work with plain
curl + a browser UA + Referer:

- `https://d.apkpure.com/b/XAPK/<pkgid>?version=latest` → XAPK (zip: base+split apks +
  manifest.json)
- `https://d.apkpure.com/b/APK/<pkgid>?version=latest` → base APK only (fails if splits
  required)
- apkcombo: HTML contains `https://apkcombo.com/d?u=<base64>` → base64-decode for real
  URL

Install: unzip, then
`adb install-multiple base.apk config.<abi>.apk config.<lang>.apk config.<dpi>.apk`.

## Completion

- `adb install-multiple` reports `Success` for every APK.
- `adb shell dumpsys package <pkg> | grep -E 'versionName|primaryCpuAbi'` shows the
  expected version and ABI.
