"""Google Drive backup gateway — port of backup/gdrive.py."""
from __future__ import annotations

import io
import json
import os
import random
import time
from pathlib import Path

from modules.shared.src.backup.contract_backup_protocol import IBackupGateway
from modules.shared.src.backup.taxonomy_backup_vo import BackupResult, RestoreResult
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.retry.utility_retry import retry_api
from modules.shared.src.xdg.utility_xdg_paths import data_home

DEFAULT_FOLDER_NAME = "Agents-Arwaky-Backups"


def _is_transient(err: Exception) -> bool:
    """True for retryable (transient) errors only."""
    if isinstance(err, (ConnectionError, TimeoutError)):
        return True
    try:
        from googleapiclient.errors import HttpError  # type: ignore[import-not-found]
        if isinstance(err, HttpError):
            status = getattr(err, "resp", None)
            code = status.status if status is not None else getattr(err, "status_code", None)
            return code in (429, 500, 502, 503)
    except ImportError:
        pass
    return False


def get_credentials():
    """Load / refresh google-workspace-mcp credentials (XDG data dir)."""
    creds_dir = data_home() / "google-workspace-mcp" / "credentials"
    user_email = os.environ.get("USER_GOOGLE_EMAIL", "")
    cred_file = creds_dir / f"{user_email}.json"
    if not cred_file.exists():
        candidates = list(creds_dir.glob("*.json"))
        candidates = [c for c in candidates if c.name != "oauth_states.json"]
        if candidates:
            cred_file = candidates[0]
        else:
            raise FileNotFoundError(
                f"Google Workspace credentials not found in {creds_dir}. "
                "Please run: aa install workspace or workspace-mcp setup"
            )
    with open(cred_file, "r", encoding="utf-8") as f:
        cdata = json.load(f)
    from google.auth.exceptions import RefreshError  # type: ignore[import-not-found]
    from google.auth.transport.requests import Request  # type: ignore[import-not-found]
    from google.oauth2.credentials import Credentials  # type: ignore[import-not-found]
    creds = Credentials(
        token=cdata.get("token"),
        refresh_token=cdata.get("refresh_token"),
        token_uri=cdata.get("token_uri"),
        client_id=cdata.get("client_id"),
        client_secret=cdata.get("client_secret"),
        scopes=cdata.get("scopes"),
    )
    if not creds.valid or creds.expired:
        try:
            creds.refresh(Request())
            cdata["token"] = creds.token
            tmp = cred_file.with_suffix(cred_file.suffix + ".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(cdata, f, indent=2)
            os.replace(tmp, cred_file)
        except (RefreshError, OSError, TypeError) as e:
            print(f"Warning: Failed to refresh token: {e}", file=__import__("sys").stderr)
    return creds


def get_drive_service():
    import google_auth_httplib2  # type: ignore[import-not-found]
    import httplib2  # type: ignore[import-not-found]
    from googleapiclient.discovery import build  # type: ignore[import-not-found]
    creds = get_credentials()
    http = httplib2.Http(timeout=60)
    http.redirect_codes = http.redirect_codes - {308}
    auth_http = google_auth_httplib2.AuthorizedHttp(creds, http=http)
    return build("drive", "v3", http=auth_http)


def escape_drive_query(value: str) -> str:
    """Escape values for Google Drive query language."""
    return value.replace("\\", "\\\\").replace("'", "\\'")


def list_all_files(service, query: str, fields: str, max_pages: int = 50) -> list:
    """List files with pagination (bounded)."""
    all_files: list = []
    page_token: str | None = None
    pages = 0
    while True:
        pages += 1
        if pages > max_pages:
            print(f"  \u26a0 Warning: stopped after {max_pages} pages (pagination bound).",
                  file=__import__("sys").stderr)
            break
        params: dict[str, object] = {"q": query, "fields": fields, "pageSize": 100}
        if page_token:
            params["pageToken"] = page_token
        res = retry_api(lambda p=params: service.files().list(**p).execute(),
                        is_transient=_is_transient)
        all_files.extend(res.get("files", []))
        page_token = res.get("nextPageToken")
        if not page_token:
            break
    return all_files


def get_or_create_folder(service, folder_name: str = DEFAULT_FOLDER_NAME) -> str:
    query = (
        f"name = '{escape_drive_query(folder_name)}' "
        "and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    )
    res = retry_api(
        lambda: service.files().list(q=query, spaces="drive", fields="files(id, name)").execute(),
        is_transient=_is_transient,
    )
    files = res.get("files", [])
    if files:
        return files[0]["id"]
    metadata = {"name": folder_name, "mimeType": "application/vnd.google-apps.folder"}
    folder = retry_api(
        lambda: service.files().create(body=metadata, fields="id").execute(),
        is_transient=_is_transient,
    )
    return folder.get("id")


class GdriveBackupGateway(IBackupGateway):
    """Upload / download backup archives via Google Drive.

    # Block 1: Configuration (folder, credentials)
    # Block 2: Backup (upload)
    # Block 3: Restore (download)
    """

    # -- Block 1: Configuration ---------------------------------------------------
    def __init__(self, folder_name: str = DEFAULT_FOLDER_NAME) -> None:
        self._folder_name = folder_name
        self._service = None

    def _get_service(self):
        if self._service is None:
            self._service = get_drive_service()
        return self._service

    # -- Block 2: Backup -------------------------------------------------------------
    def backup(self, tool: str, dest: str = "") -> BackupResult:
        """Upload a local archive named <tool>*.tar.gz to the Drive folder."""
        import sys
        store = data_home() / "backups"
        matches = sorted(store.glob(f"{tool}-*.tar.gz")) if store.exists() else []
        if not matches:
            return BackupResult(False, tool, "", False, "no local archive found")
        archive = matches[-1]
        service = self._get_service()
        folder_id = get_or_create_folder(service, self._folder_name)
        from googleapiclient.http import MediaFileUpload  # type: ignore[import-not-found]
        media = MediaFileUpload(str(archive), mimetype="application/gzip", resumable=True)
        metadata = {"name": archive.name, "parents": [folder_id]}
        file_obj = retry_api(lambda: service.files().create(
            body=metadata, media_body=media,
            fields="id, name, webViewLink, size",
        ).execute(), is_transient=_is_transient)
        print(json.dumps({
            "status": "success",
            "file_id": file_obj.get("id"),
            "name": file_obj.get("name"),
            "web_view_link": file_obj.get("webViewLink"),
            "size": file_obj.get("size"),
        }, indent=2))
        return BackupResult(True, tool, str(archive), True, "uploaded to Google Drive")

    # -- Block 3: Restore --------------------------------------------------------------
    def restore(self, tool: str, archive: Path) -> RestoreResult:
        """Download the newest Drive archive matching *tool* into *archive* path."""
        import sys
        service = self._get_service()
        folder_id = get_or_create_folder(service, self._folder_name)
        q = (f"'{folder_id}' in parents and name contains "
             f"'{escape_drive_query(tool)}' and trashed = false")
        res = retry_api(lambda: service.files().list(
            q=q, orderBy="createdTime desc", fields="files(id, name)",
        ).execute(), is_transient=_is_transient)
        files = res.get("files", [])
        if not files:
            return RestoreResult(False, tool, str(archive), "", "no Drive archive found")
        file_id = files[0]["id"]
        target_name = files[0]["name"]
        dest = Path(archive)
        if dest.is_dir():
            dest = dest / target_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        from googleapiclient.http import MediaIoBaseDownload  # type: ignore[import-not-found]
        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(str(dest), "wb")
        try:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                last_err: Exception | None = None
                for attempt in range(1, 5):
                    try:
                        _, done = downloader.next_chunk()
                        last_err = None
                        break
                    except Exception as exc:
                        last_err = exc
                        if not _is_transient(exc):
                            raise
                        if attempt < 4:
                            wait = min(1.0 * (2 ** attempt) + random.uniform(0, 1), 10)
                            time.sleep(wait)
                if last_err is not None:
                    raise last_err
        finally:
            fh.close()
        print(json.dumps({
            "status": "success",
            "file_id": file_id,
            "name": target_name,
            "local_path": str(dest),
        }, indent=2))
        return RestoreResult(True, tool, target_name, str(dest), "downloaded from Google Drive")
