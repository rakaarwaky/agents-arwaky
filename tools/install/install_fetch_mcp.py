#!/usr/bin/env python3
"""Installer fetch-mcp — zcaceres/fetch-mcp (TypeScript, bun).

Spesifik: script build memakai bun (`bun build src/index.ts src/cli.ts
--outdir dist`), jadi wajib `bun install` + `bun run build` (ada dua lockfile,
bun.lock & pnpm-lock.yaml; yang dipakai build adalah bun). Hasil:
  - dist/index.js -> MCP server (fetch-mcp, mcp-fetch)
  - dist/cli.js   -> CLI mode (html/markdown/readable/txt/json/youtube/--help/...)
Launcher mendispatch CLI vs MCP berdasarkan argumen pertama.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import bin_home, data_home, ensure_bin_home, warn_if_bin_not_on_path  # type: ignore[import-not-found]

SRC = ROOT / "vendor/fetch-mcp"
APP_DIR = data_home() / "fetch-mcp"

# Argumen pertama yang berarti "CLI mode" -> jalankan dist/cli.js, selain itu MCP.
CLI_ARGS = {"html", "markdown", "readable", "txt", "json", "youtube", "--help", "-h", "--version", "-v"}

IGNORES = shutil.ignore_patterns(
    "node_modules", ".git", "__pycache__", "target", "*.egg-info",
    ".venv", "venv", "*.tsbuildinfo",
)


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    if not (SRC / "package.json").exists():
        print("Error: fetch-mcp source not found (submodule belum di-init).", file=sys.stderr)
        return 1

    print(f">>> Installing fetch-mcp into {APP_DIR}...")
    if APP_DIR.exists():
        shutil.rmtree(APP_DIR)
    shutil.copytree(SRC, APP_DIR, ignore=IGNORES)

    run(["bun", "install"], APP_DIR)
    run(["bun", "run", "build"], APP_DIR)

    index_js = APP_DIR / "dist/index.js"
    cli_js = APP_DIR / "dist/cli.js"
    if not index_js.exists() or not cli_js.exists():
        print(f"  Error: hasil build tidak lengkap ({index_js}, {cli_js})", file=sys.stderr)
        return 1

    ensure_bin_home()
    content = (
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        f'index_js = r"{index_js}"\n'
        f'cli_js = r"{cli_js}"\n'
        "cli = " + repr(sorted(CLI_ARGS)) + "\n"
        "script = cli_js if (len(sys.argv) > 1 and sys.argv[1] in cli) else index_js\n"
        'env = os.environ.copy()\n'
        'os.execvpe("node", ["node", script, *sys.argv[1:]], env)\n'
    )
    for name in ("fetch-mcp", "mcp-fetch"):
        launcher = bin_home() / name
        launcher.write_text(content, encoding="utf-8")
        launcher.chmod(0o755)
        print(f"  -> {launcher}")

    warn_if_bin_not_on_path()
    print(">>> Successfully installed fetch-mcp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
