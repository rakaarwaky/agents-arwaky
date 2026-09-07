from __future__ import annotations

import hashlib
import tempfile
import zipfile
from pathlib import Path

from modules.plugin.src.capabilities_plugin_package import PluginPackageCapability
from modules.plugin.src.taxonomy_plugin_vo import (
    PluginActionName,
    PluginCachePath,
    PluginId,
    PluginInstallPath,
    PluginPackageRequestVO,
    PluginSha256,
    PluginSourceUrl,
)


def main() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        cache = root / "mpfb2.zip"
        install = root / "installed" / "mpfb2"
        with zipfile.ZipFile(cache, "w") as archive:
            archive.writestr("mpfb2/__init__.py", "bl_info = {}\n")
        request = PluginPackageRequestVO(
            plugin_id=PluginId("mpfb2"),
            source_url=PluginSourceUrl("https://example.invalid/mpfb2.zip"),
            sha256=PluginSha256(hashlib.sha256(cache.read_bytes()).hexdigest()),
            cache_path=PluginCachePath(str(cache)),
            install_path=PluginInstallPath(str(install)),
        )
        capability = PluginPackageCapability()
        verified = capability.execute(PluginActionName("verify_plugin"), request)
        assert verified.success and verified.message == "verified"
        installed = capability.execute(PluginActionName("install_plugin"), request)
        assert installed.success and (install / "__init__.py").exists()
        removed = capability.execute(PluginActionName("remove_plugin"), request)
        assert removed.success and not install.exists()
        print("plugin package lifecycle smoke test passed")


if __name__ == "__main__":
    main()
