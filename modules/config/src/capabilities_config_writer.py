"""Config writer capability — load / save / detect / normalize / dumps.

Thin AES capability wrapping the shared config kernel. The config agent
(``agent_config_orchestrator``) is the only caller; no I/O outside the
injected protocol.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.contract_config_protocol import IConfigProtocol
from modules.shared.src.taxonomy_common_vo import (
    ConfigData,
    ConfigFormat,
    ConfigTuple,
)
from modules.shared.src.utility_config_engine import (
    detect_format,
    load_file,
    save_file,
)
from modules.shared.src.utility_jsonc_parser import strip_jsonc_comments
from modules.shared.src.utility_toml_write import write_toml


# ─── Block 1: Class Definition & Constructor ──────────────
class ConfigWriter(IConfigProtocol):
    """Load / detect / save capability (single-execute dispatcher)."""

    # ─── Block 2: Protocol Method Implementation ──────────────
    def execute(
        self,
        op: str,
        path: Path,
        payload: dict | None = None,
    ) -> ConfigTuple | bool | ConfigFormat:
        """Dispatcher for load/save/detect_format operations."""
        if op == "load":
            return self.load_file(path)
        if op == "save":
            body = payload or {}
            fmt = body.get("fmt")
            if fmt is not None:
                fmt = ConfigFormat(fmt)
            return self.save_file(path, ConfigData(body.get("data", {})), fmt)
        if op == "detect_format":
            return self.detect_format(path)
        raise ValueError(f"ConfigWriter does not support op {op!r}")

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
