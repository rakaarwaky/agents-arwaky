# Gists + Cleaning an Over-Tracked Backup Repo

## 10. Gists

**With gh:**

```bash
gh gist create script.py --public --desc "Useful script"
gh gist list
```

**With curl:**

```bash
# Create a gist
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/gists \
  -d '{
    "description": "Useful script",
    "public": true,
    "files": {
      "script.py": {"content": "print(\"hello\")"}
    }
  }'

# List your gists
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/gists \
  | python -c "
import sys, json
for g in json.load(sys.stdin):
    files = ', '.join(g['files'].keys())
    print(f\"  {g['id']}  {g['description'] or '(no desc)':40}  {files}\")"
```

## 11. Cleaning an Over-Tracked / "Dirty" Backup Repo

A repo that was copied/restored from a backup (or that glob-committed everything) often shows thousands of "modified" files that are not real changes. Before `git rm`-ing anything, **diagnose first** — most of the noise is harmless.

### Step 1 — Separate real changes from mode-bit noise

A backup restore frequently flips the executable bit (`100644 ↔ 100755`) on every file, which git reports as a modification even though **content is identical**. Confirm before doing anything destructive:

```bash
# Count mode-only vs content vs typechange in the working tree
git diff --raw | awk '{print $5}' | cut -c1 | sort | uniq -c
#   mode-only (chmod) -> 'M' with old!=new mode, same sha
#   content           -> 'M' with sha change
#   typechange        -> 'T' (symlink<->file)
```

If the vast majority are mode-only (e.g. 2473 of 2500, **zero content changes**), fix it with one safe config flag — do NOT edit 2500 files:

```bash
git config core.fileMode false      # local repo only; collapses all mode-bit noise
git status --short | wc -l          # re-measure — should drop dramatically
```

> **Why:** `core.fileMode false` tells git to ignore the executable bit, so all those false positives vanish from `git status` without touching a single file. Set it **per-repo** (`git config`, not `--global`) unless you want it everywhere.

### Step 2 — Classify the real remaining changes

With the noise gone, bucket every remaining entry into three classes:

- **JUNK** — runtime/cache/auto-generated: `*.pid`, `gateway_state.json`, `cron/ticker_*`, `*.bundled_manifest`, `*.usage.json`, `checkpoints/store/*`, embedded runtimes (`node/`), `*.db`/`*.snapshot` when not intentional backups, loose dotfiles (`.restart_last_processed.json`, `.update_exit_code`).
- **SECRET** — anything with credentials: `.env`, `auth.json`, `*/auth.json`, `nous_auth.json`, `shared/nous_auth.json`. **Never commit these.**
- **KEEP** — real config & content: `config.yaml`, `memories/MEMORY.md`, skills (`SKILL.md`), scripts, your own `.db.snapshot` backups you intentionally keep.

### Step 3 — Ignore + untrack (keep files on disk)

Add the JUNK + SECRET patterns to `.gitignore`, then **untrack** already-committed junk so it's removed from git tracking but stays on disk:

```bash
# 1. Append to .gitignore (runtime, caches, AND secrets)
cat >> .gitignore <<'EOF'
# Secrets — never commit raw credentials
auth.json
profiles/*/auth.json
shared/nous_auth.json
.env
profiles/*/.env
# Runtime state / caches / auto-generated
.curator_backups/
checkpoints/
node/
cron/ticker_heartbeat
cron/ticker_last_success
profiles/*/cron/ticker_heartbeat
profiles/*/cron/ticker_last_success
*.bak*
state/gateway.heartbeat
EOF

# 2. Untrack the now-ignored files (deletes from index, leaves on disk)
git rm -r --cached --quiet $(git ls-files | grep -E 'secret|junk|cache|pattern') 
#    (build the list from your JUNK+SECRET buckets; never glob blindly)

# 3. Add the real new files + updated .gitignore, then commit
git add .gitignore <real-new-files>
git commit -m "chore: untrack runtime junk + secrets, keep real config/skills"
```

**Key rules:**
- Use `git rm --cached` (NOT plain `git rm`) so files survive on disk.
- Don't build the untrack list with a blind `*` — enumerate your classified buckets.
- Set a local git identity if the repo has none: `git config user.name ... && git config user.email ...` (avoids `Author identity unknown`).
- If you keep `*.snapshot` database dumps as **intentional** backups, exclude them from the JUNK glob (the original `.gitignore` may already allow them).

### Step 4 — Verify cleanliness

```bash
git status --short | wc -l                 # expect 0 after commit
git check-ignore node/ .env shared/nous_auth.json   # should list each
git ls-files | grep -iE 'auth\.json|\.env$|nous_auth' || echo "no secrets tracked"  # expect "no secrets tracked"
```

> **PITFALL — repo-specific do-not-touch:** When cleaning the Hermes agent's own repo (`~/.hermes`), **never touch `hermes-agent/`** — it is managed by the Nous team and is intentionally git-ignored. Leave it untouched even if a cleanup pass would otherwise sweep it.

> **PITFALL — secrets in history:** Untracking stops *future* commits, but anything already pushed still contains the secret in old history. If the repo is/was public or shared, rotate the credential and purge history with `git filter-repo` (force-push required). Decide with the user before doing this.
