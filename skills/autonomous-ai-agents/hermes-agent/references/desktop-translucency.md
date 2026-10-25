# Desktop App — Window Translucency / See-Through Window

Diagnose and fix a Hermes desktop window that looks transparent, faded, or
"glassy" — and make the fix survive relaunches. This is a distinct subsystem
from themes/skins (which color surfaces) and from desktop plugins (which add
UI). Translucency changes the **native window opacity** of the whole Electron
window so the desktop shows through.

## When to Use

- "My Hermes desktop GUI is transparent / see-through / faded."
- "The window looks glassy / ghostly; the wallpaper bleeds through."
- "I turned off translucency but it comes back after I restart the app."
- A persisted desktop setting that keeps reverting to a stale value on launch.

## The Two Stores That Fight Each Other

This is the crux of the whole task. Translucency state lives in **two
independent stores**, and only aligning BOTH makes the fix stick:

1. **`~/.config/Hermes/translucency.json`** (Electron `userData`).
   - Fields: `{ intensity, fade, mode, material, scope }`.
   - **Main process** reads this on cold launch and applies it to every chat
     window at creation. It also **writes it back** on clean quit
     (`before-quit`) and after every live IPC change.
   - `intensity` 0–100 is the lever. `mode` is `'clear'` or `'glass'`.
     In `clear` mode, `intensity` maps straight to native window opacity:
     `opacity = 1 - 0.7·(intensity/100)²`. So `intensity: 29` → ~0.86 opacity
     (the see-through look). `intensity: 0` → 1.0 (fully opaque).
   - `glass` mode instead thins the page surfaces over a platform material and
     only the separate `fade` field touches native opacity.

2. **The renderer's localStorage book** (Chromium `Local Storage/leveldb`, key
   `hermes.desktop.translucency.v2`, legacy `v1`).
   - The **renderer** owns this. On boot it re-seeds and sends its resolved
     state over IPC (`hermes:translucency`), which main then persists back to
   `translucency.json`.
   - If the file is edited but the renderer book still holds the old value, the
     **next launch resurrects it** — this is exactly why "just edit the
     JSON" does not stick.

### Platform gate (important for triage)

`TRANSLUCENCY_SUPPORTED` / `GLASS_SUPPORTED` are computed from the OS:
- **Linux: neither is supported** — the native fade (`setOpacity`) is a
documented no-op on X11, and there is no platform material. The Settings row
is hidden on Linux.
- macOS + Windows 11 22H2+: fully supported.

So on a Linux box, the ONLY way a stale `translucency.json` value has ever
reached the window is through the **stale persisted file + a prior
cross-platform state**. The lever itself does nothing natively on Linux; the
fix is still to zero the file so a clean-quit flush or a future
cross-platform relaunch cannot re-apply a stale value.

## Diagnosis Steps

```bash
# 1. Read the persisted file
 cat ~/.config/Hermes/translucency.json

# 2. Is the desktop app actually running? Which is the MAIN process?
 pgrep -f "release/linux-unpacked/Hermes"          # all Electron procs
 # main = the proc whose cmdline has NO "--type=" flag:
 for p in $(pgrep -f "release/linux-unpacked/Hermes"); do
   args=$(tr '\0' ' ' < /proc/$p/cmdline); case "$args" in *--type=*) ;; *) echo "MAIN $p";; esac; done

# 3. Confirm what the window actually looks like — do not assume.
 DISPLAY=:0 gnome-screenshot -f /tmp/shot.png   # then analyze the image
```

Always **verify with a screenshot** that the window is/ isn't actually
transparent before declaring the cause. "The JSON says 29" is a hypothesis;
the rendered window is the evidence. On Linux the native fade is a no-op, so
the JSON value alone may not even be the visible cause.

## The Fix That Sticks (procedure)

A one-shot edit of the JSON is NOT sufficient — the app re-writes the value
on quit and on the next cold launch. The durable fix is **a file guard**:

1. **Stop the desktop app** (kill the Electron MAIN pid; SIGKILL the whole
   `pgrep -f "release/linux-unpacked/Hermes"` set to be safe). Do NOT stop the
gateway for this — they are separate processes. See the Hard Invariant about
not killing the gateway from inside itself.
2. **Zero the file**: write `{ intensity: 0, fade: 0, mode: "clear",
   material: "titlebar", scope: "sidebar" }` to `translucency.json`.
3. **Relaunch the desktop app** with the correct GUI env (a headless shell
   has no display — the relaunch must carry `DISPLAY`, `XAUTHORITY`, and
   `DBUS_SESSION_BUS_ADDRESS`):
   ```bash
   DISPLAY=:0 /usr/libexec/deepin/application-manager/debFix.sh \
     /home/raka/.local/bin/hermes desktop --skip-build
   ```
   (Deepin launches the DDE app through `debFix.sh`; on other desktops just run
   `hermes desktop` with the display env. `--skip-build` reuses the
   prebuilt binary at `apps/desktop/release/linux-unpacked/Hermes`.)
4. **Run a file guard** that re-zeros `translucency.json` the instant anything
   rewrites it (see `scripts/translucency-guard.py` in this skill dir). Launch
   it in the background (`nohup … &`) so it outlives the session. Log each
   interception.
5. **Verify**: `cat translucency.json` shows `intensity: 0`; the guard log
   shows any 29 rewrites were forced back; a fresh screenshot shows the
   window fully opaque.

## Making the Guard Persistent (optional, user preference)

The `/tmp` guard dies with the machine. To persist across reboots, install it
as a **user systemd service** instead of a `/tmp` process. Use the
`systemd-headless-service` skill for the unit boilerplate; point `ExecStart`
at a copied `translucency-guard.py`, add `After=graphical-session.target`
and `Wants=` for the desktop app. Offer this to the user — do not assume.

## Pitfalls

- **Never claim the fix worked after only editing the JSON.** The app
cold-launches by RE-READING the file and the renderer book then mirrors it
back. Confirm with (a) the guard log showing a rewrite was intercepted and
(b) a screenshot showing an opaque window.
- **Editing the file while the app runs does not change the live window.**
   Main only re-applies translucency on (a) cold launch, or (b) a live IPC
   change from the renderer. A running window keeps its in-memory
   `translucencyState` until restarted. So: kill → zero file → relaunch.
- **Relaunching headless fails with "Missing X server or $DISPLAY".** Always
   set `DISPLAY`/`XAUTHORITY`/`DBUS_SESSION_BUS_ADDRESS` for GUI relaunches
   from a non-GUI shell.
- **Two source-of-truth stores** — the JSON (main) and the localStorage book
   (renderer). If you only fix the JSON and the renderer book still holds the
   stale value, it comes back on the next launch. The guard neutralizes the
   file side; the localStorage book side is the renderer's — in practice the
   guard wins the race, but understand that a *clean* user action (sliding the
   Tint to 0 in Settings on a Mac/Windows machine) is the proper source fix.
- **On Linux the lever is a documented no-op** — `setOpacity` does nothing on
   X11, so you may not even be seeing the window faded *because of* this file
   on a pure-Linux box. If a screenshot shows the window is already opaque but
   the user still reports "transparency", suspect a different cause (a CSS
   `--user-bubble-*` or glass-surface var, or a compositing setting) before
   writing more to `translucency.json`.
- **Do not stop the gateway to fix the desktop.** They are separate processes.
   Killing the gateway from inside the gateway is blocked (SIGTERM propagates
to this process). Restart the gateway only with `hermes gateway restart` from
   an outside shell.
