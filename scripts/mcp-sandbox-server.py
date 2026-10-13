#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/mcp-sandbox-server.py — Governed Local MCP Sandbox Server (Subfase 7A.2)
Proyecto: Desarrollador Autónomo

Implements a deterministic, minimum-surface Model Context Protocol (MCP) server over stdio
(JSON-RPC 2.0, newline-delimited UTF-8) strictly confined to `sandbox/phase7a2-mcp/`.

Exposed MCP Tools:
- da_echo(message): Echoes a sanitized string with deterministic metadata.
- da_read_sandbox(relative_path): Reads a UTF-8 file strictly inside `sandbox/phase7a2-mcp/`.
  Blocks `../` traversal, absolute paths outside the sandbox (e.g., `C:\\Windows`), and
  NTFS symlinks/junctions (FILE_ATTRIBUTE_REPARSE_POINT).
- da_health(): Returns deterministic health status (`HEALTHY`, PID, sandbox root, policy).
- da_slow_test(sleep_seconds): Sleeps for `sleep_seconds` to validate deterministic 30s MCP timeouts.
- da_forbidden_test(payload): Deliberately exposed in `tools/list` but excluded from `tools.include`
  in `config.yaml` and `config/security.yaml` to test `T-7A-MCP-002` (`DENY / TOOL_NOT_ALLOWED`).
