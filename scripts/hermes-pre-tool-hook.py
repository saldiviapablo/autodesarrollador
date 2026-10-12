#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/hermes-pre-tool-hook.py — Native Hermes pre_tool_call Security & Memory Sanitization Hook
Proyecto: Desarrollador Autónomo (Subfase 7A.1)

Responsibilities:
1. Pre-write Secret Sanitization for Hermes Persistent Memory (`memory` tool):
   - Intercepts `add`, `replace`, and `operations` batch calls BEFORE MemoryStore writes to MEMORY.md / USER.md.
   - Redacts API keys (`sk-...`), GitHub tokens (`ghp_...`, `github_pat_...`), Bearer tokens (`Bearer ...`),
     and credential assignments (`password=...`, `api_key=...`, `token=...`, `secret=...`) to `[REDACTED]`.
   - Returns `{"action": "modify", "args": ...}` so the raw secret never reaches disk.
2. Deterministic Guardrail Enforcement (`terminal`, `write_file`, `patch`, `edit_file`, `skill_manage`):
   - Enforces `config/security.yaml` policies even if an adversarial skill or prompt attempts to bypass them.
   - Blocks `git push`, `git reset --hard`, `git clean -fdx`, `format`, `diskpart`, `bcdedit`, `reg delete`,
     `shutdown`, `Restart-Computer`.
   - Blocks writes/modifications to protected paths (`config/security.yaml`, `RUN-CONTRACT.yaml`, `runner/`,
     `backups/`, `C:\\AI\\llama.cpp`, `scripts/security-guard.ps1`, `scripts/hermes-pre-tool-hook.py`).
   - Blocks writes outside the allowed workspace (`Desarrollador autonomo` and the active Hermes profile dir).
3. CLI Utility Mode:
   - `--sanitize-text <text>`: prints sanitized text to stdout.
   - `--sanitize-file <path>`: sanitizes a memory/markdown file in place (atomic write) and outputs JSON report.
   - `--audit-skill <path>`: deterministically scans a SKILL.md for forbidden commands/paths and outputs JSON verdict.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

WORKSPACE_ROOT = Path(r"C:\Users\Pc\Documents\Proyectos Tech\Desarrollador autonomo").resolve()
HERMES_PROFILE_ROOT = Path(r"C:\Users\Pc\AppData\Local\hermes\profiles\desarrollador-autonomo").resolve()

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
]

# Secret regexes applied in order before any memory persistence
SECRET_PATTERNS: List[Tuple[str, re.Pattern[str], str]] = [
    (
        "openai_or_sk_key",
        re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
        "[REDACTED]",
    ),
    (
        "github_pat",
        re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_-]{8,}\b"),
        "[REDACTED]",
    ),
    (
        "github_fine_grained_pat",
        re.compile(r"\bgithub_pat_[A-Za-z0-9_-]{8,}\b"),
        "[REDACTED]",
    ),
    (
        "aws_access_key",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        "[REDACTED]",
    ),
    (
        "bearer_token",
        re.compile(r"(?i)(\bBearer\s+)(?!\[REDACTED\b)[A-Za-z0-9._~+/=-]{6,}"),
        r"\1[REDACTED]",
    ),
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

BLOCKED_COMMAND_REGEXES: List[Tuple[str, re.Pattern[str]]] = [
    ("git_push", re.compile(r"(?i)\bgit\s+push\b")),
    ("git_reset_hard", re.compile(r"(?i)\bgit\s+reset\s+--hard\b")),
    ("git_clean_fdx", re.compile(r"(?i)\bgit\s+clean\s+-[a-z]*f[a-z]*d[a-z]*x\b|\bgit\s+clean\s+-fdx\b")),
    ("diskpart", re.compile(r"(?i)\bdiskpart\b")),
    ("bcdedit", re.compile(r"(?i)\bbcdedit\b")),
    ("reg_delete", re.compile(r"(?i)\breg\s+delete\b")),
    ("shutdown", re.compile(r"(?i)\bshutdown(?:\.exe)?\s+/[sr]|\bStop-Computer\b")),
    ("restart_computer", re.compile(r"(?i)\bRestart-Computer\b")),
    ("format_volume", re.compile(r"(?i)(?:^|[;&|]\s*)format(?:\.com|\.exe)?\s+[a-zA-Z]:|\bFormat-Volume\b")),
    ("destructive_root_delete", re.compile(r"(?i)\b(?:Remove-Item|del|rd|rmdir)\b[^\n;]*\b[a-zA-Z]:\\\s*(?:-Recurse|/s)")),
]


