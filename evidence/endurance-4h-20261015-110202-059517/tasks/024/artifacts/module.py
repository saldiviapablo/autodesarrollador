"""Portable file catalog validator and duplicate detector.

No filesystem I/O is performed. All operations work on in-memory data only.

Contract
--------
catalog(entries) validates a list of entry dicts with exactly the keys
``path`` (str), ``size`` (int >= 0, bool forbidden), ``sha256`` (64 lowercase hex).
Path rules: POSIX relative — no backslash, colon, leading slash, empty component,
``.``, ``..``, NUL, or newline. Unicode is allowed (e.g. ``ñ``, ``汉字``).
Raises ``ValueError`` on malformed entries or duplicate paths.
Returns a **new** list of dicts sorted by path; the input list is never mutated.

duplicate_groups(entries) calls ``catalog`` to validate, then groups entries by
the ``(size, sha256)`` pair. Returns a list of path-lists for groups with >= 2
members; paths within each group are sorted lexicographically, and groups are
sorted lexicographically as well.

CLI
---
``python module.py`` reads a JSON array from stdin and writes a JSON object
``{"catalog": [...], "duplicates": [...]}`` to stdout (``ensure_ascii=False``).
On invalid input the process exits with code 2 and prints a concise error to
stderr (no ``Traceback``).
"""

import sys
import json
import copy
import re
import collections

# ---------------------------------------------------------------------------
# Internal validators
# ---------------------------------------------------------------------------

_PATH_RE = re.compile(r'^[^\\\x00\x0a:/][^\\]*$')
_HEX64_RE = re.compile(r'^[0-9a-f]{64}$')


def _validate_path(p: str) -> None:
    """Raise ValueError when *p* violates the portable-POSIX contract."""
    if not isinstance(p, str):
        raise ValueError(f"path must be str, got {type(p).__name__}")
    if not p:
        raise ValueError("path must be nonempty")
    if '\x5c' in p:
        raise ValueError(f"path must not contain backslash, got {p!r}")
    if p.startswith('/'):
        raise ValueError(f"path must be POSIX relative, got {p!r}")
    if ':' in p:
        raise ValueError(f"path must not contain colon, got {p!r}")
    if '\x00' in p or '\n' in p:
        raise ValueError("path must not contain NUL or newline")
    parts = p.split('/')
    for part in parts:
        if part == '' or part == '.' or part == '..':
            raise ValueError(f"bad path component {part!r} in {p!r}")


def _validate_size(s) -> None:
    if isinstance(s, bool) or not isinstance(s, int):
        raise ValueError(f"size must be int>=0, got {type(s).__name__}")
    if s < 0:
        raise ValueError(f"size must be >=0, got {s}")


def _validate_sha256(h: str) -> None:
    if not isinstance(h, str) or not _HEX64_RE.match(h):
        raise ValueError(f"sha256 must be 64 lowercase hex, got {h!r}")


def _validate_entry(e: dict) -> dict:
    """Return a new dict with exactly path, size, sha256 (validated)."""
    if not isinstance(e, dict):
        raise ValueError(f"entry must be dict, got {type(e).__name__}")
    expected = {'path', 'size', 'sha256'}
    if set(e.keys()) != expected:
        raise ValueError(f"entry keys must be {{path,size,sha256}}, got {set(e.keys())}")
    _validate_path(e['path'])
    _validate_size(e['size'])
    _validate_sha256(e['sha256'])
    return {'path': e['path'], 'size': e['size'], 'sha256': e['sha256']}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def catalog(entries):
    """Validate entries and return a new sorted list (input never mutated).

    Parameters
    ----------
    entries : list[dict]
        Each dict has keys ``path``, ``size``, ``sha256``.

    Returns
    -------
    list[dict]
        New list sorted by ``path``.

    Raises
    ------
    ValueError
        On malformed entry, duplicate path, or invalid structure.
    """
    if not isinstance(entries, list):
        raise ValueError("entries must be a list")
    validated = []
    seen_paths: set[str] = set()
    for e in entries:
        rec = _validate_entry(e)
        if rec['path'] in seen_paths:
            raise ValueError(f"duplicate path: {rec['path']!r}")
        seen_paths.add(rec['path'])
        validated.append(rec)
    return sorted(validated, key=lambda x: x['path'])


def duplicate_groups(entries):
    """Return groups of paths sharing the same ``(size, sha256)``.

    Parameters
    ----------
    entries : list[dict]
        Same contract as ``catalog``.

    Returns
    -------
    list[list[str]]
        Each inner list contains >= 2 paths sorted lexicographically.
        Outer list is also sorted lexicographically by the first element.
    """
    validated = catalog(entries)
    buckets: dict[tuple, list[str]] = collections.defaultdict(list)
    for rec in validated:
        buckets[(rec['size'], rec['sha256'])].append(rec['path'])
    groups = sorted((sorted(paths) for paths in buckets.values() if len(paths) >= 2))
    return groups


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def _cli_main():
    """Read JSON array from stdin, write {"catalog": ..., "duplicates": ...} to stdout."""
    try:
        raw = sys.stdin.read()
        entries = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        print("invalid JSON input", file=sys.stderr)
        sys.exit(2)

    if not isinstance(entries, list):
        print("input must be a JSON array", file=sys.stderr)
        sys.exit(2)

    try:
        cat = catalog(entries)
        dups = duplicate_groups(entries)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)

    out = {"catalog": cat, "duplicates": dups}
    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    _cli_main()
