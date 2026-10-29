# Step 0 — version bump

Working directory: project root.

1. Compute `NEW_VERSION`. `YYYY.M.D` is the current UTC date; `N` follows the
   calver rule (`YYYY.M.D.N`, no zero padding, `N` starts at 1 each UTC day).

   ```shell
   last=$(gh release list --limit 1 --json tagName --jq '.[0].tagName')   # e.g. 2026.10.24.1
   today=$(date -u +%Y.%-m.%-d)                                     # no zero padding
   # N = 1 if last tag is from a different day, else last N + 1
   N=1
   if [ -n "$last" ]; then
     last_date="${last%.*}"
     last_N="${last##*.}"
     [ "$last_date" = "$today" ] && N=$((last_N + 1))
   fi
   NEW_VERSION="$today.$N"
   ```

2. Use the bump script at project-root `scripts/` — check for `scripts/bump.sh`
   or `scripts/bump.py`:

   ```shell
   if [ -f scripts/bump.sh ]; then
     bash scripts/bump.sh "$NEW_VERSION"
   elif [ -f scripts/bump.py ]; then
     python3 scripts/bump.py "$NEW_VERSION"
   else
     mkdir -p scripts
     cat > scripts/bump.sh <<'EOF'
   #!/usr/bin/env bash
   sed -i -E 's/^__RELEASE_VERSION__ = .*/__RELEASE_VERSION__ = "'"$1"'"/' \
     pyproject.toml Cargo.toml 2>/dev/null || true
   echo "## $1" >> CHANGELOG.md
   for f in scripts pyproject.toml Cargo.toml CHANGELOG.md; do [ -e "$f" ] && git add -A "$f" || true; done
   git commit -m "release: bump to $1"
   EOF
     chmod +x scripts/bump.sh
     bash scripts/bump.sh "$NEW_VERSION"
   fi
   ```