def sanitize_text(text: str) -> Tuple[str, List[str]]:
    """Redact all secret patterns in text to [REDACTED]. Returns (sanitized_text, matched_rule_names)."""
    if not isinstance(text, str) or not text:
        return text, []
    sanitized = text
    matched: List[str] = []
    for rule_name, pattern, replacement in SECRET_PATTERNS:
        if pattern.search(sanitized):
            sanitized = pattern.sub(replacement, sanitized)
            if rule_name not in matched:
                matched.append(rule_name)
    return sanitized, matched


def sanitize_memory_args(args: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """Sanitize arguments of a Hermes `memory` tool call before execution."""
    new_args = copy.deepcopy(args)
    matched_rules: List[str] = []

    for field_name in ("content", "new_text", "old_text"):
        val = new_args.get(field_name)
        if isinstance(val, str) and val:
            sanitized_val, rules = sanitize_text(val)
            if sanitized_val != val:
                new_args[field_name] = sanitized_val
                for r in rules:
                    if r not in matched_rules:
                        matched_rules.append(r)

    ops = new_args.get("operations")
    if isinstance(ops, list):
        for op in ops:
            if not isinstance(op, dict):
                continue
            for field_name in ("content", "new_text", "old_text"):
                val = op.get(field_name)
                if isinstance(val, str) and val:
                    sanitized_val, rules = sanitize_text(val)
                    if sanitized_val != val:
                        op[field_name] = sanitized_val
                        for r in rules:
                            if r not in matched_rules:
                                matched_rules.append(r)

    return new_args, matched_rules


def _is_subpath(candidate: Path, parent: Path) -> bool:
    try:
        candidate.relative_to(parent)
        return True
    except ValueError:
        return False


def check_target_path(raw_path: str, cwd: str = "") -> Tuple[bool, str]:
    """Validate a file write/edit path against workspace boundaries and protected paths."""
    if not raw_path or not isinstance(raw_path, str):
        return False, "Missing or invalid target path"
    try:
        base_dir = Path(cwd).resolve() if cwd else WORKSPACE_ROOT
        p = Path(os.path.expanduser(raw_path))
        resolved = (base_dir / p).resolve() if not p.is_absolute() else p.resolve()
    except Exception as exc:
        return False, f"Cannot resolve target path {raw_path!r}: {exc}"

    name_upper = resolved.name.upper()
    if name_upper == "RUN-CONTRACT.YAML" or name_upper == "SECURITY.YAML":
        return False, f"Target file '{resolved}' is protected by deterministic security policy (RUN-CONTRACT / security.yaml)."

    for prot in PROTECTED_PATHS:
        if resolved == prot or _is_subpath(resolved, prot):
            return False, f"Target path '{resolved}' is inside protected infrastructure path '{prot}'."

    in_workspace = resolved == WORKSPACE_ROOT or _is_subpath(resolved, WORKSPACE_ROOT)
    in_profile = resolved == HERMES_PROFILE_ROOT or _is_subpath(resolved, HERMES_PROFILE_ROOT)
    if not (in_workspace or in_profile):
        return False, f"Target path '{resolved}' is outside the authorized workspace '{WORKSPACE_ROOT}'."

    return True, "ALLOWED"


def check_terminal_command(command: str, cwd: str = "") -> Tuple[bool, str]:
    """Validate a terminal command against blocked commands, protected paths, and workspace boundaries."""
    if not isinstance(command, str) or not command.strip():
        return True, "ALLOWED"

    for rule_name, pattern in BLOCKED_COMMAND_REGEXES:
        if pattern.search(command):
            return False, f"Command blocked by security policy ({rule_name}): '{command.strip()[:120]}'"

    # Check if command attempts to modify security.yaml, RUN-CONTRACT.yaml, or runner/
    write_Redirect_or_cmd = re.search(
        r"(?i)(?:Set-Content|Add-Content|Out-File|Copy-Item|Move-Item|Remove-Item|\bdel\b|\berase\b|\brm\b|>|>>)",
        command,
    )
    if write_Redirect_or_cmd or re.search(r"(?i)security\.yaml|RUN-CONTRACT\.yaml", command):
        if re.search(r"(?i)\bsecurity\.yaml\b|\bRUN-CONTRACT\.yaml\b", command):
            return False, "Command blocked: modifying or overwriting security.yaml / RUN-CONTRACT.yaml is forbidden."

    # Check for explicit absolute paths outside workspace in write operations
    if write_Redirect_or_cmd:
        for match in re.finditer(r'([A-Za-z]:\\[A-Za-z0-9_.\-\\ /]+)', command):
            candidate_str = match.group(1).strip().rstrip('"\'')
            allowed, reason = check_target_path(candidate_str, cwd=cwd)
            if not allowed:
                return False, f"Command blocked by path policy: {reason}"

    return True, "ALLOWED"


def audit_skill_content(skill_text: str, skill_path: str = "") -> Dict[str, Any]:
    """Deterministically audit a SKILL.md for guardrail violations (blocked commands, protected paths, outside writes)."""
    violations: List[Dict[str, str]] = []

    for rule_name, pattern in BLOCKED_COMMAND_REGEXES:
        m = pattern.search(skill_text)
        if m:
            violations.append({
                "type": "BLOCKED_COMMAND_IN_SKILL",
                "rule": rule_name,
                "excerpt": m.group(0),
                "message": f"Skill contains forbidden command pattern '{rule_name}': {m.group(0)}",
            })

    if re.search(r"(?i)(?:modify|edit|overwrite|delete|disable|bypass|modificar|editar|sobrescribir|desactivar)[^\n]{0,80}\b(?:security\.yaml|RUN-CONTRACT\.yaml)\b", skill_text) or re.search(r"(?i)\b(?:security\.yaml|RUN-CONTRACT\.yaml)\b[^\n]{0,80}(?:allow_push:\s*true|allow_write_outside:\s*true)", skill_text):
        violations.append({
            "type": "PROTECTED_CONFIG_TAMPERING_IN_SKILL",
            "rule": "protected_security_config",
            "excerpt": "security.yaml / RUN-CONTRACT.yaml",
            "message": "Skill instructs tampering with protected security configuration (security.yaml / RUN-CONTRACT.yaml).",
        })

    # Detect explicit paths outside workspace in skill instructions
    for m in re.finditer(r'([A-Za-z]:/(?:[^\s"\'`<>|]+)|[A-Za-z]:\\(?:[^\s"\'`<>|]+))', skill_text):
        raw_p = m.group(1).rstrip(".,;:)]}")
        allowed, reason = check_target_path(raw_p)
        if not allowed:
            violations.append({
                "type": "UNAUTHORIZED_PATH_IN_SKILL",
                "rule": "workspace_isolation",
                "excerpt": raw_p,
                "message": reason,
            })

    status = "DENY" if violations else "ALLOW"
    return {
        "status": status,
        "allowed": len(violations) == 0,
        "skill_path": skill_path,
        "violations_count": len(violations),
        "violations": violations,
    }


def handle_pre_tool_call(payload: Dict[str, Any]) -> int:
    """Process a Hermes pre_tool_call stdin JSON payload."""
    tool_name = str(payload.get("tool_name") or "").strip()
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}
    cwd = str(payload.get("cwd") or str(WORKSPACE_ROOT))

    # 1. Persistent Memory Tool -> Sanitize secrets BEFORE writing
    if tool_name == "memory":
        sanitized_args, matched_rules = sanitize_memory_args(tool_input)
        if matched_rules:
            sys.stdout.write(json.dumps({"action": "modify", "args": sanitized_args}, ensure_ascii=False))
            sys.stdout.flush()
        return 0

    # 2. Terminal Tool -> Validate command against blocked commands & protected paths
    if tool_name == "terminal":
        cmd = str(tool_input.get("command") or "")
        allowed, reason = check_terminal_command(cmd, cwd=cwd)
        if not allowed:
            msg = f"DENY [SECURITY_GUARD]: {reason}"
            sys.stdout.write(json.dumps({"action": "block", "message": msg}, ensure_ascii=False))
            sys.stdout.flush()
            return 2
        return 0

    # 3. File Mutation Tools -> Validate target path against workspace & protected paths
    if tool_name in {"write_file", "patch", "edit_file"}:
        target_path = str(tool_input.get("path") or tool_input.get("file_path") or tool_input.get("target_file") or "")
        allowed, reason = check_target_path(target_path, cwd=cwd)
        if not allowed:
            msg = f"DENY [SECURITY_GUARD]: {reason}"
            sys.stdout.write(json.dumps({"action": "block", "message": msg}, ensure_ascii=False))
            sys.stdout.flush()
            return 2
        return 0

    # 4. Skill View / Skill Manage -> Audit skill content before allowing adversarial skill execution
    if tool_name == "skill_view":
        skill_name = str(tool_input.get("name") or "").strip()
        if skill_name:
            for candidate in (HERMES_PROFILE_ROOT / "skills").rglob("SKILL.md"):
                try:
                    txt = candidate.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                if re.search(rf"(?m)^name:\s*{re.escape(skill_name)}\s*$", txt) or candidate.parent.name == skill_name:
                    audit = audit_skill_content(txt, str(candidate))
                    if not audit["allowed"]:
                        reasons = "; ".join(v["message"] for v in audit["violations"])
                        msg = f"DENY [SECURITY_GUARD]: Adversarial or policy-violating skill '{skill_name}' blocked: {reasons}"
                        sys.stdout.write(json.dumps({"action": "block", "message": msg}, ensure_ascii=False))
                        sys.stdout.flush()
                        return 2
        return 0

    if tool_name == "skill_manage":
        content = str(tool_input.get("content") or "")
        if content:
            audit = audit_skill_content(content, str(tool_input.get("name") or ""))
            if not audit["allowed"]:
                reasons = "; ".join(v["message"] for v in audit["violations"])
                msg = f"DENY [SECURITY_GUARD]: Skill creation/modification blocked by policy: {reasons}"
                sys.stdout.write(json.dumps({"action": "block", "message": msg}, ensure_ascii=False))
                sys.stdout.flush()
                return 2
        return 0

    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Hermes pre_tool_call Security & Memory Sanitization Hook")
    parser.add_argument("--sanitize-text", type=str, help="Sanitize secret patterns in text and output JSON")
    parser.add_argument("--sanitize-file", type=str, help="Sanitize secret patterns in a file in-place and output JSON")
    parser.add_argument("--audit-skill", type=str, help="Audit a SKILL.md file against security guardrails")
    args, _ = parser.parse_known_args()

    if args.sanitize_text is not None:
        sanitized, rules = sanitize_text(args.sanitize_text)
        print(json.dumps({"sanitized_text": sanitized, "redacted_rules": rules, "was_modified": sanitized != args.sanitize_text}, ensure_ascii=False))
        return 0

    if args.sanitize_file is not None:
        fpath = Path(args.sanitize_file).resolve()
        if not fpath.is_file():
            print(json.dumps({"success": False, "error": f"File not found: {fpath}"}, ensure_ascii=False))
            return 1
        original = fpath.read_text(encoding="utf-8-sig")
        sanitized, rules = sanitize_text(original)
        if sanitized != original:
            tmp = fpath.with_suffix(fpath.suffix + ".tmp")
            tmp.write_text(sanitized, encoding="utf-8")
            os.replace(tmp, fpath)
        print(json.dumps({
            "success": True,
            "file": str(fpath),
            "was_modified": sanitized != original,
            "redacted_rules": rules,
        }, ensure_ascii=False))
        return 0

    if args.audit_skill is not None:
        spath = Path(args.audit_skill).resolve()
        if not spath.is_file():
            print(json.dumps({"status": "ERROR", "allowed": False, "error": f"File not found: {spath}"}, ensure_ascii=False))
            return 1
        txt = spath.read_text(encoding="utf-8-sig", errors="replace")
        report = audit_skill_content(txt, str(spath))
        print(json.dumps(report, ensure_ascii=False))
        return 0 if report["allowed"] else 2

    # Default mode: read Hermes pre_tool_call JSON from stdin (strip any UTF-8 BOM from PowerShell/.NET pipes)
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8-sig", errors="replace")
    raw_stdin = sys.stdin.read()
    if not raw_stdin:
        return 0
    raw_stdin = raw_stdin.lstrip("\ufeff").strip()
    if not raw_stdin:
        return 0
    try:
        payload = json.loads(raw_stdin)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"Invalid JSON payload on stdin: {exc}\n")
        return 2
    if not isinstance(payload, dict):
        return 0
    return handle_pre_tool_call(payload)


if __name__ == "__main__":
    raise SystemExit(main())
