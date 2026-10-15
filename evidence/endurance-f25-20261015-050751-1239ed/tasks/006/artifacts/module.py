"""Portable file-catalog validator and duplicate reporter (no filesystem I/O).

Contract
--------
catalog(entries)
    Accepts a list of dicts with exactly the keys ``path``, ``size``, ``sha256``.
    Validates every field strictly; raises ``ValueError`` on:
      - ``path``: must be a non-empty POSIX-relative string containing no
        backslash, colon, leading slash, empty component (``//``), ``.``,
        ``..``, NUL, or newline. Unicode is allowed.
      - ``size``: must be an ``int`` >= 0 (``bool`` is rejected).
      - ``sha256``: must be exactly 64 lowercase hex characters.
      - Duplicate ``path`` values across entries.
      - Wrong type, extra keys, or missing keys.
    Returns a **new** list of dicts sorted by ``path`` (never mutates input).

duplicate_groups(entries)
    Consumes *validated* catalog entries (or calls ``catalog`` internally).
    Groups entries by the composite key ``(size, sha256)`` and returns a list
    of lists of paths where each group has **at least 2 members**.  Paths
    inside each group and the groups themselves are sorted
    lexicographically.  Groups with a single entry are dropped.

CLI
---
python module.py < input.json
    Reads a JSON array of entries from stdin, prints
    ``{"catalog": [...], "duplicates": [...]}`` (``ensure_ascii=False``) to
    stdout.  Returns exit code 0 on success and exit code 2 with a concise
    error message on stderr for invalid input.

Unicode — example
    ``{"path": "café/naïve.txt", "size": 10, "sha256": "a" * 64}`` is valid.

No filesystem I/O — the module never imports ``os``, ``pathlib``, or performs
disk/network operations.
"""

import copy
import hashlib
import json
import sys

# ---------------------------------------------------------------------------
# Internal validators
# ---------------------------------------------------------------------------

_HEX = set('0123456789abcdef')


def _validate_path(path, index):
    """Return *path* if valid; raise ``ValueError`` otherwise."""
    if not isinstance(path, str):
        raise ValueError(f'entry[{index}][\"path\"]: must be str')
    if '\x00' in path or '\n' in path:
        raise ValueError(f'entry[{index}][\"path\"]: NUL/newline forbidden')
    if not path:
        raise ValueError(f'entry[{index}][\"path\"]: must be non-empty')
    if path[0] == '/':
        raise ValueError(f'entry[{index}][\"path\"]: no leading slash')
    if '\\' in path:
        raise ValueError(f'entry[{index}][\"path\"]: no backslash')
    if ':' in path:
        raise ValueError(f'entry[{index}][\"path\"]: no colon')
    parts = path.split('/')
    for p in parts:
        if p == '' or p == '.' or p == '..':
            raise ValueError(
                f'entry[{index}][\"path\"]: empty/./.. component forbidden'
            )
    return path


def _validate_size(size, index):
    """Return *size* if valid; raise ``ValueError`` otherwise."""
    if isinstance(size, bool) or not isinstance(size, int):
        raise ValueError(f'entry[{index}][\"size\"]: int>=0 required, bool forbidden')
    if size < 0:
        raise ValueError(f'entry[{index}][\"size\"]: must be >= 0')
    return size


def _validate_sha256(h, index):
    """Return *h* if valid; raise ``ValueError`` otherwise."""
    if not isinstance(h, str) or len(h) != 64:
        raise ValueError(f'entry[{index}]["sha256"]: exactly 64 hex chars')
    if not set(h).issubset(_HEX):
        raise ValueError(f'entry[{index}]["sha256"]: lowercase hex only')
    return h


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def catalog(entries):
    """Validate and return a **new** sorted list of entry dicts."""
    if not isinstance(entries, (list, tuple)):
        raise ValueError('entries must be a list')

    seen_paths = set()
    result = []

    for i, raw in enumerate(entries):
        if not isinstance(raw, dict):
            raise ValueError(f'entry[{i}]: must be a dict')
        if set(raw.keys()) != {'path', 'size', 'sha256'}:
            raise ValueError(
                f'entry[{i}]: must have exactly keys path,size,sha256'
            )

        p = _validate_path(raw['path'], i)
        s = _validate_size(raw['size'], i)
        h = _validate_sha256(raw['sha256'], i)

        if p in seen_paths:
            raise ValueError(f'entry[{i}]: duplicate path {p!r}')
        seen_paths.add(p)

        result.append({'path': p, 'size': s, 'sha256': h})

    result.sort(key=lambda e: e['path'])
    return result


def duplicate_groups(entries):
    """Return sorted groups of duplicate paths (same size+sha256, >=2)."""
    validated = catalog(entries)

    buckets = {}
    for e in validated:
        buckets.setdefault((e['size'], e['sha256']), []).append(e['path'])

    groups = sorted(
        sorted(paths) for paths in buckets.values() if len(paths) >= 2
    )
    return groups


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
        cat = catalog(data)
        dups = duplicate_groups(data)
        print(json.dumps({'catalog': cat, 'duplicates': dups}, ensure_ascii=False))
    except (json.JSONDecodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
