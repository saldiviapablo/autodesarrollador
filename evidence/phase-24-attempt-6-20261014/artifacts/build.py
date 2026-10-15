import ast,pathlib
for p in pathlib.Path(".").glob("*.py"):ast.parse(p.read_text(encoding="utf-8"))
print("F24_BUILD_PASS")
