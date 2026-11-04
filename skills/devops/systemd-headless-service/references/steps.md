# The steps that actually matter

Run in order; each one has killed a first attempt.

**Goal:** the service stays up across crash and reboot, with the right process running behind the right port.

## 1. Find the real process name and port first

`ss -ltnp | grep <port>` and read the process. Do not assume the app
from the port number alone (e.g. port 7777 is the local AI gateway;
deleting the wrong one breaks the user's setup).

## 2. Inspect how it launches

Read the CLI entry (the binary, `cli.js`): does it read PORT/HOST from
env? Does it spawn a child server (`detached: true`) then `return`?
If the parent exits, systemd sees the service stop and the child may
be killed too.

## 3. Pass the headless/background flag

If the app has one (e.g. `omniroute --port 7777 --no-browser` under
systemd — no `--tray`, which backgrounds the main PID). Without a
headless path, a TTY-less parent often self-exits.

## 4. Set MemoryMax high enough

First boot frequently compiles native modules (e.g.
`better-sqlite3` via node-gyp) and boots a framework (Next.js),
spiking ~1.5GB. Use `MemoryMax=3G` to avoid the OOM killer wiping the
instance (and sometimes the shell) mid-build.

## 5. Wait long enough before checking

30–60s, not 5s. A fresh `next-server` + native build can take that
long before the port listens.

## 6. Linger

Confirm `loginctl show-user <user> | grep Linger=yes` so the user
service runs with no active login session. If `no`,
`sudo loginctl enable-linger <user>`.

## Completion

- All six steps are done for the target app, and step 1's port
  belongs to the app being backgrounded (checked, not assumed).
