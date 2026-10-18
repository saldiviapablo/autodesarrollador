"""Generate deterministic malformed and corrected planner proposals for native Windows CI."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("structural_input",ROOT/"tests/test-onboarding-structural-fix.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
base=module.base_value()
first=json.loads(json.dumps(base))
first["plan"]["tests"][0]["argv"]=["npm"]
first["seed_files"]={"notes.md":"Example"}
second=base
root=ROOT/"sandbox"/"ci-self-repair-binding"
root.mkdir(parents=True,exist_ok=True)
(root/"first.json").write_text(json.dumps(first,ensure_ascii=False),encoding="utf-8")
(root/"second.json").write_text(json.dumps(second,ensure_ascii=False),encoding="utf-8")
(root/"project").mkdir(exist_ok=True)
print("SELF_REPAIR_REAL_BINDING_FIXTURES_READY")
