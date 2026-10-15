# catalog

Portable file-catalog validator and duplicate reporter. **No filesystem I/O** — the module operates purely on data structures.

## API

### `catalog(entries)`

Accepts a list of dicts with exactly the keys `path`, `size`, `sha256`.

**Validation rules:**

- `path`: non-empty POSIX-relative string. No backslash, colon, leading slash, empty component (`//`), `.`, `..`, NUL, or newline. Unicode is allowed.
- `size`: integer >= 0. `bool` is explicitly forbidden.
- `sha256`: exactly 64 lowercase hex characters.
- Duplicate `path` values raise `ValueError`.
- Wrong type, extra keys, or missing keys raise `ValueError`.

Returns a **new** list of dicts sorted by `path`. Never mutates input.

### `duplicate_groups(entries)`

Groups validated entries by `(size, sha256)`. Returns lists of paths where each group has **at least 2 members**. Groups and paths inside them are sorted lexicographically. Single-entry groups are dropped.

## CLI

```bash
echo '[{"path":"a","size":1,"sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}]' | python module.py
```

Output (JSON to stdout, exit 0):
```json
{"catalog": [{"path": "a", "size": 1, "sha256": "aaa..."}], "duplicates": []}
```

Invalid input prints a concise error to stderr and exits with code 2.

## Unicode example

```python
catalog([{"path": "café/naïve.txt", "size": 10, "sha256": "a" * 64}])
# Returns new list with entry sorted alongside others by path
```

## No filesystem

The module imports only `copy`, `hashlib`, `json`, and `sys`. It never accesses the filesystem.