"""

from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

WORKSPACE_ROOT = Path(r"C:\Users\Pc\Documents\Proyectos Tech\Desarrollador autonomo").resolve()
SANDBOX_ROOT = (WORKSPACE_ROOT / "sandbox" / "phase7a2-mcp").resolve()
SECURITY_YAML_PATH = (WORKSPACE_ROOT / "config" / "security.yaml").resolve()

SERVER_NAME = "da_local_sandbox"
SERVER_VERSION = "1.0.0"
DEFAULT_ALLOWED_TOOLS = {"da_echo", "da_read_sandbox", "da_health", "da_slow_test"}

SECRET_PATTERNS: List[Tuple[str, re.Pattern[str], str]] = [
    ("openai_or_sk_key", re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"), "[REDACTED]"),
    ("github_pat", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_-]{8,}\b"), "[REDACTED]"),
    ("github_fine_grained_pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_-]{8,}\b"), "[REDACTED]"),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED]"),
    ("bearer_token", re.compile(r"(?i)(\bBearer\s+)(?!\[REDACTED\b)[A-Za-z0-9._~+/=-]{6,}"), r"\1[REDACTED]"),
    (
        "key_value_secret",
        re.compile(
            r"(?i)\b(password|passwd|pwd|api_key|apikey|token|secret|access_token|auth_token|client_secret|private_key)\b"
            r"(\s*[:=]\s*)"
            r"(?!\[REDACTED\])(\"[^\"]*\"|'[^']*'|[^\s,;\]\)]+)"
        ),
        r"\1\2[REDACTED]",
    ),
]


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


def sanitize_secrets(text: str) -> str:
    if not isinstance(text, str) or not text:
        return text
    out = text
    for _name, pattern, repl in SECRET_PATTERNS:
        out = pattern.sub(repl, out)
    return out


def load_security_mcp_policy(security_yaml: Path = SECURITY_YAML_PATH) -> Dict[str, Any]:
    """Load MCP policy from config/security.yaml if available, falling back to strict defaults."""
    policy: Dict[str, Any] = {
        "enabled": True,
        "allowed_servers": [SERVER_NAME],
        "allowed_tools": list(DEFAULT_ALLOWED_TOOLS),
        "sandbox_root": str(SANDBOX_ROOT),
        "timeout_seconds": 30,
        "connect_timeout_seconds": 15,
    }
    try:
        import yaml  # type: ignore
        if security_yaml.is_file():
            data = yaml.safe_load(security_yaml.read_text(encoding="utf-8-sig")) or {}
            mcp_cfg = data.get("mcp") or {}
            if isinstance(mcp_cfg, dict):
                if "enabled" in mcp_cfg:
                    policy["enabled"] = bool(mcp_cfg["enabled"])
                srv_cfg = (mcp_cfg.get("servers") or {}).get(SERVER_NAME) or {}
                if isinstance(srv_cfg, dict):
                    if isinstance(srv_cfg.get("allowed_tools"), list):
                        policy["allowed_tools"] = [str(x) for x in srv_cfg["allowed_tools"]]
                    if srv_cfg.get("sandbox_root"):
                        policy["sandbox_root"] = str(srv_cfg["sandbox_root"])
                    if srv_cfg.get("timeout_seconds"):
                        policy["timeout_seconds"] = int(srv_cfg["timeout_seconds"])
    except Exception:
        pass
    return policy


def _is_reparse_point_or_symlink(path_obj: Path) -> bool:
    """Detect Windows NTFS junctions, directory symbolic links, or file symlinks."""
    try:
        if path_obj.is_symlink():
            return True
        st = os.lstat(str(path_obj))
        file_attrs = getattr(st, "st_file_attributes", 0)
        if file_attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
            return True
    except OSError:
        return False
    return False


def validate_sandbox_path(raw_path: str, sandbox_root: Path = SANDBOX_ROOT) -> Tuple[bool, str, Optional[Path]]:
    """
    Strictly validate that `raw_path` resolves inside `sandbox_root`, contains no `..` traversal,
    and traverses no symlinks or NTFS junctions.
    """
    if not isinstance(raw_path, str) or not raw_path.strip():
        return False, "DENY [PATH_CONFINEMENT_VIOLATION]: Empty or invalid path argument.", None

    cleaned = raw_path.strip()
    if "\x00" in cleaned:
        return False, "DENY [PATH_CONFINEMENT_VIOLATION]: Null byte in path argument.", None

    # 1. Explicit traversal token check before resolution
    norm_slashes = cleaned.replace("/", "\\")
    parts = [p for p in norm_slashes.split("\\") if p]
    if ".." in parts or cleaned.startswith(".."):
        return (
            False,
            f"DENY [PATH_CONFINEMENT_VIOLATION]: Relative path traversal ('..') is forbidden in '{raw_path}'.",
            None,
        )

    # 2. Construct candidate path without resolving symlinks first so we can inspect every segment
    raw_p = Path(cleaned)
    if raw_p.is_absolute():
        unres = raw_p
    else:
        unres = sandbox_root / raw_p

    # Check if the candidate or any parent up to sandbox_root is a reparse point / junction / symlink
    try:
        curr = unres
        visited = set()
        while curr != curr.parent and str(curr) not in visited:
            visited.add(str(curr))
            if curr.exists() or _is_reparse_point_or_symlink(curr):
                if _is_reparse_point_or_symlink(curr):
                    return (
                        False,
                        f"DENY [PATH_CONFINEMENT_VIOLATION]: Symlink or NTFS junction escape detected at '{curr}'.",
                        None,
                    )
            if curr == sandbox_root:
                break
            curr = curr.parent
    except Exception as exc:
        return False, f"DENY [PATH_CONFINEMENT_VIOLATION]: Error inspecting path segments: {exc}", None

    # 3. Canonical resolution check
    try:
        resolved = unres.resolve()
        sandbox_resolved = sandbox_root.resolve()
    except Exception as exc:
        return False, f"DENY [PATH_CONFINEMENT_VIOLATION]: Failed to resolve canonical path '{raw_path}': {exc}", None

    try:
        resolved.relative_to(sandbox_resolved)
    except ValueError:
        return (
            False,
            f"DENY [PATH_CONFINEMENT_VIOLATION]: Canonical path '{resolved}' is outside allowed sandbox root '{sandbox_resolved}'.",
            None,
        )

    if _is_reparse_point_or_symlink(resolved):
        return (
            False,
            f"DENY [PATH_CONFINEMENT_VIOLATION]: Resolved target '{resolved}' is a symlink or reparse point.",
            None,
        )

    return True, "ALLOW", resolved


MCP_TOOLS_MANIFEST: List[Dict[str, Any]] = [
    {
        "name": "da_echo",
        "description": "Echoes a sanitized message back deterministically from the Desarrollador Autonomo governed MCP sandbox.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Text message to echo back.",
                }
            },
            "required": ["message"],
        },
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "da_read_sandbox",
        "description": "Reads a UTF-8 file strictly confined to sandbox/phase7a2-mcp/. Rejects '../', outside paths, and symlinks/junctions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "relative_path": {
                    "type": "string",
                    "description": "Relative path of the file inside sandbox/phase7a2-mcp/.",
                }
            },
            "required": ["relative_path"],
        },
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "da_health",
        "description": "Returns deterministic health status of the local governed MCP sandbox server.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "da_slow_test",
        "description": "Simulates a slow MCP operation that sleeps for sleep_seconds to validate deterministic 30s MCP timeouts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sleep_seconds": {
                    "type": "number",
                    "description": "Number of seconds to sleep before returning.",
                }
            },
            "required": ["sleep_seconds"],
        },
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "da_forbidden_test",
        "description": "Unapproved test tool exposed by the server to verify that Hermes and Security Guard block non-allowlisted tools.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "payload": {
                    "type": "string",
                    "description": "Optional test payload.",
                }
            },
        },
        "annotations": {"readOnlyHint": False},
    },
]


def execute_mcp_tool(name: str, arguments: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """Execute one MCP tool deterministically. Returns (is_error, payload_dict)."""
    policy = load_security_mcp_policy()
    if not policy.get("enabled", True):
        return True, {
            "status": "SECURITY_BLOCKED",
            "decision": "DENY",
            "reason": "MCP server is disabled by security policy.",
            "tool": name,
        }

    allowed_tools = set(policy.get("allowed_tools") or DEFAULT_ALLOWED_TOOLS)
    if name not in allowed_tools:
        return True, {
            "status": "TOOL_NOT_ALLOWED",
            "decision": "DENY",
            "reason": f"DENY [TOOL_NOT_ALLOWED]: Tool '{name}' is not in the approved allowlist {sorted(allowed_tools)}.",
            "tool": name,
            "server": SERVER_NAME,
        }

    if name == "da_echo":
        raw_msg = str(arguments.get("message") or "")
        clean_msg = sanitize_secrets(raw_msg)
        return False, {
            "status": "OK",
            "decision": "ALLOW",
            "server": SERVER_NAME,
            "tool": "da_echo",
            "echo": clean_msg,
            "pid": os.getpid(),
            "timestamp": utc_now_iso(),
        }

    if name == "da_health":
        SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)
        return False, {
            "status": "HEALTHY",
            "decision": "ALLOW",
            "server": SERVER_NAME,
            "version": SERVER_VERSION,
            "tool": "da_health",
            "pid": os.getpid(),
            "sandbox_root": str(SANDBOX_ROOT),
            "allowed_tools": sorted(allowed_tools),
            "timestamp": utc_now_iso(),
        }

    if name == "da_read_sandbox":
        rel_path = str(arguments.get("relative_path") or "")
        SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)
        allowed, reason, resolved_path = validate_sandbox_path(rel_path, SANDBOX_ROOT)
        if not allowed or resolved_path is None:
            return True, {
                "status": "PATH_CONFINEMENT_VIOLATION",
                "decision": "DENY",
                "server": SERVER_NAME,
                "tool": "da_read_sandbox",
                "requested_path": rel_path,
                "reason": reason,
                "timestamp": utc_now_iso(),
            }
        if not resolved_path.is_file():
            return True, {
                "status": "FILE_NOT_FOUND",
                "decision": "DENY",
                "server": SERVER_NAME,
                "tool": "da_read_sandbox",
                "requested_path": rel_path,
                "canonical_path": str(resolved_path),
                "reason": f"File not found inside sandbox: {resolved_path.name}",
                "timestamp": utc_now_iso(),
            }
        try:
            content = resolved_path.read_text(encoding="utf-8", errors="replace")
            sanitized_content = sanitize_secrets(content)
            return False, {
                "status": "OK",
                "decision": "ALLOW",
                "server": SERVER_NAME,
                "tool": "da_read_sandbox",
                "requested_path": rel_path,
                "canonical_path": str(resolved_path),
                "content": sanitized_content,
                "bytes": len(sanitized_content.encode("utf-8")),
                "timestamp": utc_now_iso(),
            }
        except Exception as exc:
            return True, {
                "status": "READ_ERROR",
                "decision": "DENY",
                "server": SERVER_NAME,
                "tool": "da_read_sandbox",
                "requested_path": rel_path,
                "reason": str(exc),
                "timestamp": utc_now_iso(),
            }

    if name == "da_slow_test":
        try:
            sleep_sec = float(arguments.get("sleep_seconds", 35.0))
        except (TypeError, ValueError):
            sleep_sec = 35.0
        sleep_sec = max(0.1, min(sleep_sec, 60.0))
        time.sleep(sleep_sec)
        return False, {
            "status": "OK",
            "decision": "ALLOW",
            "server": SERVER_NAME,
            "tool": "da_slow_test",
            "slept_seconds": sleep_sec,
            "pid": os.getpid(),
            "timestamp": utc_now_iso(),
        }

    return True, {
        "status": "UNKNOWN_TOOL",
        "decision": "DENY",
        "server": SERVER_NAME,
        "tool": name,
        "reason": f"Unknown MCP tool '{name}'.",
    }


def _send_jsonrpc(msg: Dict[str, Any]) -> None:
    line = json.dumps(msg, ensure_ascii=False)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def run_stdio_server() -> int:
    """Run the JSON-RPC 2.0 MCP stdio server loop until EOF on stdin."""
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8-sig", errors="replace")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)

    for raw_line in sys.stdin:
        line = raw_line.lstrip("\ufeff").strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as exc:
            _send_jsonrpc({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {exc}"},
            })
            continue

        if not isinstance(req, dict):
            continue

        method = req.get("method")
        req_id = req.get("id")
        params = req.get("params") if isinstance(req.get("params"), dict) else {}

        # Notifications have no 'id'
        if req_id is None:
            continue

        if method == "initialize":
            client_proto = str(params.get("protocolVersion") or "2024-11-05")
            _send_jsonrpc({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": client_proto,
                    "capabilities": {
                        "tools": {"listChanged": False},
                    },
                    "serverInfo": {
                        "name": SERVER_NAME,
                        "version": SERVER_VERSION,
                    },
                },
            })
        elif method == "ping":
            _send_jsonrpc({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {},
            })
        elif method == "tools/list":
            _send_jsonrpc({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": MCP_TOOLS_MANIFEST,
                },
            })
        elif method == "tools/call":
            tool_name = str(params.get("name") or "")
            tool_args = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
            is_err, result_payload = execute_mcp_tool(tool_name, tool_args)
            _send_jsonrpc({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result_payload, ensure_ascii=False),
                        }
                    ],
                    "structuredContent": result_payload,
                    "isError": is_err,
                },
            })
        else:
            _send_jsonrpc({
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}",
                },
            })

    return 0


def run_client_probe(
    tool_name: str,
    tool_args: Dict[str, Any],
    timeout_sec: float = 30.0,
    server_script: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Spawn the MCP stdio server as a child process, perform JSON-RPC 2.0 handshake + tool call
    with a strict wall-clock timeout, and ensure deterministic child cleanup.
    """
    target_script = server_script or Path(__file__).resolve()
    policy = load_security_mcp_policy()
    if not policy.get("enabled", True):
        return {
            "status": "DISABLED",
            "decision": "DENY",
            "server": SERVER_NAME,
            "tool": tool_name,
            "reason": "MCP server is disabled in security policy.",
        }

    if not target_script.is_file():
        return {
            "status": "UNAVAILABLE",
            "decision": "DENY",
            "server": SERVER_NAME,
            "tool": tool_name,
            "reason": f"MCP server script not found: {target_script}",
        }

    start_ts = time.monotonic()
    proc: Optional[subprocess.Popen[str]] = None
    child_pid: Optional[int] = None
    try:
        proc = subprocess.Popen(
            [sys.executable, str(target_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        child_pid = proc.pid

        requests = [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "da-mcp-guard-client", "version": "1.0.0"},
                },
            },
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": tool_args},
            },
        ]
        stdin_payload = "\n".join(json.dumps(r, ensure_ascii=False) for r in requests) + "\n"
        stdout_data, stderr_data = proc.communicate(input=stdin_payload, timeout=timeout_sec)
        elapsed = round(time.monotonic() - start_ts, 3)

        if proc.returncode != 0 and not stdout_data.strip():
            return {
                "status": "UNAVAILABLE",
                "decision": "DENY",
                "server": SERVER_NAME,
                "tool": tool_name,
                "child_pid": child_pid,
                "duration_seconds": elapsed,
                "reason": f"MCP server exited with code {proc.returncode}: {stderr_data.strip()[:300]}",
            }

        lines = [ln.strip() for ln in stdout_data.splitlines() if ln.strip()]
        call_resp = None
        for ln in lines:
            try:
                parsed = json.loads(ln)
                if isinstance(parsed, dict) and parsed.get("id") == 2:
                    call_resp = parsed
            except Exception:
                continue

        if not call_resp:
            return {
                "status": "UNAVAILABLE",
                "decision": "DENY",
                "server": SERVER_NAME,
                "tool": tool_name,
                "child_pid": child_pid,
                "duration_seconds": elapsed,
                "reason": "MCP server did not return a response for tools/call.",
            }

        res_obj = call_resp.get("result") or {}
        is_err = bool(res_obj.get("isError", False))
        structured = res_obj.get("structuredContent")
        if not isinstance(structured, dict):
            content_list = res_obj.get("content") or []
            if content_list and isinstance(content_list[0], dict):
                try:
                    structured = json.loads(content_list[0].get("text") or "{}")
                except Exception:
                    structured = {"raw_text": content_list[0].get("text")}
            else:
                structured = {}

        return {
            "status": structured.get("status", "ERROR" if is_err else "OK"),
            "decision": structured.get("decision", "DENY" if is_err else "ALLOW"),
            "is_error": is_err,
            "server": SERVER_NAME,
            "tool": tool_name,
            "child_pid": child_pid,
            "duration_seconds": elapsed,
            "result": structured,
        }

    except subprocess.TimeoutExpired:
        elapsed = round(time.monotonic() - start_ts, 3)
        if proc is not None:
            try:
                proc.kill()
                proc.wait(timeout=5)
            except Exception:
                pass
        return {
            "status": "MCP_TIMEOUT",
            "decision": "DENY",
            "is_error": True,
            "server": SERVER_NAME,
            "tool": tool_name,
            "child_pid": child_pid,
            "duration_seconds": elapsed,
            "timeout_seconds": timeout_sec,
            "reason": f"MCP tool '{tool_name}' exceeded deterministic timeout of {timeout_sec}s and was terminated cleanly.",
        }
    except Exception as exc:
        elapsed = round(time.monotonic() - start_ts, 3)
        if proc is not None:
            try:
                proc.kill()
                proc.wait(timeout=3)
            except Exception:
                pass
        return {
            "status": "UNAVAILABLE",
            "decision": "DENY",
            "is_error": True,
            "server": SERVER_NAME,
            "tool": tool_name,
            "child_pid": child_pid,
            "duration_seconds": elapsed,
            "reason": str(exc),
        }


