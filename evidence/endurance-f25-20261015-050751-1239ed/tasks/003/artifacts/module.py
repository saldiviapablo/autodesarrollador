"""Portable file catalog validator and duplicate reporter.

Contract
--------
* ``catalog(entries)`` validates and sorts a list of file entries.
  - *entries*: list of ``dict`` with exactly the keys ``path``, ``size``, ``sha256``.
  - ``path``: non-empty POSIX relative path; no backslash, colon, leading ``/``, empty
    component, ``.``, or ``..``; no NUL or newline. Unicode is allowed.
  - ``size``: integer >= 0; ``bool`` is forbidden.
  - ``sha256``: exactly 64 lowercase hexadecimal characters.
  - Duplicate paths raise ``ValueError``.
  - Returns a **new** list of dicts sorted by ``path``; never mutates the input.
  - Raises ``ValueError`` on any malformed entry or duplicate path.

* ``duplicate_groups(entries)`` uses ``catalog`` and returns duplicate groups.
  - A *duplicate* is a pair of entries sharing the same ``(size, sha256)``.
  - Returns a list of lists of ``path`` strings, each group sorted, only groups of
    length >= 2, and groups sorted lexicographically.

CLI
---
Reads a JSON array from stdin, outputs ``{"catalog": ..., "duplicates": ...}``
to stdout (``ensure_ascii=False``). On invalid input exits with code 2 and
prints a concise error to stderr.

No filesystem I/O is performed — all validation is in-memory.

Examples
--------
>>> catalog([{'path': 'b.txt', 'size': 10, 'sha256': 'a' * 64},
...          {'path': 'a.txt', 'size': 10, 'sha256': 'a' * 64}])
[{'path': 'a.txt', 'size': 10, 'sha256': 'a' * 64},
 {'path': 'b.txt', 'size': 10, 'sha256': 'a' * 64}]

>>> duplicate_groups([{'path': 'a', 'size': 10, 'sha256': 'a' * 64},
...                   {'path': 'b', 'size': 10, 'sha256': 'a' * 64}])
[['a', 'b']]

No filesystem I/O — pure in-memory validation and reporting.
"""
import json
import re
import sys
from collections import defaultdict


def _validate_entry(entry):
    """Validate a single catalog entry dict. Returns the validated dict or raises ValueError."""
    if not isinstance(entry, dict):
        raise ValueError("entry must be a dict")

    required_keys = {"path", "size", "sha256"}
    if set(entry.keys()) != required_keys:
        raise ValueError("entry must have exactly keys: path, size, sha256")

    path = entry["path"]
    size = entry["size"]
    sha256 = entry["sha256"]

    # --- path validation ---
    if not isinstance(path, str):
        raise ValueError("path must be a string")
    if not path:
        raise ValueError("path must be non-empty")
    if "\\" in path:
        raise ValueError("path must not contain backslash")
    if ":" in path:
        raise ValueError("path must not contain colon")
    if path.startswith("/"):
        raise ValueError("path must not have leading slash")
    if "\x00" in path or "\n" in path:
        raise ValueError("path must not contain NUL or newline")
    parts = path.split("/")
    for part in parts:
        if part == "" or part == "." or part == "..":
            raise ValueError("path must not have empty, . or .. component")

    # --- size validation ---
    if isinstance(size, bool) or not isinstance(size, int):
        raise ValueError("size must be an integer (bool forbidden)")
    if size < 0:
        raise ValueError("size must be >= 0")

    # --- sha256 validation ---
    if not isinstance(sha256, str):
        raise ValueError("sha256 must be a string")
    if len(sha256) != 64:
        raise ValueError("sha256 must be exactly 64 characters")
    if not re.fullmatch(r"[0-9a-f]{64}", sha256):
        raise ValueError("sha256 must be lowercase hex")

    return {"path": path, "size": size, "sha256": sha256}


def catalog(entries):
    """Validate and sort catalog entries. Returns a new list sorted by path."""
    if not isinstance(entries, list):
        raise ValueError("entries must be a list")

    validated = []
    seen_paths = set()
    for entry in entries:
        record = _validate_entry(entry)
        if record["path"] in seen_paths:
            raise ValueError(f"duplicate path: {record['path']}")
        seen_paths.add(record["path"])
        validated.append(record)

    return sorted(validated, key=lambda e: e["path"])


def duplicate_groups(entries):
    """Return lists of paths sharing the same (size, sha256), sorted groups."""
    validated = catalog(entries)

    buckets = defaultdict(list)
    for record in validated:
        key = (record["size"], record["sha256"])
        buckets[key].append(record["path"])

    groups = sorted([paths for paths in buckets.values() if len(paths) >= 2])
    return groups


def _cli_main():
    """CLI entry point: read JSON array from stdin, output catalog + duplicates."""
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Invalid JSON input: {exc}", file=sys.stderr)
        sys.exit(2)

    try:
        validated = catalog(data)
        dups = duplicate_groups(data)
        result = {"catalog": validated, "duplicates": dups}
        print(json.dumps(result, ensure_ascii=False))
    except ValueError as exc:
        print(f"Validation error: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    _cli_main()
