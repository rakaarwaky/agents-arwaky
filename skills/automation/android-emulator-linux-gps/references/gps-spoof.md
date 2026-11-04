# GPS spoofing on the AOSP emulator

**Goal:** you can make the emulator report a mock GPS location that the app reads.

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

## Completion

- `adb shell dumpsys location` shows the mock `last location` with the expected
  coordinates while the fix loop is running.
- The target app receives the location (the app's UI / logs / logs via
  `adb logcat | grep Location` show the new value).
- The `add-test-provider` path was only used after `appops set com.android.shell android:mock_location allow`; `adb root` was NOT used to grant it.
