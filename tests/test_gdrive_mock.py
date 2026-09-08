"""Unit test: MockDriveClient untuk backup/restore tanpa network (P5-P2)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools/backup"))

from contract_backup_gateway_protocol import IBackupGateway


class MockDriveClient(IBackupGateway):
    """In-memory mock gateway untuk testing."""

    def __init__(self):
        self.store = {}

    def upload(self, local_path, remote_name=""):
        data = local_path.read_bytes()
        self.store[remote_name or local_path.name] = data
        return {"name": remote_name or local_path.name, "size": len(data)}

    def download(self, query_or_id, destination):
        if query_or_id not in self.store:
            raise FileNotFoundError(query_or_id)
        destination.write_bytes(self.store[query_or_id])
        return destination

    def list(self, prefix=""):
        return [{"name": k} for k in self.store if k.startswith(prefix)]


def test_mock_roundtrip():
    import tempfile
    client = MockDriveClient()
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "backup.tar.gz"
        src.write_bytes(b"test-archive-data")
        client.upload(src)
        dest = Path(d) / "restored.tar.gz"
        client.download("backup.tar.gz", dest)
        assert dest.read_bytes() == b"test-archive-data", "roundtrip failed"
    assert len(client.list()) == 1


if __name__ == "__main__":
    test_mock_roundtrip()
    print("test_gdrive_mock.py: ALL PASSED")
