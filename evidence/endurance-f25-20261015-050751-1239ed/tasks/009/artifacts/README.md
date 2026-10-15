# catalog

Validate a portable file catalog and report duplicates — **no filesystem I/O**.

## API

### `catalog(entries) -> list[dict]`

Validates a list of file-entry dicts and returns a **new** sorted list.

**Entry contract** — each dict must have **exactly** three keys:

| Key | Type | Constraint |
|-----|------|------------|
| `path` | `str` | Non-empty POSIX relative path. No backslash, colon, leading slash, NUL, newline. No empty components (`//`), no `. `or `..` segments. Unicode allowed. |
| `size` | `int` | Integer ``>= 0``. `bool` is forbidden. |
| `sha256` | `str` | Exactly 64 lowercase hex characters. |

Returns a **new** list of deep-copied dicts sorted by `path` (ascending,
lexicographic Unicode-aware). Input is **never mutated**.

**Raises:** `ValueError` on malformed entries, unknown keys, or duplicate paths.

### `duplicate_groups(entries) -> list[list[str]]`

Returns lists of paths that share the same `(size, sha256)` pair.

- Each group is a sorted list of path strings.
- Only groups with ``>= 2`` members appear.
- Groups are sorted lexicographically by their first element.

**Raises:** `ValueError` (same validation as `catalog`).

## Unicode

Paths may contain any Unicode code point allowed by POSIX file names:
``ñ``, ``日本語``, ``émoji 🎉``, etc.  Sorting follows Python's default
lexicographic order (code-point order), which is stable and deterministic.

## CLI

```bash
echo '[{"path":"a.txt","size":10,"sha256":"'"$(python -c 'print("a"*64)"')"'"}]' | python module.py
```

Outputs JSON to stdout:

```json
{
  "catalog": [{"path": "a.txt", "size": 10, "sha256": "aaa..."}],
  "duplicates": []
}
```

Invalid input (bad JSON, malformed entries, duplicate paths) → exit code 2
with a concise message to stderr (no traceback).

## Examples

```python
from module import catalog, duplicate_groups

# Basic validation + sort
entries = [
    {"path": "ñ/b.txt", "size": 10, "sha256": "a" * 64},
    {"path": "a.txt",   "size": 5,  "sha256": "b" * 64},
]
result = catalog(entries)
assert result[0]["path"] == "a.txt"
assert result[1]["path"] == "ñ/b.txt"

# Detect duplicates
dups = duplicate_groups([
    {"path": "z", "size": 1, "sha256": "a" * 64},
    {"path": "a", "size": 1, "sha256": "a" * 64},
    {"path": "b", "size": 2, "sha256": "b" * 64},
    {"path": "c", "size": 2, "sha256": "b" * 64},
])
# [['a', 'z'], ['b', 'c']]

# Reject malformed
try:
    catalog([{"path": "", "size": 0, "sha256": "a" * 64}])
except ValueError as exc:
    print(exc)  # "path must be non-empty"

# Reject bool as size
try:
    catalog([{"path": "x", "size": True, "sha256": "a" * 64}])
except ValueError as exc:
    print(exc)  # "size must be an integer (bool forbidden)"
```

## Testing

```bash
python test_module.py   # unit + acceptance tests
python build.py         # AST-parse sanity check
```

## Design decisions

- **No filesystem access** — all validation is in-memory; the tool works on
  portable data, not local files.
- **Deep-copy output** — callers receive independent dicts; mutations never
  leak between calls.
- **ValueError, not custom exceptions** — keeps the public API minimal and
  Python-idiomatic.
- **Exit 2 on CLI error** — follows POSIX convention for usage/validation errors.
