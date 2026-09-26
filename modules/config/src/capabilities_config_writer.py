"""Config writer capability — load / save / inspect / help.

Thin AES capability wrapping the shared config kernel. The config agent
(``agent_config_orchestrator``) is the only caller; no I/O outside the
injected protocol. Implements ``IConfigReaderProtocol`` exclusively — the
mutating operations live on ``ConfigModifier`` under its own seam.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.contract_config_protocol import IConfigReaderProtocol
from modules.shared.src.taxonomy_common_vo import (
    ConfigData,
    ConfigFormat,
    ConfigSnapshot,
    ConfigTuple,
    HelpText,
)
from modules.shared.src.utility_config_engine import (
    detect_format,
    list_mcp_servers,
    load_file,
    save_file,
)
from modules.shared.src.utility_jsonc_parser import strip_jsonc_comments
from modules.shared.src.utility_toml_write import write_toml


# ─── Block 1: Class Definition & Constructor ──────────────
class ConfigWriter(IConfigReaderProtocol):
    """Load / save / inspect / help capability."""

    def __init__(self, usage: HelpText | None = None) -> None:
        self._usage = usage if usage is not None else HelpText("")

    # ─── Block 2: Protocol Method Implementation ──────────────
    def load(self, path: Path) -> ConfigTuple:
        """Read *path*; returns ``(data, format)``."""
        return self.load_file(path)

    def save(
        self,
        path: Path,
        data: ConfigData,
        fmt: ConfigFormat | None = None,
    ) -> bool:
        """Write *data* to *path*, detecting the format when *fmt* is None."""
        return self.save_file(path, data, fmt)

    def inspect(self, path: Path) -> ConfigSnapshot:
        """Read-only snapshot: path, format, data, and server names."""
        data, fmt = self.load(path)
        return ConfigSnapshot({
            "path": str(path),
            "format": str(fmt),
            "data": dict(data),
            "servers": list(list_mcp_servers(path) or []),
        })

    def help(self) -> HelpText:
        """Return the usage text the agent injected."""
        return self._usage

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return "ConfigWriter()"

    def load_file(self, path: Path) -> ConfigTuple:
        """Load a config file and return ``(data, format)``."""
        data, fmt = load_file(path)
        return (ConfigData(data), ConfigFormat(fmt))

    def save_file(
        self,
        path: Path,
        data: ConfigData,
        fmt: ConfigFormat | None = None,
    ) -> bool:
        """Save *data* to *path*, detecting format when *fmt* is None."""
        if fmt is None:
            fmt = ConfigFormat(detect_format(path))
        return save_file(path, data, fmt)

    def detect_format(self, path: Path) -> ConfigFormat:
        """Detect the config format of *path* and wrap it as ``ConfigFormat``."""
        return ConfigFormat(detect_format(path))

    def normalize_jsonc(self, text: str) -> str:
        """Strip JSONC comments from *text*."""
        return strip_jsonc_comments(text)

    def dumps_toml(self, data) -> str:
        """Serialize *data* to a TOML string."""
        return write_toml(data)


__all__ = [
    "ConfigWriter",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ConfigData": ConfigData,
    "ConfigFormat": ConfigFormat,
    "ConfigWriter": ConfigWriter,
    "ConfigTuple": ConfigTuple,
}
