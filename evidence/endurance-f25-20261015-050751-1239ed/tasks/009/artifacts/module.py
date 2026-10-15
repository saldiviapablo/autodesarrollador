"""Validate a portable file catalog and report duplicates — no filesystem I/O.

Contract
--------
``catalog(entries)``
    *entries* is a list of dicts with **exactly** three keys: ``path``, ``size``,
    ``sha256``.

    ``path`` — non-empty POSIX relative path:
      * No backslashes, colons, leading slash, NUL, or newline.
      * No empty components (``a//b``), no ``.`` or ``..`` segments.
      * Unicode is allowed (e.g. ``ñ``, ``日本語``).

    ``size`` — integer ``>= 0``; ``bool`` is **forbidden** (``bool`` is a
    subclass of ``int`` in Python and must be explicitly rejected).

    ``sha256`` — exactly 64 lowercase hex characters.

    Raises ``ValueError`` on any malformed entry, unknown keys, or duplicate
    paths.

    Returns a **new** list of dicts sorted by ``path`` (ascending, lexicographic
    Unicode-aware). The input list and its dicts are **never mutated**.

``duplicate_groups(entries)``
    Validates *entries* through :func:`catalog` internally, then returns a list
    of groups — each group is a **new** sorted list of ``path`` strings — where
    all entries share the same ``(size, sha256)`` tuple.  Only groups of size
    ``>= 2`` appear.  Groups themselves are sorted lexicographically by their
    first element.

    Returns ``[]`` when there are no duplicates.

CLI
---
Run ``python module.py`` and pipe a JSON array to stdin.  Outputs
``{"catalog": ..., "duplicates": ...}`` (``ensure_ascii=False``) to stdout.
Invalid input → exit code 2 with a concise message to stderr.

Examples
--------
>>> catalog([{'path': 'ñ/b.txt', 'size': 10, 'sha256': 'a' * 64},
...          {'path': 'a.txt',       'size': 5,  'sha256': 'b' * 64}])
[{'path': 'a.txt', ...}, {'path': 'ñ/b.txt', ...}]

>>> duplicate_groups([{'path': 'z', 'size': 1, 'sha256': 'a' * 64},
...                   {'path': 'a', 'size': 1, 'sha256': 'a' * 64},
...                   {'path': 'b', 'size': 2, 'sha256': 'b' * 64},
...                   {'path': 'c', 'size': 2, 'sha256': 'b' * 64}])
[['a', 'z'], ['b', 'c']]
"""

import copy
import hashlib
import json
import re
import sys
from collections import defaultdict

_ALLOWED_KEYS = frozenset({"path", "size", "sha256"})
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


# ---- internal helpers -----------------------------------------------------

def _validate_path(path):
    """Raise ValueError if *path* is not a valid portable POSIX relative path."""
    if not isinstance(path, str):
        raise ValueError("path must be a string")
    if not path:
        raise ValueError("path must be non-empty")
    # Forbidden characters
    if "\x00" in path or "\n" in path:
        raise ValueError("path contains forbidden characters (NUL / newline)")
    if "\\" in path or ":" in path or path.startswith("/"):
        raise ValueError("path must be a relative POSIX path (no backslash, colon, leading slash)")
    if "." in path:
        parts = path.replace("\\", "/").split("/")
        for segment in parts:
            if segment in (".", ".."):
                raise ValueError("path must not contain . or .. components")
    if "//" in path:
        raise ValueError("path contains empty component")
    # Final component cannot end with '/'
    if path.endswith("/"):
        raise ValueError("path component cannot end with '/'")


def _validate_size(size):
    """Raise ValueError if *size* is not a non-negative integer (bool forbidden)."""
    if isinstance(size, bool) or not isinstance(size, int):
        raise ValueError("size must be an integer (bool forbidden)")
    if size < 0:
        raise ValueError("size must be >= 0")


def _validate_sha256(value):
    """Raise ValueError if *value* is not a 64-char lowercase hex string."""
    if not isinstance(value, str) or not _HEX64.match(value):
        raise ValueError("sha256 must be exactly 64 lowercase hex characters")


def _validate_entry(record):
    """Validate a single entry dict. Raises ValueError on any problem."""
    if not isinstance(record, dict):
        raise ValueError("each entry must be a dict")
    keys = set(record.keys())
    if keys != _ALLOWED_KEYS:
        raise ValueError(f"entry must have exactly {sorted(_ALLOWED_KEYS)} keys, got {sorted(keys)}")
    _validate_path(record["path"])
    _validate_size(record["size"])
    _validate_sha256(record["sha256"])


# ---- public API -----------------------------------------------------------

def catalog(entries):
    """Validate and return a new list of entry dicts sorted by path.

    Never mutates the input list or its dicts.
    Raises ``ValueError`` on any malformed entry or duplicate path.
    """
    if not isinstance(entries, (list, tuple)):
        raise ValueError("entries must be a list")

    seen_paths = set()
    validated = []

    for record in entries:
        _validate_entry(record)
        path = record["path"]
        if path in seen_paths:
            raise ValueError(f"duplicate path: {path!r}")
        seen_paths.add(path)
        # Deep-copy to guarantee immutability
        validated.append(copy.deepcopy(record))

    validated.sort(key=lambda r: r["path"])
    return validated


def duplicate_groups(entries):
    """Return duplicate groups from *entries*.

    Validates through :func:`catalog`.  Returns lists of paths sharing the
    same ``(size, sha256)`` — each group sorted, only groups of ``>= 2``,
    groups sorted lexicographically.
    """
    validated = catalog(entries)

    bucket = defaultdict(list)
    for rec in validated:
        bucket[(rec["size"], rec["sha256"])].append(rec["path"])

    groups = sorted(
        sorted(paths)
        for paths in bucket.values()
        if len(paths) >= 2
    )
    return groups


# ---- CLI -------------------------------------------------------------------

def _cli():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"invalid JSON: {exc}", file=sys.stderr)
        sys.exit(2)

    if not isinstance(data, list):
        print("stdin must contain a JSON array", file=sys.stderr)
        sys.exit(2)

    try:
        cat = catalog(data)
        dups = duplicate_groups(data)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)

    out = {"catalog": cat, "duplicates": dups}
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    _cli()
