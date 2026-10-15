"""Execute related deterministic suites against this resumed working tree."""
import hashlib,json,os,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parents[1];E=R/'evidence/f24-transaction-cert-20261014';D=E/'chatgpt';D.mkdir(exist_ok=True)
h=hashlib.sha256((R/'tools/chatgpt-bridge.js').read_bytes()).hexdigest()
(D/'integrity-before.json').write_text(json.dumps({'protected':{'tools/chatgpt-bridge.js':h},'source':'resumed authorized working tree before deterministic suite'}),encoding='utf-8')
env=dict(os.environ,F24_PREFLIGHT_E=str(E),CHATGPT_TEST_EVIDENCE_DIR=str(D),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
results={}
for name in ['transaction','fresh-chat','delivery','send-actuator','single-physical-click','domain-lock','idempotency','human-reconciliation','controlled-send-utf8']:
 p=R/'tests'/('test-chatgpt-'+name+'.js' if name!='controlled-send-utf8' else 'test-controlled-send-utf8.js')
 r=subprocess.run(['node',str(p)],cwd=R,env=env,capture_output=True,encoding='utf-8',timeout=40)
 (E/(name+'.stdout.txt')).write_text(r.stdout,encoding='utf-8');(E/(name+'.stderr.txt')).write_text(r.stderr,encoding='utf-8')
 results[name]={'status':'PASS' if r.returncode==0 else 'FAIL','exit_code':r.returncode}
 print(json.dumps({name:results[name]}),flush=True)
 if r.returncode:raise RuntimeError(name+': '+r.stderr[-2000:])
assert hashlib.sha256((R/'tools/chatgpt-bridge.js').read_bytes()).hexdigest()==h
(E/'DETERMINISTIC.json').write_text(json.dumps({'status':'PASS','suites':results,'bridge_unchanged_during_tests':True},indent=2)+'\n',encoding='utf-8')
