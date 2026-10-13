#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config/plugins/desarrollador-autonomo-health/__init__.py
Governed Hermes Plugin for Desarrollador Autónomo (Subfase 7A.2)

Provides:
1. Custom Tool `da_project_health`:
   - Read-only deterministic health inspection of the Desarrollador Autónomo workspace,
     configuration files, and governed MCP sandbox.
   - Strictly governed by Security Guard (`PLUGIN != PRIVILEGE ESCALATION`): any attempt to
     invoke non-read-only actions, blocked commands (`git push`, `format`, etc.), protected
     files (`config/security.yaml`, `RUN-CONTRACT.yaml`, `runner/`), or paths outside the
     workspace (`C:\\Windows`, `../`) is deterministically denied (`DENY`).
2. Lifecycle Hook `pre_tool_call`:
   - Enforces MCP server/tool allowlist (`TOOL_NOT_ALLOWED`) and canonical sandbox path
     confinement (`PATH_CONFINEMENT_VIOLATION`) before any `mcp__*` or plugin tool call executes.
"""

from __future__ import annotations

import json
import os
import re
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

PLUGIN_NAME = "desarrollador-autonomo-health"
PLUGIN_VERSION = "1.0.0"

WORKSPACE_ROOT = Path(r"C:\Users\Pc\Documents\Proyectos Tech\Desarrollador autonomo").resolve()
MCP_SANDBOX_ROOT = (WORKSPACE_ROOT / "sandbox" / "phase7a2-mcp").resolve()

ALLOWED_MCP_SERVERS = {"da_local_sandbox"}
ALLOWED_MCP_TOOLS = {"da_echo", "da_read_sandbox", "da_health", "da_slow_test"}

PROTECTED_PATHS = [
    Path(r"C:\AI\llama.cpp").resolve(),
    Path(r"C:\Users\Pc\.cache\huggingface\hub\models--ggml-org--Qwen3.6-35B-A3B-GGUF").resolve(),
    (WORKSPACE_ROOT / "backups").resolve(),
    (WORKSPACE_ROOT / "runner").resolve(),
    (WORKSPACE_ROOT / "config" / "security.yaml").resolve(),
    (WORKSPACE_ROOT / "config" / "system.yaml").resolve(),
    (WORKSPACE_ROOT / "config" / "VERSIONS.lock").resolve(),
    (WORKSPACE_ROOT / "scripts" / "security-guard.ps1").resolve(),
    (WORKSPACE_ROOT / "scripts" / "hermes-pre-tool-hook.py").resolve(),
    (WORKSPACE_ROOT / "scripts" / "hermes-memory-guard.ps1").resolve(),
    (WORKSPACE_ROOT / "scripts" / "hermes-mcp-plugin-guard.ps1").resolve(),
]

BLOCKED_ACTION_PATTERNS = [
    re.compile(r"(?i)\bgit\s+push\b"),
    re.compile(r"(?i)\bgit\s+reset\s+--hard\b"),
    re.compile(r"(?i)\bgit\s+clean\s+-fdx\b"),
    re.compile(r"(?i)\b(?:format|diskpart|bcdedit|reg\s+delete|shutdown|Restart-Computer)\b"),
    re.compile(r"(?i)\b(?:security\.yaml|RUN-CONTRACT\.yaml)\b"),
    re.compile(r"(?i)\b(?:write|delete|modify|overwrite|exec|shell|cmd|powershell)\b"),
]


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _is_reparse_or_symlink(p: Path) -> bool:
    try:
        if p.is_symlink():
            return True
        st = os.lstat(str(p))
        attrs = getattr(st, "st_file_attributes", 0)
        if attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
            return True
    except OSError:
        return False
    return False


def _validate_mcp_sandbox_path(raw_path: str) -> Tuple[bool, str]:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return False, "DENY [PATH_CONFINEMENT_VIOLATION]: Empty or missing relative_path."
    cleaned = raw_path.strip()
    if "\x00" in cleaned:
        return False, "DENY [PATH_CONFINEMENT_VIOLATION]: Null byte in path."
    parts = [seg for seg in cleaned.replace("/", "\\").split("\\") if seg]
    if ".." in parts or cleaned.startswith(".."):
        return False, f"DENY [PATH_CONFINEMENT_VIOLATION]: Path traversal ('..') blocked in '{raw_path}'."

    candidate = Path(cleaned)
    unres = candidate if candidate.is_absolute() else (MCP_SANDBOX_ROOT / candidate)
    try:
        curr = unres
        visited = set()
        while curr != curr.parent and str(curr) not in visited:
            visited.add(str(curr))
            if (curr.exists() or _is_reparse_or_symlink(curr)) and _is_reparse_or_symlink(curr):
                return False, f"DENY [PATH_CONFINEMENT_VIOLATION]: Symlink or NTFS junction blocked at '{curr}'."
            if curr == MCP_SANDBOX_ROOT:
                break
            curr = curr.parent
        resolved = unres.resolve()
        resolved.relative_to(MCP_SANDBOX_ROOT.resolve())
    except ValueError:
        return False, f"DENY [PATH_CONFINEMENT_VIOLATION]: Path '{raw_path}' resolves outside '{MCP_SANDBOX_ROOT}'."
    except Exception as exc:
        return False, f"DENY [PATH_CONFINEMENT_VIOLATION]: Invalid sandbox path '{raw_path}': {exc}"

    if _is_reparse_or_symlink(resolved):
        return False, f"DENY [PATH_CONFINEMENT_VIOLATION]: Target '{resolved}' is a symlink or reparse point."
    return True, "ALLOW"


def _validate_plugin_request(requested_action: str, target_path: str) -> Tuple[bool, str]:
    """Enforce deterministic Security Guard rules on plugin tool parameters (T-7A-PLUGIN-002)."""
    action_clean = (requested_action or "read_health").strip()
    if action_clean != "read_health":
        for pat in BLOCKED_ACTION_PATTERNS:
            if pat.search(action_clean):
                return (
                    False,
                    f"DENY [PLUGIN_SECURITY_GUARD]: Prohibited plugin action '{action_clean}' blocked by Security Guard (PLUGIN != PRIVILEGE ESCALATION).",
                )
        return (
            False,
            f"DENY [PLUGIN_SECURITY_GUARD]: Unauthorized action '{action_clean}'. Plugin 'desarrollador-autonomo-health' is strictly read-only ('read_health').",
        )

    if target_path and target_path.strip():
        raw_t = target_path.strip()
        if ".." in raw_t.replace("/", "\\").split("\\"):
            return (
                False,
                f"DENY [PLUGIN_SECURITY_GUARD]: Path traversal ('..') in target_path '{raw_t}' blocked by Security Guard.",
            )
        try:
            tp = Path(raw_t)
            resolved = tp.resolve() if tp.is_absolute() else (WORKSPACE_ROOT / tp).resolve()
        except Exception as exc:
            return False, f"DENY [PLUGIN_SECURITY_GUARD]: Invalid target_path '{raw_t}': {exc}"

        name_up = resolved.name.upper()
        if name_up in {"SECURITY.YAML", "RUN-CONTRACT.YAML"}:
            return (
                False,
                f"DENY [PLUGIN_SECURITY_GUARD]: Access/mutation to protected file '{resolved.name}' is forbidden.",
            )
        for prot in PROTECTED_PATHS:
            try:
                resolved.relative_to(prot)
                return (
                    False,
                    f"DENY [PLUGIN_SECURITY_GUARD]: Target path '{resolved}' is inside protected path '{prot}'.",
                )
            except ValueError:
                if resolved == prot:
                    return (
                        False,
                        f"DENY [PLUGIN_SECURITY_GUARD]: Target path '{resolved}' is a protected path.",
                    )
        try:
            resolved.relative_to(WORKSPACE_ROOT)
        except ValueError:
            return (
                False,
                f"DENY [PLUGIN_SECURITY_GUARD]: Target path '{resolved}' is outside workspace '{WORKSPACE_ROOT}'.",
            )

    return True, "ALLOW"


DA_PROJECT_HEALTH_SCHEMA: Dict[str, Any] = {
    "name": "da_project_health",
    "description": (
        "Returns deterministic read-only health status of the Desarrollador Autónomo workspace, "
        "governed configuration files, and MCP sandbox. Strictly governed by Security Guard."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "requested_action": {
                "type": "string",
                "description": "Operation to perform. Only 'read_health' is allowed.",
            },
            "target_path": {
                "type": "string",
                "description": "Optional workspace-relative path to inspect (read-only).",
            },
        },
        "required": [],
    },
}


def handle_da_project_health(args: Dict[str, Any], **kwargs: Any) -> str:
    """Handler for the governed plugin tool `da_project_health`."""
    req_action = str((args or {}).get("requested_action") or "read_health")
    target_path = str((args or {}).get("target_path") or "")

    allowed, reason = _validate_plugin_request(req_action, target_path)
    if not allowed:
        return json.dumps(
            {
                "status": "SECURITY_BLOCKED",
                "decision": "DENY",
                "plugin": PLUGIN_NAME,
                "version": PLUGIN_VERSION,
                "tool": "da_project_health",
                "requested_action": req_action,
                "target_path": target_path,
                "reason": reason,
                "timestamp": _utc_now_iso(),
            },
            ensure_ascii=False,
        )

    sys_yaml = WORKSPACE_ROOT / "config" / "system.yaml"
    sec_yaml = WORKSPACE_ROOT / "config" / "security.yaml"
    ver_lock = WORKSPACE_ROOT / "config" / "VERSIONS.lock"
    hook_py = WORKSPACE_ROOT / "scripts" / "hermes-pre-tool-hook.py"
    mcp_srv = WORKSPACE_ROOT / "scripts" / "mcp-sandbox-server.py"

    payload = {
        "status": "HEALTHY",
        "decision": "ALLOW",
        "plugin": PLUGIN_NAME,
        "version": PLUGIN_VERSION,
        "tool": "da_project_health",
        "requested_action": "read_health",
        "workspace_root": str(WORKSPACE_ROOT),
        "checks": {
            "system_yaml_present": sys_yaml.is_file(),
            "security_yaml_present": sec_yaml.is_file(),
            "versions_lock_present": ver_lock.is_file(),
            "pre_tool_hook_present": hook_py.is_file(),
            "mcp_sandbox_server_present": mcp_srv.is_file(),
            "mcp_sandbox_dir_present": MCP_SANDBOX_ROOT.is_dir(),
        },
        "timestamp": _utc_now_iso(),
    }
    return json.dumps(payload, ensure_ascii=False)


def da_mcp_and_plugin_pre_tool_guard(
    tool_name: str = "", args: Optional[Dict[str, Any]] = None, **kwargs: Any
) -> Optional[Dict[str, Any]]:
    """
    In-process deterministic pre_tool_call hook enforcing MCP allowlists, MCP path confinement,
    and plugin security boundaries before tool execution.
    """
    tname = str(tool_name or "").strip()
    targs = args if isinstance(args, dict) else {}

    # 1. Governed MCP tool calls (`mcp__<server>__<tool>`)
    if tname.startswith("mcp__"):
        parts = tname.split("__", 2)
        if len(parts) < 3:
            return {
                "action": "block",
                "message": f"DENY [TOOL_NOT_ALLOWED]: Malformed MCP tool name '{tname}'.",
            }
        _, server_name, raw_tool = parts
        if server_name not in ALLOWED_MCP_SERVERS:
            return {
                "action": "block",
                "message": f"DENY [TOOL_NOT_ALLOWED]: MCP server '{server_name}' is not in the approved allowlist.",
            }
        if raw_tool not in ALLOWED_MCP_TOOLS:
            return {
                "action": "block",
                "message": f"DENY [TOOL_NOT_ALLOWED]: MCP tool '{raw_tool}' on server '{server_name}' is not in the approved allowlist.",
            }
        if raw_tool == "da_read_sandbox":
            rel_path = str(targs.get("relative_path") or "")
            ok, reason = _validate_mcp_sandbox_path(rel_path)
            if not ok:
                return {"action": "block", "message": reason}
        return None

    # 2. Direct unprefixed call to forbidden MCP tool name if ever attempted
    if tname == "da_forbidden_test":
        return {
            "action": "block",
            "message": "DENY [TOOL_NOT_ALLOWED]: Tool 'da_forbidden_test' is explicitly excluded from the approved allowlist.",
        }

    # 3. Governed plugin tool call (`da_project_health`)
    if tname == "da_project_health":
        req_action = str(targs.get("requested_action") or "read_health")
        target_path = str(targs.get("target_path") or "")
        ok, reason = _validate_plugin_request(req_action, target_path)
        if not ok:
            return {"action": "block", "message": reason}

    return None


def register(ctx: Any) -> None:
    """Register the governed tool and pre_tool_call security hook with Hermes PluginManager."""
    ctx.register_tool(
        name="da_project_health",
        toolset="desarrollador_autonomo",
        schema=DA_PROJECT_HEALTH_SCHEMA,
        handler=handle_da_project_health,
        description=DA_PROJECT_HEALTH_SCHEMA["description"],
        override=False,
    )
    ctx.register_hook("pre_tool_call", da_mcp_and_plugin_pre_tool_guard)
