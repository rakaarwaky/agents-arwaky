#!/usr/bin/env python3
"""
Google Drive Backup & Restore Helper for agents-arwaky
Uses Google Workspace MCP credentials to upload/download/list backup archives.
"""

import io
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "lib"))
from paths import repo_root
ROOT = repo_root()
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import data_home  # type: ignore[import-not-found]

DEFAULT_FOLDER_NAME = "Agents-Arwaky-Backups"

def get_credentials():
    creds_dir = data_home() / "google-workspace-mcp" / "credentials"
    user_email = os.environ.get("USER_GOOGLE_EMAIL", "")

    cred_file = creds_dir / f"{user_email}.json"
    if not cred_file.exists():
        # Fallback to any json file in credentials directory
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

    from google.auth.exceptions import RefreshError  # type: ignore
    from google.auth.transport.requests import Request  # type: ignore
    from google.oauth2.credentials import Credentials  # type: ignore
    creds = Credentials(
        token=cdata.get("token"),
        refresh_token=cdata.get("refresh_token"),
        token_uri=cdata.get("token_uri"),
        client_id=cdata.get("client_id"),
        client_secret=cdata.get("client_secret"),
        scopes=cdata.get("scopes")
    )
    if not creds.valid or creds.expired:
        try:
            creds.refresh(Request())
            cdata["token"] = creds.token
            # Atomic write: temp file + rename prevents partial-write corruption
            tmp = cred_file.with_suffix(cred_file.suffix + ".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(cdata, f, indent=2)
            os.replace(tmp, cred_file)
        except (RefreshError, OSError, TypeError) as e:
            print(f"Warning: Failed to refresh token: {e}", file=sys.stderr)
    return creds

def get_drive_service():
    import google_auth_httplib2  # type: ignore
    import httplib2  # type: ignore
    from googleapiclient.discovery import build  # type: ignore
    creds = get_credentials()
    http = httplib2.Http(timeout=60)
    http.redirect_codes = http.redirect_codes - {308}
    auth_http = google_auth_httplib2.AuthorizedHttp(creds, http=http)
    return build("drive", "v3", http=auth_http)


def _is_transient(err) -> bool:
    """Return True if the error is retryable (transient), False for permanent
    failures."""
    # Timeout / connection errors
    if isinstance(err, (ConnectionError, TimeoutError)):
        return True
    # Google API HttpError: retry only 429/500/502/503
    try:
        from googleapiclient.errors import HttpError  # type: ignore
        if isinstance(err, HttpError):
            status = getattr(err, "resp", None)
            code = (
                status.status
                if status is not None
                else getattr(err, "status_code", None)
            )
            return code in (429, 500, 502, 503)  # 401/403/404 = permanen, jangan retry
    except ImportError:
        pass
    return False


def retry_api(func, max_retries=4, delay=1):
    """Retry a Google API call (shared utility) — transient errors only."""
    from retry import retry_api as _shared_retry  # type: ignore
    return _shared_retry(
        func, max_retries=max_retries, delay=delay, is_transient=_is_transient
    )

def escape_drive_query(value: str) -> str:
    """Escape values for Google Drive query language (single quotes & backslashes)."""
    return value.replace("\\", "\\\\").replace("'", "\\'")


def list_all_files(service, query, fields, max_pages: int = 50):
    """List files with pagination (P1: handle multiple pages, bounded)."""
    all_files = []
    page_token = None
    pages = 0
    while True:
        pages += 1
        if pages > max_pages:
            print(
                f"  \u26a0 Warning: stopped after {max_pages} pages "
                f"(pagination bound).",
                file=sys.stderr,
            )
            break
        params = {"q": query, "fields": fields, "pageSize": 100}
        if page_token:
            params["pageToken"] = page_token
        res = retry_api(lambda p=params: service.files().list(**p).execute())
        all_files.extend(res.get("files", []))
        page_token = res.get("nextPageToken")
        if not page_token:
            break
    return all_files


def get_or_create_folder(service, folder_name=DEFAULT_FOLDER_NAME):
    query = (
        f"name = '{escape_drive_query(folder_name)}' "
        "and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    )
    res = retry_api(
        lambda: service.files().list(
            q=query, spaces="drive", fields="files(id, name)"
        ).execute()
    )
    files = res.get("files", [])
    if files:
        return files[0]["id"]

    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder"
    }
    folder = retry_api(
        lambda: service.files().create(body=metadata, fields="id").execute()
    )
    return folder.get("id")

def cmd_upload(local_path, folder_name=DEFAULT_FOLDER_NAME):
    path = Path(local_path).resolve()
    if not path.exists():
        print(f"Error: Local file not found: {path}", file=sys.stderr)
        sys.exit(1)

    service = get_drive_service()
    folder_id = get_or_create_folder(service, folder_name)

    from googleapiclient.http import MediaFileUpload  # type: ignore
    media = MediaFileUpload(str(path), mimetype="application/gzip", resumable=True)
    metadata = {
        "name": path.name,
        "parents": [folder_id]
    }

    file_obj = retry_api(lambda: service.files().create(
        body=metadata,
        media_body=media,
        fields="id, name, webViewLink, size"
    ).execute())

    print(json.dumps({
        "status": "success",
        "file_id": file_obj.get("id"),
        "name": file_obj.get("name"),
        "web_view_link": file_obj.get("webViewLink"),
        "size": file_obj.get("size")
    }, indent=2))

def cmd_download(query_or_id, destination_path, folder_name=DEFAULT_FOLDER_NAME):
    service = get_drive_service()

    file_id = None
    target_name = query_or_id

    # Check if query_or_id is a file ID (Google Drive IDs are usually
    # ~33-44 alphanum with - and _)
    if len(query_or_id) > 25 and "/" not in query_or_id and "." not in query_or_id:
        from googleapiclient.errors import HttpError  # type: ignore

        try:
            meta = retry_api(
                lambda: service.files().get(
                    fileId=query_or_id, fields="id, name"
                ).execute()
            )
            if meta:
                file_id = meta["id"]
                target_name = meta["name"]
        except (HttpError, OSError, ValueError):
            pass

    if not file_id:
        # Search by file name in folder
        folder_id = get_or_create_folder(service, folder_name)
        q = (
            f"'{folder_id}' in parents and name contains "
            f"'{escape_drive_query(query_or_id)}' and trashed = false"
        )
        res = retry_api(
            lambda: service.files().list(
                q=q, orderBy="createdTime desc", fields="files(id, name)"
            ).execute()
        )
        files = res.get("files", [])
        if not files:
            # Fallback: search anywhere in Drive
            q_any = (
                f"name contains '{escape_drive_query(query_or_id)}' "
                "and trashed = false"
            )
            res = retry_api(
                lambda: service.files().list(
                    q=q_any, orderBy="createdTime desc", fields="files(id, name)"
                ).execute()
            )
            files = res.get("files", [])

        if not files:
            print(
                f"Error: No backup archive found in Google Drive matching "
                f"'{query_or_id}'",
                file=sys.stderr,
            )
            sys.exit(1)
        file_id = files[0]["id"]
        target_name = files[0]["name"]

    dest = Path(destination_path)
    if dest.is_dir():
        dest = dest / target_name
    dest.parent.mkdir(parents=True, exist_ok=True)

    from googleapiclient.http import MediaIoBaseDownload  # type: ignore
    import random as _random
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(str(dest), "wb")
    try:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            # R2: retry transient errors during chunk download
            last_err = None
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
                        wait = min(1.0 * (2 ** attempt) + _random.uniform(0, 1), 10)
                        time.sleep(wait)
            if last_err is not None:
                raise last_err
    finally:
        fh.close()
    print(json.dumps({
        "status": "success",
        "file_id": file_id,
        "name": target_name,
        "local_path": str(dest)
    }, indent=2))

def cmd_list(folder_name=DEFAULT_FOLDER_NAME):
    service = get_drive_service()
    folder_id = get_or_create_folder(service, folder_name)
    q = f"'{folder_id}' in parents and trashed = false"
    # Use list_all_files (pagination-aware, bounded) (P3)
    files = list_all_files(
        service, q, "files(id, name, size, createdTime, webViewLink)"
    )
    print(json.dumps(files, indent=2))

def main():
    if len(sys.argv) < 2:
        print("Usage: gdrive.py <upload|download|list> [args...]", file=sys.stderr)
        sys.exit(1)

    action = sys.argv[1]
    if action == "upload":
        if len(sys.argv) < 3:
            print("Usage: gdrive.py upload <local_path> [folder_name]", file=sys.stderr)
            sys.exit(1)
        folder = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_FOLDER_NAME
        cmd_upload(sys.argv[2], folder)
    elif action == "download":
        if len(sys.argv) < 4:
            print(
                "Usage: gdrive.py download <query_or_id> <destination_path> "
                "[folder_name]",
                file=sys.stderr,
            )
            sys.exit(1)
        folder = sys.argv[4] if len(sys.argv) > 4 else DEFAULT_FOLDER_NAME
        cmd_download(sys.argv[2], sys.argv[3], folder)
    elif action == "list":
        folder = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_FOLDER_NAME
        cmd_list(folder)
    else:
        print(f"Unknown action: {action}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
