#!/usr/bin/env python3
"""Hermes desktop translucency file guard.

Watches ~/.config/Hermes/translucency.json (the Electron userData path). On
ANY rewrite, immediately forces it back to the opaque state so a stale
intensity value can't be re-applied on the next cold launch or clean-quit
flush. Run in the background; it outlives the session that started it.

Usage:
    nohup python3 translucency-guard.py >/dev/null 2>&1 &

Edit PATH to match the user's real userData location (resolve $HERMES_HOME /
the Electron userData dir first). The log lands next to the script by default.
"""
import json
import os
import time
from pathlib import Path

# Resolve the desktop userData dir. Electron on Linux uses ~/.config/Hermes;
# on macOS/Windows it differs. Override via $HERMES_DESKTOP_USERDATA if needed.
def _find_translucency_path() -> Path:
    if os.environ.get("HERMES_DESKTOP_USERDATA"):
        return Path(os.environ["HERMES_DESKTOP_USERDATA"]) / "translucency.json"
    return Path.home() / ".config" / "Hermes" / "translucency.json"

PATH = _find_translucency_path()
# Opaque, off. Keep the other keys so a clean-quit flush from the app still
# sees a well-formed state (it diffs on all five keys).
FIXED = {"intensity": 0, "fade": 0, "mode": "clear", "material": "titlebar", "scope": "sidebar"}


def write_fixed() -> None:
    tmp = str(PATH) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(FIXED, f, indent=2)
    os.replace(tmp, PATH)


def main() -> None:
    logf = open(str(PATH) + ".guard.log", "a")

    def log(msg: str) -> None:
        logf.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        logf.flush()

    write_fixed()
    last = (os.stat(PATH).st_mtime, os.stat(PATH).st_size)
    log(f"guard started on {PATH}; initial state written")
    while True:
        try:
            st = os.stat(PATH)
            cur = (st.st_mtime, st.st_size)
            if cur != last:
                try:
                    now = json.load(open(PATH))
                except Exception:
                    now = {"intensity": "unknown"}
                if now.get("intensity") != 0:
                    write_fixed()
                    log(f"detected intensity={now.get('intensity')} -> rewrote to 0")
                last = os.stat(PATH).st_mtime and (os.stat(PATH).st_mtime, os.stat(PATH).st_size)
        except FileNotFoundError:
            write_fixed()
            log("file missing -> re-created at 0")
        except Exception as e:  # keep the guard alive through transient errors
            log(f"error: {e!r}")
        time.sleep(0.2)


if __name__ == "__main__":
    main()
