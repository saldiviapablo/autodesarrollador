"""Portable file catalog validator and duplicate-reporter.

Contract
--------
catalog(entries)
    Validate a list of entry dicts with exactly the keys ``path``, ``size``,
    ``sha256``.  Raises ``ValueError`` on any malformed entry or duplicate
    ``path``.  Returns a **new** list of validated dicts sorted by ``path``,
    never mutating the input and never accessing the filesystem.

duplicate_groups(entries)
    Accept a *validated* catalog (output of ``catalog``).  Returns a list of
    groups, where each group is a sorted list of ``path`` values that share
    the same ``(size, sha256)`` pair.  Only groups with ``>= 2`` members are
    returned.  Groups themselves are sorted lexicographically by their first
    element.

CLI
---
Reads a JSON array of entries from stdin, outputs ``{"catalog": ...,
"duplicates": ...}`` to stdout (``ensure_ascii=False``), and exits 0.  On
any validation error exits 2 with a concise message on stderr.

Unicode
-------
Unicode is fully supported in ``path`` values (e.g. ``ñ``, ``中``, ``📄``)
provided the path obeys the POSIX-relative constraints below.

No filesystem I/O
-----------------
This module performs **zero** filesystem operations.  All validation is
in-memory only.

Examples
--------
>>> catalog([{"path": "z.txt", "size": 10, "sha256": "a"*64}])
[{"path": "z.txt", "size": 10, "sha256": "a"*64}]

>>> duplicate_groups([
...     {"path": "a", "size": 1, "sha256": "b"*64},
...     {"path": "z", "size": 1, "sha256": "b"*64},
... ])
[["a", "z"]]
"""

import copy
import hashlib
import json
import sys


def _validate_path(path):
    """Raise ValueError if *path* violates the portable-POSIX rules."""
    if not isinstance(path, str):
        raise ValueError("path must be a string")
    if '\x00' in path or '\n' in path:
        raise ValueError("path must not contain NUL or newline")
    if '\\' in path:
        raise ValueError("path must not contain backslash")
    if ':' in path:
        raise ValueError("path must not contain colon")
    if path.startswith('/'):
        raise ValueError("path must not start with leading slash")
    if not path:
        raise ValueError("path must be a non-empty string")
    if path in ('.', '..'):
        raise ValueError("path must not be '.' or '..'")
    parts = path.split('/')
    for part in parts:
        if part == '' or part in ('.', '..'):
            raise ValueError(f"empty or dot/dotdot component in path")


_HEX = set('0123456789abcdef')


def _validate_sha256(value):
    """Raise ValueError if *value* is not exactly 64 lowercase-hex chars."""
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError("sha256 must be exactly 64 lowercase hex characters")
    if not all(c in _HEX for c in value):
        raise ValueError("sha256 must be exactly 64 lowercase hex characters")


def _validate_size(value):
    """Raise ValueError unless *value* is an int >= 0 (bool forbidden)."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("size must be an integer >= 0; bool is forbidden")
    if value < 0:
        raise ValueError("size must be an integer >= 0")


def catalog(entries):
    """Validate *entries* and return a new list of dicts sorted by path.

    Raises ``ValueError`` on any malformed entry or duplicate path.
    """
    if not isinstance(entries, (list, tuple)):
        raise ValueError("entries must be a list")

    result = []
    seen_paths = set()

    for idx, item in enumerate(entries):
        if not isinstance(item, dict):
            raise ValueError(f"entry[{idx}] must be a dict")
        if set(item.keys()) != {'path', 'size', 'sha256'}:
            raise ValueError(
                f"entry[{idx}] must have exactly keys path, size, sha256"
            )
        _validate_path(item['path'])
        _validate_size(item['size'])
        _validate_sha256(item['sha256'])
        if item['path'] in seen_paths:
            raise ValueError(f"duplicate path: {item['path']!r}")
        seen_paths.add(item['path'])
        result.append({
            'path': item['path'],
            'size': item['size'],
            'sha256': item['sha256'],
        })

    result.sort(key=lambda d: d['path'])
    return result


def duplicate_groups(entries):
    """Return groups of duplicate paths (same *size* and *sha256*).

    Accepts a *validated* catalog (output of :func:`catalog`).  Returns a
    list of sorted path-lists, each group having ``>= 2`` members, and the
    groups themselves sorted lexicographically.
    """
    buckets = {}
    for item in entries:
        key = (item['size'], item['sha256'])
        buckets.setdefault(key, []).append(item['path'])

    groups = sorted(
        sorted(paths)
        for paths in buckets.values()
        if len(paths) >= 2
    )
    return groups


def _cli():
    """CLI entry-point: read JSON from stdin, write result to stdout."""
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"invalid JSON: {exc}", file=sys.stderr)
        sys.exit(2)

    try:
        cat = catalog(data)
        dupes = duplicate_groups(cat)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)

    print(json.dumps(
        {'catalog': cat, 'duplicates': dupes},
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == '__main__':
    _cli()
