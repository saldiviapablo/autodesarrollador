import hashlib,json,pathlib,shutil
R=pathlib.Path(__file__).resolve().parents[1];E=R/'evidence/f24-transaction-cert-20261014';B=R/'backups/f24-transaction-cert-20261014';E.mkdir(exist_ok=True);B.mkdir(exist_ok=True)
assert not(E/'history-before.json').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=json.loads((R/'evidence/f24-admission-repair-20261014/history-before.json').read_text())['files']
for tree in ['evidence/f24-admission-repair-20261014','sandbox/test-send-actuator-153deadd913e4bdfbbc081196d7f1c63']:
 for p in (R/tree).rglob('*'):
  if p.is_file():files[p.relative_to(R).as_posix()]=sha(p)
for p in (R/'runtime/chatgpt-consultations').glob('*'):
 if p.is_file() and p.name!='browser-lease.json':files[p.relative_to(R).as_posix()]=sha(p)
assert all(sha(R/p)==h for p,h in files.items());(E/'history-before.json').write_text(json.dumps({'files':files},indent=2)+'\n',encoding='utf-8')
items=['tools/chatgpt-bridge.js','tools/chatgpt-ledger.js','tools/chatgpt-delivery.js','tools/chatgpt-fresh-chat.js','tools/chatgpt-send-actuator.js','scripts/consultar-chatgpt.ps1','runner/contract.py','tests/preflight-f24-harness.py','tests/seal-f24-preflight.py','tests/test-phase24-attempt6-live.py','tests/test-chatgpt-fresh-chat.js','tests/test-chatgpt-delivery.js','tests/test-chatgpt-idempotency.js','tests/test-chatgpt-human-reconciliation.js','tests/test-chatgpt-send-actuator.js','tests/test-phase22.py','00-README.md','07-ROADMAP.md','MANIFEST.md','docs/IMPLEMENTATION-STATUS.md','config/INSTALLATION-STATE.json'];manifest=[]
for n in items:
 d=B/n;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/n,d);manifest.append({'original':n,'copy':str(d.relative_to(R)),'sha256':sha(d),'reason':'transactional preparation and owned pre-send rollback'})
(B/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('BACKUP PASS; history '+str(len(files)))
