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

2. Update changelog and version files:
   - If `git-cliff` is installed and `cliff.toml` exists, generate/prepend the changelog:
     ```shell
     if command -v git-cliff >/dev/null 2>&1; then
       git-cliff --unreleased --tag "$NEW_VERSION" --prepend CHANGELOG.md
     fi
     ```
   - Run the bump script at project-root `scripts/` — check for `scripts/bump.sh` or `scripts/bump.py`:

   ```shell
   if [ -f scripts/bump.sh ]; then
     bash scripts/bump.sh "$NEW_VERSION"
   elif [ -f scripts/bump.py ]; then
     python3 scripts/bump.py "$NEW_VERSION"
   else
     mkdir -p scripts
     cat > scripts/bump.sh <<'EOF'
   #!/usr/bin/env bash
   VERSION="$1"
   sed -i -E 's/^__RELEASE_VERSION__ = .*/__RELEASE_VERSION__ = "'"$VERSION"'"/' \
     pyproject.toml Cargo.toml 2>/dev/null || true
   if command -v git-cliff >/dev/null 2>&1 && [ -f cliff.toml ]; then
     git-cliff --unreleased --tag "$VERSION" --prepend CHANGELOG.md
   elif [ ! -f CHANGELOG.md ] || ! grep -q "## $VERSION" CHANGELOG.md; then
     echo -e "## $VERSION\n" | cat - CHANGELOG.md > CHANGELOG.tmp 2>/dev/null && mv CHANGELOG.tmp CHANGELOG.md || echo "## $VERSION" >> CHANGELOG.md
   fi
   for f in scripts pyproject.toml Cargo.toml CHANGELOG.md; do [ -e "$f" ] && git add -A "$f" || true; done
   git commit -m "release: bump to $VERSION"
   EOF
     chmod +x scripts/bump.sh
     bash scripts/bump.sh "$NEW_VERSION"
   fi
   ```