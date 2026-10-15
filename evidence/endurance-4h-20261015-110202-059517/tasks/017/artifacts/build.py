import ast,pathlib
ast.parse(pathlib.Path("module.py").read_text(encoding="utf-8"))
print("ENDURANCE_BUILD_PASS")
