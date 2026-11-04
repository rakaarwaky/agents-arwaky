# Flatpak sandbox paths and CDP launch

**Goal:** you can pick paths the sandboxed browser actually reads and start a
genuinely first-in CDP debug session.

## Which paths the browser process can actually see

The sandbox does NOT bind host `/etc` or `~/.config` (outside `~/.var/app/...`):
`/etc/brave/policies/managed/*.json` and `--policy-directory=/home/<user>/.config/...`
silently load nothing (verify via `chrome://policy` over CDP — statuses come
back as errors/not-listed rather than an exception). Paths that ARE visible:
anything under `/tmp` or `~/.var/app/<APPID>/`. Probe without launching:
`flatpak run --command=ls <APPID> <path>`.

## Orphan instances hijack your debug launch

A live browser owns the user-data dir singleton, so a fresh
`flatpak run com.brave.Browser --remote-debugging-port=... --profile-directory=...`
just hands off to the running instance and exits: no port listens, no error,
and it looks like "flatpak breaks CDP". CDP works fine from the host
(127.0.0.1) once the launch is genuinely first-in. Before launching debug
sessions, check `flatpak ps` and probe the target dir's `SingletonSocket`;
killing the `flatpak run` wrapper does NOT kill the browser — clean up with
`flatpak kill <instance-id>`, and re-verify with `pgrep -f "[/]app/brave/brave"`
(`[/]` bracket so the pattern cannot match your own shell).

## pkill/pgrep self-match kills your own shell

`pkill -f "remote-debugging-port=9233"` issued from an agent shell matches the
shell's own command line (it contains that string) and SIGTERMs the command
mid-run. Always break the pattern with a bracket class: `pkill -f "92[3]3"`.

## Completion

- `chrome://policy` over CDP shows no statuses from host policy paths (expected
  under flatpak) — the sandbox-visible path you picked is the one being tested.
- The debug port listens on 127.0.0.1 and `/json/list` returns targets;
  `flatpak ps` shows the launch was first-in (no orphan handoff).
