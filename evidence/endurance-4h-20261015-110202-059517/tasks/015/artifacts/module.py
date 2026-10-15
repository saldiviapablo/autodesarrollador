"""Portable file catalog validator and duplicate reporter.

Contract
--------
* ``catalog(entries)`` expects a list of dicts with exactly three keys:
  ``path`` (str), ``size`` (int >= 0, bool forbidden), ``sha256`` (str).
* ``path`` must be a portable POSIX relative path:
  - non-empty, no NUL/newline/backslash/colon
  - no leading ``/``, no ``.``, ``..`` or empty components (``//``).
  - Unicode code-points are allowed.
* ``sha256`` must be exactly 64 lowercase hex characters.
* Duplicate paths (same string) raise ``ValueError``.
* Returns a **new** list of validated dicts sorted by ``path``;
  the input list is never mutated and no filesystem access occurs.

* ``duplicate_groups(entries)`` uses the validated catalog to produce a
  list of groups (each group is a sorted list of paths) where every entry
  shares the same ``(size, sha256)`` tuple.  Only groups of size >= 2 are
  returned; groups themselves are sorted lexicographically by their first
  path.

No filesystem I/O — all work is done in-memory on the provided data.

Examples
--------
>>> catalog([
...     {'path': 'b.txt', 'size': 10, 'sha256': 'a' * 64},
...     {'path': 'a.txt', 'size': 5,  'sha256': 'b' * 64},
... ])
[{'path': 'a.txt', 'size': 5, 'sha256': 'b' * 64},
 {'path': 'b.txt', 'size': 10, 'sha256': 'a' * 64}]

>>> duplicate_groups([
...     {'path': 'x', 'size': 10, 'sha256': 'a' * 64},
...     {'path': 'y', 'size': 10, 'sha256': 'a' * 64},
...     {'path': 'z', 'size': 10, 'sha256': 'b' * 64},
... ])
[['x', 'y']]
"""

import collections
import hashlib
import json
import sys

# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_HEX_CHARS = frozenset('0123456789abcdef')


def _validate_path(value: object) -> str:
    """Return *value* if it is a valid portable POSIX relative path."""
    if not isinstance(value, str):
        raise ValueError(f"path must be str, got {type(value).__name__}")
    if not value:
        raise ValueError("path must be non-empty")
    if '\x00' in value or '\n' in value:
        raise ValueError("path must not contain NUL or newline")
    if '\\' in value or ':' in value:
        raise ValueError("path must not contain backslash or colon")
    if value.startswith('/'):
        raise ValueError("path must not start with /")
    parts = value.split('/')
    for part in parts:
        if not part or part == '.' or part == '..':
            raise ValueError(
                f"path component {part!r} is empty, . or .."
            )
    return value


def _validate_size(value: object) -> int:
    """Return *value* if it is a valid size (int >= 0, bool excluded)."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"size must be int >= 0, got {type(value).__name__}")
    if value < 0:
        raise ValueError(f"size must be >= 0, got {value}")
    return value


def _validate_sha256(value: object) -> str:
    """Return *value* if it is a valid 64-char lowercase hex string."""
    if not isinstance(value, str):
        raise ValueError(f"sha256 must be str, got {type(value).__name__}")
    if len(value) != 64:
        raise ValueError("sha256 must be exactly 64 characters")
    if not all(c in _HEX_CHARS for c in value):
        raise ValueError("sha256 must contain only lowercase hex chars")
    return value


_REQUIRED_KEYS = frozenset({'path', 'size', 'sha256'})


def _validate_entry(record: object) -> dict:
    """Validate a single catalog entry dict; return a *copy*."""
    if not isinstance(record, dict):
        raise ValueError(f"entry must be dict, got {type(record).__name__}")
    if set(record.keys()) != _REQUIRED_KEYS:
        raise ValueError(
            f"entry must have exactly keys {sorted(_REQUIRED_KEYS)}, "
            f"got {sorted(record.keys())}"
        )
    return {
        'path': _validate_path(record['path']),
        'size': _validate_size(record['size']),
        'sha256': _validate_sha256(record['sha256']),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def catalog(entries: list) -> list:
    """Validate and return a new sorted list of entry dicts.

    Raises ``ValueError`` on any malformed entry or duplicate path.
    """
    if not isinstance(entries, list):
        raise ValueError(f"entries must be list, got {type(entries).__name__}")

    seen_paths: set[str] = set()
    result: list[dict] = []

    for record in entries:
        validated = _validate_entry(record)
        p = validated['path']
        if p in seen_paths:
            raise ValueError(f"duplicate path: {p!r}")
        seen_paths.add(p)
        result.append(validated)

    result.sort(key=lambda e: e['path'])
    return result


def duplicate_groups(entries: list) -> list:
    """Return groups of duplicate paths (same size + sha256), sorted.

    Groups are sorted lexicographically (by first path).  Each group is a
    sorted list of paths containing >= 2 entries.
    """
    validated = catalog(entries)

    buckets: dict[tuple[int, str], list[str]] = collections.defaultdict(list)
    for rec in validated:
        buckets[(rec['size'], rec['sha256'])].append(rec['path'])

    groups = sorted(paths for paths in buckets.values() if len(paths) >= 2)
    return groups


# ---------------------------------------------------------------------------
# CLI  (python module.py)
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
        cat = catalog(data)
        dups = duplicate_groups(data)
        print(json.dumps({'catalog': cat, 'duplicates': dups}, ensure_ascii=False))
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
