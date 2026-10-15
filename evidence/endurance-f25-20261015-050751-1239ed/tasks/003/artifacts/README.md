# catalog

Portable file catalog validator and duplicate reporter. Pure Python — no filesystem I/O.

## module.py API

### `catalog(entries)`

Validates a list of file entries and returns them sorted by `path`.

**Input**: `entries` — list of `dict` with exactly three keys: `path` (str), `size` (int >= 0, bool forbidden), `sha256` (64-char lowercase hex string).

**Returns**: A new list of validated dicts sorted by `path`.

**Raises**: `ValueError` on malformed entries, invalid paths, duplicate paths, or extra/missing keys.

**Path rules**: Non-empty POSIX relative path. No backslash, colon, leading `/`, empty component, `.` or `..` component. NUL and newline characters are forbidden. Unicode is allowed.

**Size rules**: Integer >= 0. Python `bool` is explicitly forbidden even though `bool` is a subclass of `int`.

**sha256 rules**: Exactly 64 lowercase hexadecimal characters (`[0-9a-f]`).

### `duplicate_groups(entries)`

Returns groups of entries sharing the same `(size, sha256)` tuple.

**Returns**: List of lists of `path` strings. Each group is sorted lexicographically. Only groups of length >= 2 are included. Groups themselves are sorted lexicographically by their first element.

### CLI

```bash
echo '[{"path":"a","size":10,"sha256":"aaa..."}]' | python module.py
```

Reads a JSON array from stdin, outputs `{"catalog": ..., "duplicates": ...}` to stdout (`ensure_ascii=False`). On invalid input (bad JSON or validation error), exits with code 2 and prints a concise error to stderr (no traceback).

## No filesystem I/O

All validation and reporting is performed in-memory. No file reads, writes, or filesystem probes are performed by this module.

## Examples

```python
from module import catalog, duplicate_groups

# Valid catalog
entries = [
    {"path": "b.txt", "size": 100, "sha256": "a" * 64},
    {"path": "a.txt", "size": 100, "sha256": "a" * 64},
    {"path": "c.txt", "size": 200, "sha256": "b" * 64},
]
sorted_catalog = catalog(entries)
# Returns: [entry("a.txt"), entry("b.txt"), entry("c.txt")]

dups = duplicate_groups(entries)
# Returns: [["a.txt", "b.txt"]] — same size and hash

# Unicode paths are supported
catalog([{"path": "ñ/b.txt", "size": 50, "sha256": "c" * 64}])
# Returns: [{"path": "ñ/b.txt", ...}]

# Invalid paths raise ValueError
catalog([{"path": "", "size": 0, "sha256": "a" * 64}])   # empty path
catalog([{"path": "../x", "size": 0, "sha256": "a" * 64}])  # .. component
catalog([{"path": "a\\b", "size": 0, "sha256": "a" * 64}]) # backslash
catalog([{"path": "C:x", "size": 0, "sha256": "a" * 64}])  # colon

# Bool size is forbidden
catalog([{"path": "x", "size": True, "sha256": "a" * 64}])  # ValueError
```
