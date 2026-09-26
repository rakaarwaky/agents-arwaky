"""Harness provider-adapter mechanics — provider-scoped verdicts + dispatch.

Mirrors ``utility_tool_mechanics`` for the harness feature: the helpers the
five ``capabilities_harness_*_adapter`` leaves share (≥2 consumers) so their
``IHarnessProtocol.execute`` bodies stay one line each.

A leaf owns exactly one provider: its paths, config format, env keys, and
custom-API flag (FRD § System Overview). The ops it can answer alone are the
provider-scoped verdicts the capabilities need before they write anything —
``supported`` (does this provider take part in the requested scope?) and
``satisfied`` (is its declared surface already in place?). The cross-cutting
connect / disconnect / provisioning runs stay in the three capabilities: one
MCP manifest, one credential resolution, one skill pack.

Taxonomy only (AES201 — the utility scope forbids contract/capabilities
imports), so the provider argument stays duck-typed.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_harness_vo import (
    ExitCode,
    UnsupportedHarnessError,
)

#: Provider-scoped ops a single leaf serves without the capability layer.
LEAF_OPS: tuple[str, ...] = ("supported", "satisfied")


def provider_supported(provider: object, flags: dict[str, bool] | None = None) -> bool:
    """True when *provider* takes part in the run described by *flags*.

    FR-HARNESS-001 edge case: a provider declaring neither MCP nor env is
    skipped with a report while every other target continues; a run scoped to
    one surface (``mcp_only`` / ``env_only``) needs that surface declared.
    """
    scopes = flags or {}
    supports_mcp = bool(getattr(provider, "supports_mcp", False))
    supports_env = bool(getattr(provider, "supports_env", False))
    if scopes.get("env_only"):
        return supports_env
    if scopes.get("mcp_only"):
        return supports_mcp
    return supports_mcp or supports_env


def provider_satisfied(provider: object) -> bool:
    """True when every config/env file *provider* declares already exists.

    Path-existence proxy for the wiring probe — the harness analogue of the
    tools-domain ``satisfied`` — so a repeat connect can report "already
    wired" without reading any config body. A provider that declares no
    surface at all reports unsatisfied.
    """
    mcp_targets = getattr(provider, "mcp_targets", None)
    mcp_config_file = getattr(provider, "mcp_config_file", None)
    env_files = getattr(provider, "env_files", None)
    if not (callable(mcp_targets) and callable(mcp_config_file) and callable(env_files)):
        return False
    files = [mcp_config_file(target_dir) for _, target_dir in mcp_targets()]
    files += list(env_files())
    return all(Path(f).is_file() for f in files)


def resolve_provider(units: dict[str, object], harness_id: str) -> object:
    """The provider spec registered for *harness_id*, else a typed error."""
    provider = units.get(harness_id)
    if provider is None:
        raise UnsupportedHarnessError(harness_id, tuple(units))
    return provider


def dispatch_provider_op(
    units: dict[str, object],
    op: str,
    targets: tuple[str, ...],
    flags: dict[str, bool] | None = None,
    *,
    label: str,
) -> ExitCode:
    """Dispatch one ``IHarnessProtocol.execute`` call against *units*.

    Shared body of every leaf adapter's ``execute``: resolve the provider for
    each target in *units*, then route ``supported`` / ``satisfied``. A
    non-zero ``ExitCode`` means "skip this provider" for the caller. An op
    outside :data:`LEAF_OPS` raises ``ValueError`` — the contract-breach style
    the three harness capabilities already use.
    """
    if op not in LEAF_OPS:
        raise ValueError(f"{label} does not handle op {op!r}")
    verdicts = []
    for harness_id in targets:
        provider = resolve_provider(units, harness_id)
        if op == "supported":
            verdicts.append(provider_supported(provider, flags))
        else:
            verdicts.append(provider_satisfied(provider))
    return ExitCode(1 if not all(verdicts) else 0)


__all__ = [
    "LEAF_OPS",
    "dispatch_provider_op",
    "provider_satisfied",
    "provider_supported",
    "resolve_provider",
]
