"""9router / OmniRoute credential migration capability.

Pure, unit-tested functions that read OmniRoute's live ``provider_connections``
(strictly read-only), decrypt its stored credentials, map each connection into
9router's provider-connection payload shape, plan the import, and execute it
against 9router's live SQLite database (daemon stopped first, restarted after).

Write transport (justified in the phase-3 report):

* Preferred: 9router admin HTTP API (``http://127.0.0.1:20128/api/providers``,
  ``/api/provider-nodes``). Rejected here because the route is session-cookie
  gated and validates ``name`` plus ``apiKey`` per row, so every OAuth
  connection without a working key is rejected outright with HTTP 400 — no
  headless, transactional path to import all 60 connections reliably.
* Chosen: direct SQLite UPSERT into ``~/.9router/db/data.sqlite`` with the
  9router daemon stopped first (via the phase-1 systemd manager that owns the
  unit) and restarted afterward, with health re-verified on port 20128. This
  is atomic, dedupe-safe (``ON CONFLICT(id)``), matches the column shape the
  app itself writes, and never touches OmniRoute.

OmniRoute is opened strictly read-only (``mode=ro`` URI). No decrypted
plaintext credential is ever logged or printed.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from modules.shared.src.daemon.contract_daemon_import_protocol import (
    I9routerImportOmnirouteProtocol,
)
from modules.shared.src.daemon.taxonomy_daemon_constant import (
    ENC_PREFIX,
    NINEROUTER_DB_DEFAULT,
    OMNI_TO_NINE_FIELDS,
    OMNIROUTE_DB_DEFAULT,
    SKIPPED_FIELDS,
    STORAGE_ENCRYPTION_KEY_ENV,
)
from modules.shared.src.daemon.taxonomy_daemon_vo import ExitCode

__all__ = [
    "NINEROUTER_DB_DEFAULT",
    "OMNIROUTE_DB_DEFAULT",
    "NineRouterImportOmniroute",
    "decrypt_field",
    "derive_key",
    "execute_plan",
    "load_omniroute_connections",
    "load_omniroute_nodes",
    "load_secret",
    "looks_encrypted",
    "map_connection_to_9router",
    "mask_secret",
    "plan_import",
    "run_import",
    "write_via_api",
    "write_via_sqlite",
]

# ─── Block 1: Class Definition & Constructor ──────────────


class NineRouterImportOmniroute(I9routerImportOmnirouteProtocol):
    """OmniRoute -> 9router credential import capability.

    Implements ``I9routerImportOmnirouteProtocol``. The daemon stop/start
    callables are injected by the composition root so this capability never
    imports a sibling capability module (AES201).
    """

    def __init__(
        self,
        stop_fn: Callable[[], None] | None = None,
        start_fn: Callable[[], None] | None = None,
    ) -> None:
        """Store the daemon lifecycle callables injected by the container."""
        self._stop_fn = stop_fn
        self._start_fn = start_fn

    # ─── Block 2: Protocol Trait Implementation ──────────────

    def run_import(
        self,
        argv: list[str],
        stop_fn: Callable[[], None] | None = None,
        start_fn: Callable[[], None] | None = None,
    ) -> ExitCode:
        """CLI entry for ``9router import-omniroute [--dry-run] [--provider X]``."""
        stop = stop_fn or self._stop_fn or (lambda: None)
        start = start_fn or self._start_fn or (lambda: None)
        return ExitCode(_run_import(argv, stop, start))

# ─── Block 3: Constructors, Std Traits, Helpers ───────────


def run_import(
    argv: list[str],
    stop_fn: Callable[[], None] | None = None,
    start_fn: Callable[[], None] | None = None,
) -> int:
    """Module-level convenience entry (used by the CLI surface).

    Wraps :class:`NineRouterImportOmniroute`; when *stop_fn*/*start_fn* are
    omitted the capability falls back to no-op no-ops so the dry-run path
    still works without a daemon.
    """
    stop = stop_fn or (lambda: None)
    start = start_fn or (lambda: None)
    return NineRouterImportOmniroute(stop, start).run_import(argv)


def _static_salt() -> bytes:
    return b"omniroute-field-encryption-v1"


def _legacy_dynamic_salt(secret: str) -> bytes:
    return hashlib.sha256(secret.encode("utf-8")).digest()[:16]


def derive_key(secret: str, salt: bytes) -> bytes:
    """Derive the 32-byte AES-256-GCM key (scrypt, Node scryptSync defaults)."""
    return hashlib.scrypt(
        secret.encode("utf-8"), salt=salt, dklen=32, n=16384, r=8, p=1
    )


def looks_encrypted(value: str | None) -> bool:
    """True when *value* carries the ``enc:v1:`` ciphertext prefix."""
    return isinstance(value, str) and value.startswith(ENC_PREFIX)


def _decrypt_with_key_pyca(ciphertext: str, key: bytes) -> str | None:
    """Decrypt one ``enc:v1:`` value with pyca/cryptography AESGCM."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except Exception:
        return None
    body = ciphertext[len(ENC_PREFIX) :]
    iv_hex, encrypted_hex, tag_hex = body.split(":")
    try:
        return AESGCM(key).decrypt(
            bytes.fromhex(iv_hex),
            bytes.fromhex(encrypted_hex) + bytes.fromhex(tag_hex),
            None,
        ).decode("utf-8")
    except Exception:
        return None


def _decrypt_with_key_pycryptodome(ciphertext: str, key: bytes) -> str | None:
    """Decrypt one ``enc:v1:`` value with pycryptodome AES-GCM."""
    try:
        from Crypto.Cipher import AES as _AES
    except Exception:
        return None
    body = ciphertext[len(ENC_PREFIX) :]
    iv_hex, encrypted_hex, tag_hex = body.split(":")
    iv = bytes.fromhex(iv_hex)
    encrypted = bytes.fromhex(encrypted_hex)
    tag = bytes.fromhex(tag_hex)
    try:
        cipher = _AES.new(key, _AES.MODE_GCM, nonce=iv, mac_len=len(tag))
        return cipher.decrypt_and_verify(encrypted, tag).decode("utf-8")
    except Exception:
        return None


def _decrypt_with_key(ciphertext: str, key: bytes) -> str | None:
    """Decrypt one ``enc:v1:`` value with *key*; None on any failure."""
    try:

        pyca_available = True
    except Exception:
        pyca_available = False
    if pyca_available:
        return _decrypt_with_key_pyca(ciphertext, key)
    return _decrypt_with_key_pycryptodome(ciphertext, key)


def decrypt_field(ciphertext: str | None, secret: str | None) -> str | None:
    """Decrypt one encrypted field: static salt first, legacy dynamic salt second.

    Returns None for non-string/null input, non-encrypted passthrough values, and
    undecryptable ciphertexts (both derivations failed). Never raises.
    """
    if not looks_encrypted(ciphertext):
        return ciphertext
    if not secret:
        return None
    try:
        key = derive_key(secret, _static_salt())
    except Exception:
        return None
    plain = _decrypt_with_key(ciphertext, key)
    if plain is not None:
        return plain
    try:
        legacy_key = derive_key(secret, _legacy_dynamic_salt(secret))
    except Exception:
        return None
    return _decrypt_with_key(ciphertext, legacy_key)


def load_secret() -> str | None:
    """Resolve ``STORAGE_ENCRYPTION_KEY`` from env then ``~/.omniroute/.env``."""
    value = os.environ.get(STORAGE_ENCRYPTION_KEY_ENV)
    if value:
        return value.strip().strip('"').strip("'")
    env_file = Path.home() / ".omniroute" / ".env"
    try:
        for line in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
            trimmed = line.strip()
            if not trimmed.startswith("STORAGE_ENCRYPTION_KEY="):
                continue
            value = trimmed.split("=", 1)[1].strip().strip('"').strip("'")
            if value:
                return value
    except OSError:
        return None
    return None


# --------------------------------------------------------------------------- #
# Masking (never prints plaintext credentials)
# --------------------------------------------------------------------------- #

def mask_secret(value: str | None) -> str:
    """Mask a secret for logging: ``sk-...abcd`` or ``<empty>``/``<null>``."""
    if value is None:
        return "<null>"
    value = str(value)
    if looks_encrypted(value):
        return f"<encrypted len={len(value)}>"
    if not value:
        return "<empty>"
    if value.startswith("sk-"):
        return f"{value[:3]}{'*' * max(0, len(value) - 7)}...{value[-4:]}"
    if len(value) > 8:
        return f"{value[:4]}{'*' * max(0, len(value) - 8)}...{value[-4:]}"
    return "<masked>"


# --------------------------------------------------------------------------- #
# OmniRoute read (strictly read-only)
# --------------------------------------------------------------------------- #

def _open_ro(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def load_omniroute_connections(
    db_path: str = OMNIROUTE_DB_DEFAULT, secret: str | None = None
) -> list[dict[str, Any]]:
    """Read every provider_connections row from OmniRoute, read-only.

    Decrypts ``api_key`` / ``access_token`` / ``refresh_token`` / ``id_token``.
    Returns a list of dicts keyed by OmniRoute column names.
    When *secret* is omitted it is resolved via :func:`load_secret`.
    """
    if secret is None:
        secret = load_secret()
    conn = _open_ro(db_path)
    try:
        rows = conn.execute(
            "SELECT id, provider, auth_type, name, email, priority, is_active, "
            "api_key, access_token, refresh_token, id_token, expires_at, "
            "token_expires_at, scope, project_id, display_name, default_model, "
            "token_type, expires_in, provider_specific_data, \"group\", "
            "max_concurrent, global_priority, created_at, updated_at "
            "FROM provider_connections ORDER BY priority, id"
        ).fetchall()
    finally:
        conn.close()

    out: list[dict[str, Any]] = []
    for row in rows:
        d = dict(row)
        failed: list[str] = []
        api_key_raw = d.get("api_key")
        if isinstance(api_key_raw, str):
            api_key_raw = api_key_raw.strip() or None
        d["api_key"] = decrypt_field(api_key_raw, secret)
        if looks_encrypted(api_key_raw) and d["api_key"] is None:
            failed.append("api_key")
        for field in ("access_token", "refresh_token", "id_token"):
            raw = d.get(field)
            if isinstance(raw, str):
                raw = raw.strip() or None
            d[field] = decrypt_field(raw, secret)
            if looks_encrypted(raw) and d[field] is None:
                failed.append(field)
        if failed:
            d["_decrypt_failed_fields"] = failed
        out.append(d)
    return out


def load_omniroute_nodes(db_path: str = OMNIROUTE_DB_DEFAULT) -> list[dict[str, Any]]:
    """Read every provider_nodes row from OmniRoute, read-only."""
    conn = _open_ro(db_path)
    try:
        rows = conn.execute(
            "SELECT id, type, name, prefix, api_type, base_url, chat_path, "
            "models_path, custom_headers_json FROM provider_nodes ORDER BY id"
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


# --------------------------------------------------------------------------- #
# Mapping OmniRoute -> 9router payload shape
# --------------------------------------------------------------------------- #

def _canonical_id(value: str) -> str:
    """Normalize a connection id (strip whitespace)."""
    return (value or "").strip()


def _node_for_provider(provider: str, nodes: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Find the OmniRoute provider_nodes row that matches *provider*.

    Match on exact id, then on prefix derived from the provider alias.
    """
    for node in nodes:
        if node.get("id") == provider:
            return node
    prefix = re.sub(r"[^a-z0-9]+", "-", provider.lower()).strip("-")
    for node in nodes:
        if (node.get("prefix") or "").lower() == prefix:
            return node
    return None


def _node_data_9router(node: dict[str, Any] | None) -> dict[str, Any] | None:
    """Convert an OmniRoute provider_nodes row into 9router's node ``data``."""
    if not node:
        return None
    data: dict[str, Any] = {
        "baseUrl": node.get("base_url") or "",
        "apiType": node.get("api_type") or "chat",
        "chatPath": node.get("chat_path") or "/v1/chat/completions",
        "modelsPath": node.get("models_path") or "/v1/models",
        "prefix": node.get("prefix") or "",
        "name": node.get("name") or node.get("prefix") or "",
    }
    headers_raw = node.get("custom_headers_json")
    if headers_raw not in (None, ""):
        try:
            parsed = (
                headers_raw if isinstance(headers_raw, dict) else json.loads(headers_raw)
            )
        except Exception:
            parsed = {"raw": headers_raw}
        data["headers"] = parsed
    return data


def map_connection_to_9router(
    conn: dict[str, Any],
    nodes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Map one decrypted OmniRoute connection into 9router's insert payload.

    Returns a dict with top-level columns (id, provider, authType, name, email,
    priority, isActive, createdAt, updatedAt) plus a ``data`` dict holding the
    camelCase credential payload and a ``skipped_fields`` list. The 9router
    column names mirror what the app's own ``createProviderConnection`` writes.
    """
    nodes = nodes or []
    node = _node_for_provider(str(conn.get("provider", "")), nodes)
    data: dict[str, Any] = {}

    # api_key -> data.apiKey (decrypted)
    api_key = conn.get("api_key")
    if api_key not in (None, ""):
        data["apiKey"] = api_key

    # camelCase mirror of the remaining secret/credential columns.
    for omni_col, nine_key in OMNI_TO_NINE_FIELDS.items():
        if omni_col == "api_key":
            continue
        value = conn.get(omni_col)
        if value not in (None, ""):
            data[nine_key] = value

    # provider_specific_data passthrough (already a dict when JSON-text).
    psd = conn.get("provider_specific_data")
    if psd not in (None, ""):
        if isinstance(psd, str):
            try:
                psd = json.loads(psd)
            except Exception:
                psd = {"raw": psd}
        if isinstance(psd, dict):
            data["providerSpecificData"] = psd

    skipped: list[str] = []
    for field in SKIPPED_FIELDS:
        if field in conn and conn[field] not in (None, ""):
            skipped.append(field)

    node_data = _node_data_9router(node)
    if node_data:
        data["providerNode"] = node_data

    created_at = conn.get("created_at") or ""
    updated_at = conn.get("updated_at") or ""

    return {
        "id": _canonical_id(conn.get("id", "")),
        "provider": conn.get("provider") or "",
        "authType": (conn.get("auth_type") or "apikey"),
        "name": conn.get("name") or conn.get("provider") or "",
        "email": conn.get("email") or "",
        "priority": conn.get("priority") or 1,
        "isActive": 1 if conn.get("is_active") in (1, "1", True) else 0,
        "data": data,
        "createdAt": created_at,
        "updatedAt": updated_at,
        "skipped_fields": skipped,
    }


# --------------------------------------------------------------------------- #
# Planning (no writes)
# --------------------------------------------------------------------------- #

def plan_import(
    connections: list[dict[str, Any]],
    nodes: list[dict[str, Any]] | None = None,
    existing_ids: set[str] | None = None,
    existing_keys: set[str] | None = None,
    providers: list[str] | None = None,
) -> dict[str, Any]:
    """Build an import plan without writing anything.

    ``existing_ids`` / ``existing_keys`` are 9router-side state (ids already in
    providerConnections, apiKey values already present). Connections whose id
    already exists are ``skipped-existing``; duplicates of an apiKey already in
    9router are also ``skipped-existing``. ``--provider`` filters by provider
    string.
    """
    nodes = nodes or []
    providers_set = set(providers) if providers else None
    existing_ids = existing_ids or set()
    existing_keys = existing_keys or set()

    plan: dict[str, Any] = {
        "total": 0,
        "apikey": 0,
        "oauth": 0,
        "decrypt_failures": 0,
        "would_import": 0,
        "would_skip_existing": 0,
        "would_skip_provider_filter": 0,
        "items": [],
        "skipped_fields_report": {},
    }

    seen_keys: set[str] = set()
    for conn in connections:
        provider = conn.get("provider") or ""
        if providers_set and provider not in providers_set:
            plan["would_skip_provider_filter"] += 1
            continue
        plan["total"] += 1
        if conn.get("auth_type") == "oauth":
            plan["oauth"] += 1
        else:
            plan["apikey"] += 1

        item = map_connection_to_9router(conn, nodes)
        # decrypt failure: an encrypted field that could not be decrypted.
        # Reported as decrypt_failure (row still listed in items; written
        # without secrets) but still counted toward would_import per spec.
        failed_fields = conn.get("_decrypt_failed_fields") or [
            f
            for f in ("api_key", "access_token", "refresh_token", "id_token")
            if looks_encrypted(conn.get(f)) and conn.get(f) is None
        ]
        if failed_fields:
            item["decrypt_failure"] = True
            item["failed_fields"] = failed_fields
            plan["decrypt_failures"] += 1

        # dedupe by existing id
        if item["id"] in existing_ids:
            item["skip"] = "existing-id"
            plan["would_skip_existing"] += 1
            plan["items"].append(item)
            continue
        # dedupe by apiKey business key (apikey connections)
        api_key = item["data"].get("apiKey")
        if api_key and (api_key in existing_keys or api_key in seen_keys):
            item["skip"] = "existing-key"
            plan["would_skip_existing"] += 1
            plan["items"].append(item)
            continue
        if api_key:
            seen_keys.add(api_key)

        plan["would_import"] += 1
        plan["items"].append(item)

        for field in item["skipped_fields"]:
            plan["skipped_fields_report"].setdefault(provider, set()).add(field)

    plan["skipped_fields_report"] = {
        k: sorted(v) for k, v in plan["skipped_fields_report"].items()
    }
    return plan


# --------------------------------------------------------------------------- #
# Execution (writes to 9router SQLite only)
# --------------------------------------------------------------------------- #

def _ninerouter_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _existing_api_keys(db_path: str) -> set[str]:
    """Return existing apiKey values present in 9router's providerConnections."""
    keys: set[str] = set()
    conn = _ninerouter_conn(db_path)
    try:
        for row in conn.execute("SELECT data FROM providerConnections"):
            try:
                data = json.loads(row["data"] or "{}")
            except Exception:
                data = {}
            if isinstance(data, dict) and data.get("apiKey"):
                keys.add(str(data["apiKey"]))
    finally:
        conn.close()
    return keys


def write_via_sqlite(
    items: list[dict[str, Any]],
    db_path: str = NINEROUTER_DB_DEFAULT,
    dry_run: bool = False,
) -> dict[str, int]:
    """UPSERT mapped items into 9router's providerConnections (+ nodes).

    Returns counts: imported, skipped_existing, errors.
    """
    counts = {"imported": 0, "skipped_existing": 0, "errors": 0}
    seen_keys: set[str] = set(_existing_api_keys(db_path))

    if dry_run:
        for item in items:
            if item.get("skip"):
                counts["skipped_existing"] += 1
            else:
                counts["imported"] += 1
        return counts

    conn = _ninerouter_conn(db_path)
    try:
        for item in items:
            if item.get("skip"):
                counts["skipped_existing"] += 1
                continue
            try:
                data = json.dumps(item["data"], ensure_ascii=False)
                with conn:
                    conn.execute(
                        "INSERT INTO providerConnections(id, provider, authType, name, email, "
                        "priority, isActive, data, createdAt, updatedAt) "
                        "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                        "ON CONFLICT(id) DO UPDATE SET "
                        "provider=excluded.provider, authType=excluded.authType, "
                        "name=excluded.name, email=excluded.email, "
                        "priority=excluded.priority, isActive=excluded.isActive, "
                        "data=excluded.data, updatedAt=excluded.updatedAt",
                        [
                            item["id"],
                            item["provider"],
                            item["authType"],
                            item["name"],
                            item["email"],
                            item["priority"],
                            item["isActive"],
                            data,
                            item["createdAt"],
                            item["updatedAt"],
                        ],
                    )
                    api_key = item["data"].get("apiKey")
                    if api_key:
                        seen_keys.add(api_key)
                counts["imported"] += 1
            except Exception:
                counts["errors"] += 1
    finally:
        conn.close()
    return counts


def write_via_api(
    items: list[dict[str, Any]],
    base_url: str = "http://127.0.0.1:20128",
    dry_run: bool = False,
) -> dict[str, int]:
    """Last-resort write transport through the 9router admin HTTP API.

    Requires an authenticated session cookie (login via /api/auth/login).
    Not the default path; kept for when SQLite is unavailable.
    """
    counts = {"imported": 0, "skipped_existing": 0, "errors": 0}
    if dry_run:
        for item in items:
            counts["imported" if not item.get("skip") else "skipped_existing"] += 1
        return counts
    try:
        import urllib.error as _uerror
        import urllib.parse as _parse
        import urllib.request as _request
    except Exception:
        counts["errors"] += len(items)
        return counts

    cookie = ""
    try:
        req = _request.Request(
            base_url.rstrip("/") + "/api/auth/login",
            data=_parse.urlencode({"password": os.environ.get("INITIAL_PASSWORD", "")}).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with _request.urlopen(req, timeout=10) as r:
            for h in r.headers.get_all("set-cookie") or []:
                if h.lower().startswith("auth_token="):
                    cookie = h.split(";")[0].split("=", 1)[1]
    except Exception:
        counts["errors"] += len(items)
        return counts

    opener = _request.build_opener()
    for item in items:
        if item.get("skip"):
            counts["skipped_existing"] += 1
            continue
        try:
            payload = {
                "provider": item["provider"],
                "authType": item["authType"],
                "name": item["name"],
                "email": item["email"],
                "priority": item["priority"],
                "isActive": bool(item["isActive"]),
                "apiKey": item["data"].get("apiKey", ""),
                "providerSpecificData": item["data"],
                "allowOverwrite": True,
            }
            data = json.dumps(payload).encode()
            req = _request.Request(
                base_url.rstrip("/") + "/api/providers",
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Cookie": f"auth_token={cookie}",
                },
                method="POST",
            )
            with opener.open(req, timeout=20) as r:
                if r.status in (200, 201):
                    counts["imported"] += 1
                else:
                    counts["errors"] += 1
        except _uerror.HTTPError as e:
            if e.code == 409:
                counts["skipped_existing"] += 1
            else:
                counts["errors"] += 1
        except Exception:
            counts["errors"] += 1
    return counts


def execute_plan(
    plan: dict[str, Any],
    db_path: str = NINEROUTER_DB_DEFAULT,
    dry_run: bool = False,
) -> dict[str, int]:
    """Execute an import *plan* against 9router's SQLite database.

    Thin wrapper around :func:`write_via_sqlite` so callers can plan then
    execute with a single entry point.
    """
    return write_via_sqlite(plan["items"], db_path=db_path, dry_run=dry_run)


# --------------------------------------------------------------------------- #
# CLI entry
# --------------------------------------------------------------------------- #

def _run_import(
    argv: list[str],
    stop_fn: Callable[[], None],
    start_fn: Callable[[], None],
) -> int:
    """CLI entry for ``9router import-omniroute [--dry-run] [--provider X]``."""
    dry_run = False
    providers: list[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--dry-run",):
            dry_run = True
        elif arg in ("--provider",):
            if i + 1 < len(argv):
                providers.append(argv[i + 1])
                i += 1
            else:
                print("--provider requires a value", file=sys.stderr)
                return 2
        elif arg in ("-h", "--help", "help"):
            print(
                "Usage: aa 9router import-omniroute [--dry-run] [--provider <name>]...\n"
                "Migrate OmniRoute provider credentials into 9router (read-only on OmniRoute)."
            )
            return 0
        else:
            print(f"Unknown argument: {arg}", file=sys.stderr)
            return 2
        i += 1

    connections = load_omniroute_connections()
    nodes = load_omniroute_nodes()
    plan = plan_import(connections, nodes, providers=providers or None)

    print("9router import-omniroute plan")
    print(f"  source:        {OMNIROUTE_DB_DEFAULT} (read-only)")
    print(f"  destination:   {NINEROUTER_DB_DEFAULT}")
    print(f"  dry-run:       {dry_run}")
    print(f"  total:         {plan['total']}")
    print(f"    apikey:      {plan['apikey']}")
    print(f"    oauth:       {plan['oauth']}")
    print(f"    decrypt-failures: {plan['decrypt_failures']}")
    print(f"    would-import: {plan['would_import']}")
    print(f"    would-skip-existing: {plan['would_skip_existing']}")
    if plan["would_skip_provider_filter"]:
        print(f"    skipped-by-provider-filter: {plan['would_skip_provider_filter']}")
    if plan["skipped_fields_report"]:
        print("  skipped-fields-by-provider:")
        for provider, fields in sorted(plan["skipped_fields_report"].items()):
            print(f"    {provider}: {', '.join(fields)}")

    if dry_run:
        print("  (no writes performed)")
        return 0

    # SQLite write requires the daemon stopped first (per transport decision),
    # then restarted and health re-verified.
    print("  stopping 9router daemon before SQLite write...")
    stop_fn()
    counts = write_via_sqlite(plan["items"], dry_run=False)
    print("  starting 9router daemon after SQLite write...")
    start_fn()
    print(f"  imported:      {counts['imported']}")
    print(f"  skipped:       {counts['skipped_existing']}")
    print(f"  errors:        {counts['errors']}")
    if counts["errors"]:
        return 1
    return 0
