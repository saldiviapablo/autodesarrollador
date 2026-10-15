# catalog

Portable file catalog validator and duplicate reporter.  Works entirely in
memory — **no filesystem access**.

## API

### `catalog(entries)`

Validate a list of file-entry dicts and return a **new** list sorted by
`path`.

**Entry shape** — exactly three keys:

| Key      | Type           | Constraints                                              |
|----------|----------------|----------------------------------------------------------|
| `path`   | `str`          | Non-empty POSIX relative path; no `\ : / .` .. NUL newline |
| `size`   | `int >= 0`     | Boolean values are explicitly rejected                     |
| `sha256` | `str` (64 hex) | Exactly 64 lowercase hexadecimal characters                |

Raises `ValueError` on any malformed entry, duplicate path, or if `entries` is
not a list.

**Example**

```python
from module import catalog

entries = [
    {"path": "z.txt", "size": 100, "sha256": "a" * 64},
    {"path": "a.txt", "size": 200, "sha256": "b" * 64},
]
result = catalog(entries)          # sorted by path, input untouched
assert result[0]["path"] == "a.txt"
```

### `duplicate_groups(entries)`

Identify files that share the same `(size, sha256)` signature.

Returns a list of path-groups (each a sorted `list[str]`), only groups with 2+
members, sorted lexicographically.

**Example**

```python
from module import duplicate_groups

entries = [
    {"path": "b", "size": 10, "sha256": "aa" * 32},
    {"path": "a", "size": 10, "sha256": "aa" * 32},
    {"path": "c", "size": 20, "sha256": "bb" * 32},
]
groups = duplicate_groups(entries)
assert groups == [["a", "b"]]       # only b and a share (10, aa…)
```

## Unicode

Paths may contain any Unicode code points (e.g. `ñ`, `中文`, `📁`).  Sorting
follows standard Python lexicographic order (Unicode code-point order).

## CLI usage

```bash
echo '[{"path":"a.txt","size":42,"sha256":"a"*64}]' | python module.py
# → {"catalog": [{"path": "a.txt", "size": 42, "sha256": "..."}], "duplicates": []}
```

* Invalid / unparseable input → **exit code 2** + concise *stderr* message (no
  Python traceback).
* Output uses `ensure_ascii=False` so Unicode paths are preserved verbatim.

## No filesystem

All validation and sorting are performed on the in-memory data structures only.
No file reads, writes, or os-level calls are made inside `module.py`.

## Testing & build

```bash
python test_module.py   # unit + acceptance tests
python build.py         # AST parse check
```

Both must exit with code 0.
