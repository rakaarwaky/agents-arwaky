# Self-lint job (architecture enforcement)

Split from `SKILL.md` §1 (GitHub Actions workflow).

This is the differentiator: the repo lints **itself** with its own
architecture rules (AES 7-layer system). CI fails if the codebase violates
its own rules. The `self-lint` job runs two checks: zero violations on the
whole repo, and the AES rule engine still fires all 24 codes on the
intentional-violation fixture workspace (`workspaces-bad`) — the second
check catches a linter that silently stops detecting anything:

```bash
# 1. Whole-repo self-lint must be clean (exit code is authoritative;
#    the parsed count is only for the log line).
set -e
output=$(./target/release/lint-arwaky-cli check . 2>&1) || { echo "$output"; exit 1; }
violations=$(echo "$output" | grep -oP 'Total:\s*\K\d+' || echo "0")
echo "Violations: ${violations}"
[ "${violations}" = "0" ]

# 2. AES codes still fire on the bad workspace (≥24 unique AES codes).
codes=$(./target/release/lint-arwaky-cli scan workspaces-bad 2>&1 \
  | grep -oP "AES\d+" | sort -u | wc -l)
echo "Unique codes: ${codes:-0}"
[ "${codes:-0}" -ge 24 ]
```

Use `cargo build --release` (or `--bin lint-arwaky-cli`) before these
steps so the binary exists under `./target/release/`.