def _decode_args(args_json: str, args_b64: str) -> Dict[str, Any]:
    if args_b64:
        try:
            raw = base64.b64decode(args_b64).decode("utf-8")
            obj = json.loads(raw)
            return obj if isinstance(obj, dict) else {}
        except Exception:
            return {}
    if args_json:
        try:
            obj = json.loads(args_json)
            return obj if isinstance(obj, dict) else {}
        except Exception:
            return {}
    return {}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Desarrollador Autonomo Governed Local MCP Sandbox Server")
    parser.add_argument("--health-check", action="store_true", help="Run deterministic MCP health check probe and output JSON")
    parser.add_argument("--call-tool", type=str, help="Invoke a tool via MCP stdio client probe and output JSON")
    parser.add_argument("--args-json", type=str, default="", help="JSON arguments for --call-tool / --invoke-plugin")
    parser.add_argument("--args-b64", type=str, default="", help="Base64-encoded UTF-8 JSON arguments (safe from PS 5.1 quote stripping)")
    parser.add_argument("--timeout", type=float, default=30.0, help="Timeout in seconds for --call-tool / --health-check")
    parser.add_argument("--dump-yaml-json", type=str, help="Read a YAML file and print its JSON representation")
    parser.add_argument("--validate-path-b64", action="store_true", help="Validate relative_path from --args-b64 against sandbox confinement")
    parser.add_argument("--invoke-plugin", type=str, help="Path to plugin __init__.py to invoke with --args-b64")
    parser.add_argument("--test-allowlist", nargs=2, metavar=("CONFIG_YAML", "PLUGIN_INIT"), help="Test Hermes native MCP filter and plugin pre_tool_call hook")
    args, _ = parser.parse_known_args()

    if args.dump_yaml_json:
        import yaml  # type: ignore
        with open(args.dump_yaml_json, "r", encoding="utf-8-sig") as f:
            data = yaml.safe_load(f)
        print(json.dumps(data, ensure_ascii=False))
        return 0

    if args.validate_path_b64:
        parsed_args = _decode_args(args.args_json, args.args_b64)
        rel = str(parsed_args.get("relative_path") or "")
        ok, reason, resolved = validate_sandbox_path(rel)
        print(json.dumps({"allowed": ok, "reason": reason, "resolved": str(resolved) if resolved else None}, ensure_ascii=False))
        return 0

    if args.invoke_plugin:
        parsed_args = _decode_args(args.args_json, args.args_b64)
        spec = importlib.util.spec_from_file_location("da_plugin", args.invoke_plugin)
        if spec is None or spec.loader is None:
            print(json.dumps({"status": "ERROR", "decision": "DENY", "allowed": False, "reason": "Could not load plugin spec"}, ensure_ascii=False))
            return 1
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        hook_res = mod.da_mcp_and_plugin_pre_tool_guard(tool_name="da_project_health", args=parsed_args)
        if isinstance(hook_res, dict) and hook_res.get("action") == "block":
            print(json.dumps({
                "status": "SECURITY_BLOCKED",
                "decision": "DENY",
                "allowed": False,
                "blocked_by": "pre_tool_call_hook",
                "plugin": mod.PLUGIN_NAME,
                "tool": "da_project_health",
                "reason": hook_res.get("message"),
            }, ensure_ascii=False))
            return 0
        raw_out = mod.handle_da_project_health(parsed_args)
        parsed = json.loads(raw_out)
        parsed["allowed"] = (parsed.get("decision") == "ALLOW")
        print(json.dumps(parsed, ensure_ascii=False))
        return 0

    if args.test_allowlist:
        import yaml  # type: ignore
        cfg_path, plugin_init_path = args.test_allowlist
        sys.path.insert(0, r"C:\Users\Pc\AppData\Local\hermes\hermes-agent")
        from tools.mcp_tool_registration import _make_tool_filter
        with open(cfg_path, "r", encoding="utf-8-sig") as f:
            cfg = yaml.safe_load(f)
        srv_cfg = cfg["mcp_servers"]["da_local_sandbox"]
        pred = _make_tool_filter("da_local_sandbox", srv_cfg)
        spec = importlib.util.spec_from_file_location("da_plugin", plugin_init_path)
        mod = importlib.util.module_from_spec(spec)  # type: ignore
        spec.loader.exec_module(mod)  # type: ignore
        hook_verdict = mod.da_mcp_and_plugin_pre_tool_guard(
            tool_name="mcp__da_local_sandbox__da_forbidden_test",
            args={"payload": "test"},
        )
        print(json.dumps({
            "hermes_native_filter_allows_da_echo": bool(pred("da_echo")),
            "hermes_native_filter_allows_da_forbidden_test": bool(pred("da_forbidden_test")),
            "plugin_pre_tool_hook_verdict": hook_verdict,
        }, ensure_ascii=False))
        return 0

    if args.health_check:
        res = run_client_probe("da_health", {}, timeout_sec=min(args.timeout, 15.0))
        health_status = res.get("result", {}).get("status") if not res.get("is_error") else res.get("status", "UNAVAILABLE")
        out = {
            "health_state": health_status if health_status in {"HEALTHY", "UNAVAILABLE", "TIMEOUT", "DISABLED", "SECURITY_BLOCKED"} else ("TIMEOUT" if res.get("status") == "MCP_TIMEOUT" else "UNAVAILABLE"),
            "probe": res,
        }
        print(json.dumps(out, ensure_ascii=False))
        return 0 if out["health_state"] == "HEALTHY" else 1

    if args.call_tool:
        parsed_args = _decode_args(args.args_json, args.args_b64)
        res = run_client_probe(args.call_tool, parsed_args, timeout_sec=args.timeout)
        print(json.dumps(res, ensure_ascii=False))
        return 0 if not res.get("is_error") else 2

    return run_stdio_server()


if __name__ == "__main__":
    raise SystemExit(main())
