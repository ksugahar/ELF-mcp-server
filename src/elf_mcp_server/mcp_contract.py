"""Explicit MCP metadata and runtime composition contract."""
from __future__ import annotations

import json
import sys
from typing import Any, Iterable

from mcp.types import ToolAnnotations

from .tool_definitions import TOOL_CONTRACTS


SCHEMA = "elf.mcp-server-contract.v5"
_CLIENT_HISTORY_LIMIT = 8
_CLIENT_FIELD_LIMIT = 256


def _bounded_client_field(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)[:_CLIENT_FIELD_LIMIT]


def _capture_current_client(low_level: Any, server_name: str, version: str) -> None:
    """Capture initialize clientInfo on the first request after the handshake."""
    try:
        session = low_level.request_context.session
    except LookupError:
        return
    if getattr(session, "_caeai_client_info_captured", False):
        return
    params = getattr(session, "client_params", None)
    client_info = getattr(params, "clientInfo", None)
    if client_info is None:
        return

    snapshot = {
        "name": _bounded_client_field(getattr(client_info, "name", None)),
        "title": _bounded_client_field(getattr(client_info, "title", None)),
        "version": _bounded_client_field(getattr(client_info, "version", None)),
    }
    session._caeai_client_info_captured = True
    state = low_level._caeai_client_connection_state
    state["connection_count"] += 1
    state["latest"] = snapshot
    state["recent"] = (state["recent"] + [snapshot])[-_CLIENT_HISTORY_LIMIT:]
    print(
        f"[{server_name}] {version} client connected: "
        f"{json.dumps(snapshot, ensure_ascii=False)}; "
        "no product process was launched or modified",
        file=sys.stderr,
        flush=True,
    )


def _install_client_info_capture(mcp: Any, server_name: str, version: str) -> bool:
    """Install bounded, process-local clientInfo capture without product effects."""
    low_level = getattr(mcp, "_mcp_server", None)
    if low_level is None or getattr(low_level, "_caeai_client_info_capture", False):
        return False
    low_level._caeai_client_connection_state = {
        "connection_count": 0,
        "latest": None,
        "recent": [],
    }
    for request_type, previous in tuple(low_level.request_handlers.items()):
        async def _capture_then_handle(request: Any, _previous: Any = previous) -> Any:
            _capture_current_client(low_level, server_name, version)
            return await _previous(request)

        low_level.request_handlers[request_type] = _capture_then_handle
    low_level._caeai_client_info_capture = True
    return True


def get_client_connection_state(mcp: Any) -> dict[str, Any]:
    """Return a detached copy of bounded client connection metadata."""
    low_level = getattr(mcp, "_mcp_server", None)
    state = getattr(low_level, "_caeai_client_connection_state", None) or {}
    latest = state.get("latest")
    return {
        "connection_count": int(state.get("connection_count", 0)),
        "latest": dict(latest) if isinstance(latest, dict) else None,
        "recent": [dict(item) for item in state.get("recent", []) if isinstance(item, dict)],
    }


def apply_tool_contract(
    mcp: Any,
    *,
    server_name: str,
    version: str,
    tool_prefix: str = "",
    set_server_metadata: bool = True,
) -> dict[str, int]:
    """Apply and verify the explicit registry against the runtime surface."""
    tools = getattr(getattr(mcp, "_tool_manager", None), "_tools", {})
    selected = {name: tool for name, tool in tools.items() if not tool_prefix or name.startswith(tool_prefix)}
    contracts = {
        name: contract
        for name, contract in TOOL_CONTRACTS.items()
        if not tool_prefix or name.startswith(tool_prefix)
    }
    missing = sorted(set(selected) - set(contracts))
    stale = sorted(set(contracts) - set(selected))
    if missing or stale:
        raise RuntimeError(
            "explicit tool-contract registry mismatch: "
            f"missing={missing!r}, stale={stale!r}"
        )

    for name, tool in selected.items():
        contract = contracts[name]
        tool.title = contract.title
        tool.annotations = ToolAnnotations(
            readOnlyHint=contract.read_only,
            destructiveHint=contract.destructive,
            idempotentHint=contract.idempotent,
            openWorldHint=contract.open_world,
        )
        meta = dict(getattr(tool, "meta", None) or {})
        meta["elf.contract"] = SCHEMA
        if contract.read_only:
            meta["elf.classification"] = (
                "read-only-external" if contract.open_world else "read-only-local"
            )
        else:
            meta["elf.classification"] = "local-product-execution"
        tool.meta = meta

    low_level = getattr(mcp, "_mcp_server", None)
    if set_server_metadata and low_level is not None:
        low_level.version = version
        if not getattr(low_level, "instructions", None):
            low_level.instructions = (
                f"Use {server_name} for public guidance and guarded user-local product execution. "
                "Call detect and case_check before product_run; keep raw results local."
            )
    installed = _install_client_info_capture(mcp, server_name, version)
    return {
        "tools": len(selected),
        "explicit_contracts": len(contracts),
        "client_info_capture_installed": int(installed),
    }


def build_runtime_contract(capability_packs: Iterable[str], session_policy: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "runtime_core": "FastMCP over stdio",
        "capability_packs": list(capability_packs),
        "resource_layer": "static guidance exposed through stable MCP Resources",
        "skill_layer": "separate workflow skills",
        "explicit_tool_annotations": True,
        "semantic_output_models": True,
        "client_connection_visibility": {
            "initialize_identity": "server name, version, and instructions",
            "capture_point": "first post-initialize request",
            "captured_fields": ["name", "title", "version"],
            "process_local_history_limit": _CLIENT_HISTORY_LIMIT,
            "client_info_notice_logged": True,
            "product_session_side_effect": False,
        },
        "archive_extraction_policy": "public runtime does not extract untrusted archives",
        "session_policy": session_policy,
        "protocol_smoke": "initialize + tools/list + resources/list/read + prompts/list/get + representative calls",
    }
