"""Byte/staging verification for this stopped admission only."""
import hashlib,json,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];E=ROOT/'evidence/f24-admission-repair-20261014'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda p,v:p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
if len(sys.argv)>1 and sys.argv[1]=='staged':
 files=json.loads((E/'capture-manifest.json').read_text())['files'];bad=[]
 for name,h in files.items():
  r=subprocess.run(['git','show',':'+E.relative_to(ROOT).as_posix()+'/'+name],cwd=ROOT,capture_output=True)
  if r.returncode or hashlib.sha256(r.stdout).hexdigest()!=h:bad.append(name)
 save(E/'staging-integrity.json',{'status':'PASS' if not bad else 'FAIL','files':len(files),'mismatches':bad});assert not bad,bad
 print('STAGED BYTE PROOF PASS '+str(len(files)))
else:
 history=json.loads((E/'history-before.json').read_text())['files'];bad=[n for n,h in history.items() if sha(ROOT/n)!=h];assert not bad,bad
 files={p.relative_to(E).as_posix():sha(p) for p in E.rglob('*') if p.is_file() and p.name not in ['capture-manifest.json','staging-integrity.json']}
 save(E/'capture-manifest.json',{'files':files,'historical_files_rechecked':len(history),'historical_mismatches':bad,'fresh_chat_stop':True,'attempt6_started':False})
 print('CAPTURE PASS '+str(len(files))+'; history '+str(len(history)))
