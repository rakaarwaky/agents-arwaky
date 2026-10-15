"""Doctor-domain constants — toolchain binaries the environment check probes (taxonomy layer)."""

#: Toolchain binaries every host must provide; a miss is a hard diagnostic failure.
REQUIRED: tuple[str, ...] = ("git", "jq", "curl", "python3")

#: Toolchain binaries that are reported when present and skipped when absent.
OPTIONAL: tuple[str, ...] = ("cargo", "uv", "node", "npm", "bun", "pnpm", "rustc")


__all__ = [
    "OPTIONAL",
    "REQUIRED",
]
