# catalog — Portable File Catalog Validator

Validate a portable file catalog and report duplicates without filesystem access.

## Overview

`module.py` provides two public functions that operate entirely in-memory:

| Function | Purpose |
|---|---|
| `catalog(entries)` | Validate and sort a list of file-entry dicts |
| `duplicate_groups(entries)` | Return groups of paths sharing `(size, sha256)` |

No filesystem I/O — all validation and grouping is performed on the supplied data structures only.

## API

### `catalog(entries: list) -> list`

Accepts a list of dicts with exactly three keys: `path`, `size`, `sha256`.

**Path contract** — must be a portable POSIX relative path:
- Non-empty string.
- No NUL (`\x00`), newline (`\n`), backslash (`\`), or colon (`:`).
- No leading `/`, no `.` or `..` components, no empty components (`//`).
- Unicode code-points are allowed (e.g. `ñ`, `é`, `中文`).

**Size contract** — integer ≥ 0. Booleans are explicitly rejected (`isinstance(True, int)` → `ValueError`).

**SHA-256 contract** — exactly 64 lowercase hex characters (`[0-9a-f]`).

Returns a **new** list of validated dicts sorted by `path`. The input list is never mutated.

Raises `ValueError` on any malformed entry or duplicate path.

### `duplicate_groups(entries: list) -> list`

Uses `catalog()` internally to validate the entries, then groups paths by their `(size, sha256)` tuple.

Returns a list of groups (each group is a sorted list of paths) where every entry shares the same `(size, sha256)`. Only groups of size ≥ 2 are returned. Groups themselves are sorted lexicographically by their first path.

Returns an empty list `[]` when no duplicates exist.

## CLI usage

```bash
# Valid input — JSON array on stdin, JSON object on stdout
echo '[{"path":"a.txt","size":10,"sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
      {"path":"b.txt","size":10,"sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}]' \
  | python module.py

# Output
{"catalog":[{"path":"a.txt","size":10,"sha256":"a...a"},{"path":"b.txt","size":10,"sha256":"a...a"}],"duplicates":[["a.txt","b.txt"]]}
```

Exit code `0` on success, exit code `2` on invalid input (concise error on stderr, no traceback).

## Unicode examples

```python
# Unicode paths are fully supported
catalog([
    {'path': 'café.txt', 'size': 42, 'sha256': 'b' * 64},
    {'path': 'αβγ.txt',  'size': 10, 'sha256': 'a' * 64},
])
# → sorted by Unicode code-point order

duplicate_groups([
    {'path': '文件1', 'size': 100, 'sha256': 'c' * 64},
    {'path': '文件2', 'size': 100, 'sha256': 'c' * 64},
])
# → [['文件1', '文件2']]
```

## No filesystem I/O

All operations work exclusively on the in-memory data structures provided as arguments. No file reads, writes, or os-level calls occur during validation or duplicate detection.

## Invalid path examples

| Path | Reason |
|---|---|
| `''` | Empty |
| `/x` | Leading slash |
| `../x` | `..` component |
| `a/../b` | `..` component |
| `./a` | `.` component |
| `a//b` | Empty component |
| `a/` | Trailing slash → empty component |
| `C:x` | Colon |
| `a\\b` | Backslash |
| `a\x00b` | NUL byte |
| `a\nb` | Newline |

## Invalid record examples

| Record | Reason |
|---|---|
| `[entry('x', True)]` | Bool not int |
| `[entry('x', -1)]` | Negative size |
| `[entry('x', 1.5)]` | Float not int |
| `[entry('x', 1, 'A'*64)]` | Uppercase hex |
| `[entry('x', 1, 'a'*63)]` | Wrong length |
| `[entry('x'), entry('x')]` | Duplicate path |
| `[dict(entry('x'), extra=1)]` | Extra key |

## Running tests

```bash
python test_module.py
python build.py
```

Both should exit with code 0.
