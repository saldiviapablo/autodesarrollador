"""Back up changed infrastructure and preserve the failed admission byte-for-byte."""
import hashlib,json,pathlib,shutil
ROOT=pathlib.Path(__file__).resolve().parents[1];E=ROOT/'evidence/f24-admission-repair-20261014';B=ROOT/'backups/f24-admission-repair-20261014'
E.mkdir(exist_ok=True);B.mkdir(exist_ok=True);assert not(E/'history-before.json').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=json.loads((ROOT/'evidence/f24-attempt6-preflight-20261014/history-before.json').read_text())['files']
trees=['evidence/f24-attempt6-preflight-20261014','sandbox/test-send-actuator-735b2b7cc7ad4173b62227a5d45a3f46']
trees.extend(p.relative_to(ROOT).as_posix() for p in (ROOT/'sandbox').glob('7b-cleanup22-*') if p.is_dir())
for tree in trees:
 for p in (ROOT/tree).rglob('*'):
  if p.is_file():files[p.relative_to(ROOT).as_posix()]=sha(p)
for p in (ROOT/'runtime/chatgpt-consultations').glob('*'):
 if p.is_file() and p.name!='browser-lease.json':files[p.relative_to(ROOT).as_posix()]=sha(p)
assert all(sha(ROOT/n)==h for n,h in files.items())
(E/'history-before.json').write_text(json.dumps({'files':files,'purpose':'preserve all previous admissions and ledgers; no reconciliation'},indent=2)+'\n',encoding='utf-8')
items=['tools/chatgpt-bridge.js','tools/chatgpt-send-actuator.js','tools/chatgpt-delivery.js','runner/contract.py','tests/test-phase22.py','tests/test-chatgpt-actuator-live.ps1','tests/test-phase24-attempt6-live.py','tests/preflight-f24-harness.py','tests/seal-f24-preflight.py','00-README.md','07-ROADMAP.md','MANIFEST.md','docs/IMPLEMENTATION-STATUS.md','config/INSTALLATION-STATE.json']
manifest=[]
for n in items:
 p=ROOT/n;q=B/n;q.parent.mkdir(parents=True,exist_ok=True);assert not q.exists();shutil.copyfile(p,q);manifest.append({'original':n,'copy':q.relative_to(ROOT).as_posix(),'sha256':sha(p),'reason':'real New Chat isolation and fault-only heartbeat fixture'})
(B/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','historical_files':len(files),'backups':len(items)}))
