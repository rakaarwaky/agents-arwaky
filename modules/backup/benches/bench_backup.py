"""Benchmarks for modules/backup — performance testing."""
from __future__ import annotations


def bench_gateway_init(benchmark):
    """BENCH-BACKUP-001: Benchmark TarBackupGateway initialization."""
    from modules.backup.src.capabilities_backup_tar import TarBackupGateway

    benchmark(TarBackupGateway)


def bench_orchestrator_init(benchmark):
    """BENCH-BACKUP-002: Benchmark BackupOrchestrator initialization."""
    from modules.backup.src.capabilities_backup_tar import TarBackupGateway
    from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator

    def _init():
        tar = TarBackupGateway()
        return BackupOrchestrator(tar, tar)

    benchmark(_init)


def bench_execute_help(benchmark):
    """BENCH-BACKUP-003: Benchmark execute('help')."""
    from modules.backup.src.capabilities_backup_tar import TarBackupGateway

    gateway = TarBackupGateway()
    benchmark(gateway.execute, "help")


def bench_container_creation(benchmark):
    """BENCH-BACKUP-004: Benchmark BackupContainer creation."""
    from modules.backup.src.root_backup_container import BackupContainer

    benchmark(BackupContainer)
