# catalog — Portable File Catalog Validator & Duplicate Detector

A pure-Python utility that validates a portable file catalog and detects
duplicate files by (size, sha256) without performing any filesystem I/O.

## Quick start

```python
from module import catalog, duplicate_groups

entries = [
    {"path": "docs/readme.txt", "size": 1024, "sha256": "a" * 64},
    {"path": "backup/readme.txt", "size": 1024, "sha256": "a" * 64},
    {"path": "src/main.py",    "size": 512,  "sha256": "b" * 64},
]

validated = catalog(entries)
# Returns new list sorted by path; input is never mutated.

dups = duplicate_groups(entries)
# Returns [['backup/readme.txt', 'docs/readme.txt']]
```

## API

### `catalog(entries)` → `list[dict]`

Validates a list of entry dicts and returns a **new** list sorted by `path`.

**Contract per entry** — a dict with exactly three keys:

| Key      | Type              | Rules                                                                 |
|----------|-------------------|-----------------------------------------------------------------------|
| `path`   | `str`             | Non-empty POSIX relative path. Unicode allowed (`ñ`, `汉字`).         |
| `size`   | `int` (>= 0)      | Boolean `True`/`False` is **forbidden**.                              |
| `sha256` | `str` (64 chars)  | Exactly 64 lowercase hex characters `[0-9a-f]`.                       |

**Path restrictions**

- No backslash (`\`)
- No colon (`:`) — avoids Windows drive letters
- No leading slash (`/`) — must be relative
- No empty component (`a//b`)
- No `.` or `..` components
- No NUL (`\x00`) or newline (`\n`) characters
- Unicode characters are fully supported

**Returns** — A new `list[dict]` sorted lexicographically by `path`.

**Raises** — `ValueError` on:
- Malformed entry (wrong type, wrong keys, invalid values)
- Duplicate paths in the input list
- `entries` is not a list

**Immutability** — The input list and its dicts are never mutated. A fresh list
of fresh dicts is returned.

### `duplicate_groups(entries)` → `list[list[str]]`

Groups entries that share the same `(size, sha256)` pair.

**Returns** — A list of path-lists where each group has >= 2 members:
- Paths within each group are sorted lexicographically.
- Groups are sorted lexicographically by their first path.

**Example:**

```python
>>> duplicate_groups([
...     {"path": "z", "size": 1, "sha256": "a" * 64},
...     {"path": "a", "size": 1, "sha256": "a" * 64},
...     {"path": "b", "size": 2, "sha256": "b" * 64},
...     {"path": "c", "size": 2, "sha256": "b" * 64},
...     {"path": "unique", "size": 3, "sha256": "c" * 64},
... ])
[['a', 'z'], ['b', 'c']]
```

Entries with the same hash but different sizes are **not** reported as duplicates.

## CLI

```bash
# Valid input
$ echo '[{"path":"a","size":1,"sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}]' \
  | python module.py
{"catalog": [{"path": "a", "size": 1, "sha256": "aaa..."}], "duplicates": []}

# Invalid JSON — exit code 2
$ echo 'not json' | python module.py
invalid JSON input

# Invalid entry — exit code 2
$ echo '[{"path":"","size":1,"sha256":"aaa..."}]' | python module.py
path must be nonempty
```

**Stdout** — A single JSON object:
```json
{"catalog": [...], "duplicates": [...]}
```
Output uses `ensure_ascii=False` so Unicode characters appear directly.

**Stderr / exit code** — On any validation error the process exits with code `2`
and prints a concise one-line message to stderr. No Python `Traceback` is
emitted.

## Design decisions

- **No filesystem I/O.** All validation and grouping happens in memory.
  This makes the tool safe to run in sandboxed environments and trivially
  testable with synthetic data.
- **Immutability by default.** `catalog()` copies every entry so callers
  cannot accidentally mutate validated data.
- **Unicode support.** Paths such as `ñ/b.txt` or `日本語/file.md` are
  valid and sorted according to Python's default string ordering.
- **Exit code 2 for CLI errors.** Follows the POSIX convention for
  command-line usage mistakes (distinct from runtime errors).

## Testing & build

```bash
python test_module.py   # Unit & acceptance tests
python build.py          # Static AST parse check
```

Both must report `PASS` before committing.
