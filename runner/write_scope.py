"""Safe project write-scope matching shared by admission and Completion Gate."""
from __future__ import annotations

import re
from pathlib import PurePosixPath

_RESERVED_PREFIXES = (".git", ".autopilot", ".autopilot-history")
_RESERVED_EXACT = {"QWEN.md"}
_LEGACY_DENIED_PREFIXES = ("runner", "config/security")


def _norm(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("WRITE_SCOPE_INVALID")
    value = value.replace("\\", "/")
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise ValueError("WRITE_SCOPE_ABSOLUTE_DENIED")
    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError("WRITE_SCOPE_TRAVERSAL_DENIED")
    return value


def _reserved(name: str) -> bool:
    name = _norm(name)
    first = name.split("/", 1)[0]
    if first in _RESERVED_PREFIXES or name in _RESERVED_EXACT:
        return True
    return name == "runner" or name.startswith("runner/") or name == "config/security" or name.startswith("config/security/")


def validate_pattern(pattern: str) -> str:
    pattern = _norm(pattern)
    if _reserved(pattern.replace("*", "x").replace("?", "x")):
        raise ValueError("WRITE_SCOPE_RESERVED_DENIED")
    if pattern in {"*", "**", "*/**"}:
        raise ValueError("WRITE_SCOPE_TOO_BROAD")
    parts = pattern.split("/")
    wildcard_parts = [i for i, part in enumerate(parts) if "*" in part or "?" in part]
    if not wildcard_parts:
        if _reserved(pattern):
            raise ValueError("WRITE_SCOPE_RESERVED_DENIED")
        return pattern
    # Recursive scopes are admitted only as a literal directory plus trailing /**.
    if pattern.endswith("/**"):
        base = pattern[:-3]
        if not base or "*" in base or "?" in base:
            raise ValueError("WRITE_SCOPE_PATTERN_DENIED")
        if _reserved(base):
            raise ValueError("WRITE_SCOPE_RESERVED_DENIED")
        return pattern
    # Other globs may only affect the final filename component.
    if wildcard_parts != [len(parts) - 1]:
        raise ValueError("WRITE_SCOPE_PATTERN_DENIED")
    literal = re.sub(r"[*?]", "", parts[-1])
    if len(literal) < 3 or parts[-1].startswith("."):
        raise ValueError("WRITE_SCOPE_TOO_BROAD")
    parent = "/".join(parts[:-1])
    if parent and _reserved(parent):
        raise ValueError("WRITE_SCOPE_RESERVED_DENIED")
    return pattern


def _filename_glob(name: str, pattern: str) -> bool:
    # Wildcards never cross path separators.
    expr = ""
    for ch in pattern:
        if ch == "*":
            expr += "[^/]*"
        elif ch == "?":
            expr += "[^/]"
        else:
            expr += re.escape(ch)
    return re.fullmatch(expr, name) is not None


def scope_matches(name: str, patterns) -> bool:
    name = _norm(name)
    if _reserved(name):
        return False
    for raw in patterns or []:
        pattern = validate_pattern(raw)
        if pattern.endswith("/**"):
            base = pattern[:-3]
            if name == base or name.startswith(base + "/"):
                return True
        elif "*" in pattern or "?" in pattern:
            if _filename_glob(name, pattern):
                return True
        elif name == pattern:
            return True
    return False


def validate_plan_scope(plan: dict) -> None:
    patterns = plan.get("write_scope", [])
    if not isinstance(patterns, list):
        raise ValueError("WRITE_SCOPE_LIST_REQUIRED")
    if len(patterns) > 40:
        raise ValueError("WRITE_SCOPE_TOO_LARGE")
    for pattern in patterns:
        validate_pattern(pattern)
    immutable = {item["path"].replace("\\", "/") for item in plan.get("immutable_files", [])}
    for path in immutable:
        if scope_matches(path, patterns):
            raise ValueError("IMMUTABLE_FILE_IN_WRITE_SCOPE")


def allowed_change(name: str, plan: dict) -> bool:
    name = _norm(name)
    if _reserved(name):
        return False
    immutable = {item["path"].replace("\\", "/") for item in plan.get("immutable_files", [])}
    if name in immutable:
        return False
    exact = {item.replace("\\", "/") for item in plan.get("allowed_files", [])}
    return name in exact or scope_matches(name, plan.get("write_scope", []))
