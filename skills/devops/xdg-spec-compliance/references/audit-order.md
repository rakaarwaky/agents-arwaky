# Audit order (cheapest signal first)

Run in order; each check narrows the suspect set before the next one
costs more.

**Goal:** locate every path resolution, the LOG/state bug, and the
write-vs-read split before theorizing about permissions.

## 1. Grep every resolved path

```bash
grep -rn -E 'XDG_|expanduser|Path\.home|/home/|\.local/share|\.config/' \
  --include='*.py' --include='*.sh' .
```

Find every resolved path and every bypass of the base dirs.

## 2. Check the LOG/state location specifically

Logs belong in `$XDG_STATE_HOME` (`.local/state`), not DATA or CACHE.
Projects that get this right are usually already competent; the
remaining bugs are permission/precedence ones.

## 3. Check who WRITES and who READS each constant

```bash
for n in DEFAULT_OUTPUT DEFAULT_CACHE; do grep -rln $n pkg; done
```

Provisioned-but-never-written directories make the permission question
moot — say so instead of theorizing.

## 4. Reproduce before claiming

Relative/tilde env values and mkdir umask inheritance are invisible to
reading alone:

```bash
XDG_DATA_HOME=rel/dir XDG_CONFIG_HOME='~/' python -c 'from pkg.provisioner import ...'
```

Then `git status --porcelain` to see what got dumped in the repo.
Clean up any junk the probe created and re-check `git status` is
clean.

## Completion

- The grep list, the LOG/state finding, and the write/read split are
  recorded.
- The repro ran, the repo is clean again, and no claim rests on
  reading alone.
