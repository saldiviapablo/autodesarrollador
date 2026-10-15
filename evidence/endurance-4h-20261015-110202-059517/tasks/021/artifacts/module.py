"""Portable file catalog validator and duplicate grouper.

Contract
--------
catalog(entries)
    Parameters
        entries: list of dict – each dict MUST have exactly the three keys
                 ``path`` (str), ``size`` (int ≥ 0, not bool),
                 ``sha256`` (str, exactly 64 lowercase hex chars).

    Validation rules
        * path – non-empty POSIX relative path:
            - no backslash ``\\``
            - no colon ``:`` anywhere
            - no leading slash ``/``
            - no empty component (no ``//`` and no trailing ``/``)
            - no ``.`` or ``..`` component (split on ``/``)
            - no NUL (``\\x00``) or newline (``\\n``) characters
            - Unicode code points are allowed
        * size – Python ``int`` and ``not bool``, ``size >= 0``
        * sha256 – exactly 64 lowercase hex characters ``[0-9a-f]{64}``
        * No duplicate ``path`` values allowed.
        * Malformed or duplicate entries raise ``ValueError``.

    Returns
        A **new** list of dicts sorted by ``path`` (lexicographic Unicode
        ordering).  Input list and dicts are never mutated.

    No filesystem access.

duplicate_groups(entries)
    Parameters
        entries: list of dict – same format accepted by ``catalog()``.

    Returns
        A list of groups (each a sorted list of ``path`` strings) where
        paths share the same ``(size, sha256)`` tuple.  Only groups with
        ≥ 2 members are returned.  Groups themselves are sorted
        lexicographically by their first path element.

    No filesystem access.

CLI
---
  echo '[{"path":"a","size":1,"sha256":"aa..."}]' | python module.py
  → {"catalog": [...], "duplicates": [...]}

  Exit 0 on success, exit 2 on invalid JSON / malformed entries.
"""

import sys
import copy
import json
import re
from pathlib import PurePosixPath

_HEX64 = re.compile(r'^[0-9a-f]{64}$')


def _validate_entry(rec: dict) -> dict:
    """Return a fresh copy of *rec* after strict validation."""
    if not isinstance(rec, dict):
        raise ValueError(f'entry must be a dict, got {type(rec).__name__}')

    expected_keys = {'path', 'size', 'sha256'}
    if set(rec.keys()) != expected_keys:
        raise ValueError(
            f'entry must have exactly keys {sorted(expected_keys)}, '
            f'got {sorted(rec.keys())}'
        )

    # --- path ---------------------------------------------------------------
    path = rec['path']
    if not isinstance(path, str):
        raise ValueError(f'path must be str, got {type(path).__name__}')
    if '\x00' in path or '\n' in path:
        raise ValueError('path must not contain NUL or newline')
    if not path:
        raise ValueError('path must be non-empty')
    if '\\' in path:
        raise ValueError('path must not contain backslash')
    if ':' in path:
        raise ValueError('path must not contain colon')
    if path.startswith('/'):
        raise ValueError('path must not start with /')
    if path.endswith('/'):
        raise ValueError('path must not end with /')
    if '//' in path:
        raise ValueError('path must not contain empty component (//)')

    parts = path.split('/')
    for part in parts:
        if part in ('.', '..'):
            raise ValueError(f'path component {part!r} is . or ..')

    # --- size ---------------------------------------------------------------
    size = rec['size']
    if isinstance(size, bool) or not isinstance(size, int):
        raise ValueError(f'size must be int, got {type(size).__name__}')
    if size < 0:
        raise ValueError(f'size must be >= 0, got {size}')

    # --- sha256 -------------------------------------------------------------
    h = rec['sha256']
    if not isinstance(h, str):
        raise ValueError(f'sha256 must be str, got {type(h).__name__}')
    if not _HEX64.match(h):
        raise ValueError(
            f'sha256 must be exactly 64 lowercase hex chars, '
            f'got {h!r}'
        )

    return {'path': path, 'size': size, 'sha256': h}


def catalog(entries):
    """Validate entries and return a new sorted list of clean dicts."""
    if not isinstance(entries, list):
        raise ValueError('entries must be a list')

    seen_paths: set[str] = set()
    cleaned: list[dict] = []

    for rec in entries:
        clean = _validate_entry(rec)
        if clean['path'] in seen_paths:
            raise ValueError(f'duplicate path: {clean["path"]!r}')
        seen_paths.add(clean['path'])
        cleaned.append(clean)

    # Return a **new** list sorted by path – never mutate input.
    return sorted(cleaned, key=lambda d: d['path'])


def duplicate_groups(entries):
    """Return sorted groups of paths sharing the same (size, sha256).

    Only groups with ≥ 2 members are returned.  Each group is sorted
    lexicographically.  Groups themselves are sorted by their first path
    element.
    """
    validated = catalog(entries)

    buckets: dict[tuple[int, str], list[str]] = {}
    for rec in validated:
        key = (rec['size'], rec['sha256'])
        buckets.setdefault(key, []).append(rec['path'])

    groups = [sorted(paths) for paths in buckets.values() if len(paths) >= 2]
    groups.sort(key=lambda g: g[0])
    return groups


# ── CLI entry point ──────────────────────────────────────────────────────────
if __name__ == '__main__':
    try:
        raw = sys.stdin.read()
        entries = json.loads(raw)
        catalog_out = catalog(entries)
        dupes = duplicate_groups(entries)
        output = json.dumps(
            {'catalog': catalog_out, 'duplicates': dupes},
            ensure_ascii=False,
            indent=2,
        )
        sys.stdout.write(output)
        sys.stdout.write('\n')
        sys.exit(0)
    except (json.JSONDecodeError, ValueError) as exc:
        sys.stderr.write(f'error: {exc}\n')
        sys.exit(2)
