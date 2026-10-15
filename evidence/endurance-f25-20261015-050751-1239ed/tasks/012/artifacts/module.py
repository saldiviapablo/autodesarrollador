"""Portable-file catalog validator and duplicate reporter.

Contract
--------
* ``catalog(entries)`` validates and returns a new list of entry dicts sorted by
  ``path``.  **Never mutates** the input list or its dicts.
* ``duplicate_groups(entries)`` builds on ``catalog`` and returns a list of
  path-groups (each a sorted list of ``str``) sharing the same ``(size, sha256)``.
  Only groups with 2+ members; groups sorted lexicographically by their first path.
* The CLI (``python module.py``) reads a JSON array from *stdin* and writes a JSON
  object ``{"catalog": [...], "duplicates": [...]}`` to *stdout*.  On any
  validation / parsing error it prints a concise message to *stderr* and exits
  with code 2.

Path rules (portable POSIX relative)
------------------------------------
* Non-empty string.
* No backslash ``\\``, colon ``:``, leading or trailing ``/``, empty components
  (``//``), or ``.`` / ``..`` components.
* No NUL or newline characters.
* Unicode is allowed (e.g. ``ñ``, ``中文``, ``📁``).

Size rules
----------
* Integer ``>= 0``.  Booleans are rejected even though ``bool`` is a subclass of
  ``int`` in Python.

sha256 rules
------------
* Exactly 64 lowercase hexadecimal characters.

Examples
--------
>>> catalog([{'path': 'z', 'size': 1, 'sha256': 'a' * 64},
...          {'path': 'a', 'size': 1, 'sha256': 'a' * 64}])
[{'path': 'a', 'size': 1, 'sha256': 'a' * 64},
 {'path': 'z', 'size': 1, 'sha256': 'a' * 64}]

>>> duplicate_groups([{'path': 'b', 'size': 2, 'sha256': 'a' * 64},
...                   {'path': 'a', 'size': 2, 'sha256': 'a' * 64},
...                   {'path': 'c', 'size': 1, 'sha256': 'a' * 64}])
[['a', 'b']]

No filesystem I/O
-----------------
All validation and sorting happens in-memory on the provided data structures
only.
"""
import json
import re
import sys

# Pre-compiled regex for sha256 validation
_RE_SHA256 = re.compile(r'^[0-9a-f]{64}$')


# ---- helpers ----------------------------------------------------------------

def _validate_path(path):
    """Raise ValueError if *path* is not a valid portable POSIX relative path."""
    if not isinstance(path, str) or not path:
        raise ValueError("path must be a non-empty string")
    if '\\' in path or '\x00' in path or '\n' in path:
        raise ValueError("path must not contain backslash, NUL, or newline")
    if ':' in path:
        raise ValueError("path must not contain colon")
    if path.startswith('/'):
        raise ValueError("path must not have a leading slash")
    parts = path.split('/')
    if any(p == '' or p == '.' or p == '..' for p in parts):
        raise ValueError("path must not have empty, '.', or '..' components")


def _validate_size(size):
    """Raise ValueError if *size* is not a valid integer >= 0."""
    if isinstance(size, bool) or not isinstance(size, int):
        raise ValueError("size must be an integer >= 0 (bool forbidden)")
    if size < 0:
        raise ValueError("size must be >= 0")


def _validate_sha256(sha256):
    """Raise ValueError if *sha256* is not exactly 64 lowercase hex chars."""
    if not isinstance(sha256, str) or not _RE_SHA256.match(sha256):
        raise ValueError("sha256 must be exactly 64 lowercase hex characters")


def _validate_entry(entry):
    """Raise ValueError if *entry* is not a well-formed catalog record."""
    if not isinstance(entry, dict):
        raise ValueError("each entry must be a dict")
    if set(entry.keys()) != {'path', 'size', 'sha256'}:
        raise ValueError("entry must have exactly keys: path, size, sha256")
    _validate_path(entry['path'])
    _validate_size(entry['size'])
    _validate_sha256(entry['sha256'])


# ---- public API -------------------------------------------------------------

def catalog(entries):
    """Validate and return a **new** list of entry dicts sorted by *path*.

    Parameters
    ----------
    entries : list[dict]
        Each dict must have exactly ``{path: str, size: int, sha256: str}``.

    Returns
    -------
    list[dict]
        A fresh list sorted by ``path``.  Original list and dicts are never
        mutated.

    Raises
    ------
    ValueError
        On any malformed entry, duplicate path, or if *entries* is not a list.
    """
    if not isinstance(entries, list):
        raise ValueError("entries must be a list")

    seen_paths = set()
    result = []
    for entry in entries:
        _validate_entry(entry)
        path = entry['path']
        if path in seen_paths:
            raise ValueError(f"duplicate path: {path}")
        seen_paths.add(path)
        # Build a fresh dict so we never mutate the caller's object
        result.append({'path': path, 'size': entry['size'], 'sha256': entry['sha256']})

    result.sort(key=lambda e: e['path'])
    return result


def duplicate_groups(entries):
    """Return groups of paths sharing the same *(size, sha256)*.

    Groups contain 2+ members, each group's paths are sorted, and groups are
    sorted lexicographically by their first path.  Uses ``catalog`` internally
    for validation.

    Returns
    -------
    list[list[str]]
    """
    validated = catalog(entries)
    groups = {}
    for entry in validated:
        key = (entry['size'], entry['sha256'])
        groups.setdefault(key, []).append(entry['path'])

    result = [sorted(paths) for paths in groups.values() if len(paths) >= 2]
    result.sort(key=lambda g: g[0])
    return result


# ---- CLI entry-point --------------------------------------------------------

if __name__ == '__main__':
    try:
        data = json.loads(sys.stdin.read())
        cat = catalog(data)
        dups = duplicate_groups(data)
        print(json.dumps({"catalog": cat, "duplicates": dups}, ensure_ascii=False))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
