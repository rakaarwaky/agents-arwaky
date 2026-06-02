"""
Agent: Server bootstrap manager — resolves config from infrastructure
for consumption by surface layer via DI.
"""

import os

from contract import ServerBootstrapManagerAggregate
from infrastructure.config_file_loader import get_config, get_project_root
from taxonomy import ConfigPath, ConfigValue, DirectoryPath, FilePath, ObjectName


class ServerBootstrapManager(ServerBootstrapManagerAggregate):
    """Resolves configuration values for server startup."""

    _contract_name: ObjectName = ObjectName("ServerBootstrapManager")

    @staticmethod
    def get_project_root() -> FilePath:
        """Returns the root directory of the project."""
        return FilePath(str(get_project_root()))

    def to_request_dict(self) -> dict:
        """BlenderOpsIO: serialize bootstrap state."""
        return {
            "log_file": str(self.resolve_log_file()),
        }

    def get(self, path: ConfigPath, default: ConfigValue = None) -> ConfigValue:
        """Retrieve config value by dot-notation path."""
        return get_config(path, default)

    @staticmethod
    def resolve_log_file() -> FilePath:
        """Resolve and return full log file path."""
        project_root = str(get_project_root())
        log_dir_rel = str(get_config(ConfigPath("server.log_dir"), "log"))
        log_dir: DirectoryPath = DirectoryPath(os.path.join(project_root, log_dir_rel))
        os.makedirs(log_dir, exist_ok=True)
        log_file = str(get_config(ConfigPath("server.log_file"), "blender_run.log"))
        return FilePath(os.path.join(log_dir, log_file))

    @staticmethod
    def resolve_transport_config() -> tuple[str, str, str]:
        """Resolve transport, host, port configuration."""
        transport = str(
            os.environ.get(
                "MCP_TRANSPORT",
                get_config(ConfigPath("server.transport"), "stdio"),
            )
        )
        host = str(
            os.environ.get(
                "MCP_HOST",
                get_config(ConfigPath("server.host"), "127.0.0.1"),
            )
        )
        port_str = str(
            os.environ.get(
                "MCP_PORT",
                str(get_config(ConfigPath("server.port"), 8000)),
            )
        )
        return transport, host, port_str
