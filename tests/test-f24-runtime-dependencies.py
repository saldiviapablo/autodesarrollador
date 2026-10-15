"""Import every harness dependency in the same Hermes Python used by the harness."""
import ast,importlib,json,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[1];env=__import__('os').environ;path=root/env.get('F24_HARNESS','tests/test-phase24-attempt5-live.py');modules=[]
for node in ast.parse(path.read_text(encoding='utf-8')).body:
 if isinstance(node,ast.Import):modules.extend(n.name for n in node.names)
 elif isinstance(node,ast.ImportFrom):modules.append(node.module)
for name in sorted(set(modules)):importlib.import_module(name)
r=subprocess.run(['C:/Python314/python.exe','-c','import yaml;print(yaml.__version__)'],capture_output=True,text=True,check=True,timeout=15)
result={'status':'PASS','runtime':sys.executable,'imports':sorted(set(modules)),'canonical_python_pyyaml':r.stdout.strip(),'live_run_started':False,'no_new_dependency':True}
(pathlib.Path(env.get('F24_PREFLIGHT_E',root/'evidence/f24-harness-preflight-20261014'))/'runtime-dependencies.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
