"""Preserve historical attempts and back up infrastructure before actuator repair."""
import hashlib,json,pathlib,shutil
ROOT=pathlib.Path(__file__).resolve().parents[1]
E=ROOT/'evidence/f24-attempt6-preflight-20261014';E.mkdir(exist_ok=True)
B=ROOT/'backups/f24-actuator-20261014';B.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not (E/'history-before.json').exists(),'PRESERVATION_ALREADY_CAPTURED'
files=json.loads((ROOT/'evidence/f24-harness-preflight-20261014/history-before.json').read_text())['files']
for tree in ('sandbox/f24-attempt5-e6230453','evidence/phase-24-attempt-5-20261014','evidence/f24-harness-preflight-20261014'):
 for p in (ROOT/tree).rglob('*'):
  if p.is_file():files[p.relative_to(ROOT).as_posix()]=sha(p)
for p in (ROOT/'runtime/chatgpt-consultations').glob('*'):
 if p.is_file() and p.name!='browser-lease.json':files[p.relative_to(ROOT).as_posix()]=sha(p)
assert all((ROOT/p).is_file() and sha(ROOT/p)==h for p,h in files.items())
(E/'history-before.json').write_text(json.dumps({'files':files,'preserve':'all previous attempts and existing ledgers; no reconciliation'},indent=2)+'\n',encoding='utf-8')
items=['tools/chatgpt-bridge.js','tools/chatgpt-delivery.js','tools/chatgpt-ledger.js','runner/contract.py','tests/preflight-f24-harness.py','tests/seal-f24-preflight.py','tests/test-f24-frozen-evaluator.py','tests/test-qwen-research-model-input.py','tests/test-f24-runtime-dependencies.py','tests/test-chatgpt-delivery.js','tests/test-chatgpt-single-physical-click.js','00-README.md','07-ROADMAP.md','MANIFEST.md','docs/IMPLEMENTATION-STATUS.md','config/INSTALLATION-STATE.json']
manifest=[]
for name in items:
 source=ROOT/name;dest=B/name;dest.parent.mkdir(parents=True,exist_ok=True);assert not dest.exists();shutil.copyfile(source,dest)
 manifest.append({'original':name,'copy':dest.relative_to(ROOT).as_posix(),'sha256':sha(source),'reason':'composer-scoped actuator and fresh F24 attempt6; historical runs immutable'})
(B/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','historical_files':len(files),'backups':len(items)}))
