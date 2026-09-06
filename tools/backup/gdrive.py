#!/usr/bin/env python3
"""
Google Drive Backup & Restore Helper for agents-arwaky
Uses Google Workspace MCP credentials to upload/download/list backup archives.
"""

import sys
import os
import json
import io
from pathlib import Path

DEFAULT_FOLDER_NAME = "Agents-Arwaky-Backups"

def get_credentials():
    data_dir = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    creds_dir = Path(data_dir) / "google-workspace-mcp" / "credentials"
    user_email = os.environ.get("USER_GOOGLE_EMAIL", "arwaky90@gmail.com")
    
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

    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
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
            with open(cred_file, "w", encoding="utf-8") as f:
                json.dump(cdata, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to refresh token: {e}", file=sys.stderr)
    return creds

def get_drive_service():
    from googleapiclient.discovery import build
    import httplib2
    import google_auth_httplib2
    creds = get_credentials()
    http = httplib2.Http(timeout=60)
    http.redirect_codes = http.redirect_codes - {308}
    auth_http = google_auth_httplib2.AuthorizedHttp(creds, http=http)
    return build("drive", "v3", http=auth_http)

def get_or_create_folder(service, folder_name=DEFAULT_FOLDER_NAME):
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    res = service.files().list(q=query, spaces="drive", fields="files(id, name)").execute()
    files = res.get("files", [])
    if files:
        return files[0]["id"]
        
    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder"
    }
    folder = service.files().create(body=metadata, fields="id").execute()
    return folder.get("id")

def cmd_upload(local_path, folder_name=DEFAULT_FOLDER_NAME):
    path = Path(local_path).resolve()
    if not path.exists():
        print(f"Error: Local file not found: {path}", file=sys.stderr)
        sys.exit(1)

    service = get_drive_service()
    folder_id = get_or_create_folder(service, folder_name)

    from googleapiclient.http import MediaFileUpload
    media = MediaFileUpload(str(path), mimetype="application/gzip", resumable=True)
    metadata = {
        "name": path.name,
        "parents": [folder_id]
    }
    
    file_obj = service.files().create(
        body=metadata,
        media_body=media,
        fields="id, name, webViewLink, size"
    ).execute()

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

    # Check if query_or_id is a file ID (Google Drive IDs are usually ~33-44 alphanum with - and _)
    if len(query_or_id) > 25 and "/" not in query_or_id and "." not in query_or_id:
        try:
            meta = service.files().get(fileId=query_or_id, fields="id, name").execute()
            if meta:
                file_id = meta["id"]
                target_name = meta["name"]
        except Exception:
            pass

    if not file_id:
        # Search by file name in folder
        folder_id = get_or_create_folder(service, folder_name)
        q = f"'{folder_id}' in parents and name contains '{query_or_id}' and trashed = false"
        res = service.files().list(q=q, orderBy="createdTime desc", fields="files(id, name)").execute()
        files = res.get("files", [])
        if not files:
            # Fallback: search anywhere in Drive
            q_any = f"name contains '{query_or_id}' and trashed = false"
            res = service.files().list(q=q_any, orderBy="createdTime desc", fields="files(id, name)").execute()
            files = res.get("files", [])

        if not files:
            print(f"Error: No backup archive found in Google Drive matching '{query_or_id}'", file=sys.stderr)
            sys.exit(1)
        file_id = files[0]["id"]
        target_name = files[0]["name"]

    dest = Path(destination_path)
    if dest.is_dir():
        dest = dest / target_name
    dest.parent.mkdir(parents=True, exist_ok=True)

    from googleapiclient.http import MediaIoBaseDownload
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(str(dest), "wb")
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()

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
    res = service.files().list(q=q, orderBy="createdTime desc", fields="files(id, name, size, createdTime, webViewLink)").execute()
    files = res.get("files", [])
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
            print("Usage: gdrive.py download <query_or_id> <destination_path> [folder_name]", file=sys.stderr)
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
