"""Harmless live process-ownership certification; no inference or bridge action."""
from pathlib import Path
import base64,datetime,json,os,subprocess,sys,time,uuid
import psutil
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tests'))
from endurance_controller import ps,sha,write
E=R/'evidence'/('audit-owned-gate-cert-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6]);E.mkdir()
wrapper=R/'logs/overnight/run-owned-audit-gate.ps1'
(E/'wrapper.snapshot.ps1').write_bytes(wrapper.read_bytes())
fixture=E/'harmless child space.py'
fixture.write_text('''import json,os,subprocess,sys,time
from pathlib import Path
import psutil
if sys.argv[1]=='utf8':
 sys.stdout.buffer.write('á ñ € 😀\\n'.encode());sys.stderr.buffer.write('diagnóstico ü\\n'.encode());raise SystemExit(0)
if sys.argv[1]=='exit7':raise SystemExit(7)
if sys.argv[1]=='sleep':time.sleep(120)
if sys.argv[1]=='tree':
 child=subprocess.Popen([sys.executable,__file__,'sleep'])
 ids=[{'pid':os.getpid(),'birth':psutil.Process().create_time()},{'pid':child.pid,'birth':psutil.Process(child.pid).create_time()}]
 Path(sys.argv[2]).write_text(json.dumps(ids),encoding='utf-8');time.sleep(120)
''',encoding='utf-8')
results={};env=dict(os.environ,PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
birth=lambda pid:ps('(Get-Process -Id '+str(pid)+').StartTime.ToUniversalTime().Ticks')
def alive(i):
 try:return abs(psutil.Process(i['pid']).create_time()-i['birth'])<.01
 except psutil.NoSuchProcess:return False
def launch(name,mode,timeout,controller=None):
 controller=controller or os.getpid();pidfile=E/(name+'-tree.json')
 req={'evidence':str(E),'name':name,'argv':[sys.executable,str(fixture),mode,str(pidfile)],'timeout':timeout,'controller_pid':controller,'controller_birth_ticks':birth(controller)}
 payload=base64.b64encode(json.dumps(req).encode()).decode()
 out=(E/(name+'.wrapper.stdout.txt')).open('wb');err=(E/(name+'.wrapper.stderr.txt')).open('wb')
 p=subprocess.Popen(['powershell.exe','-NoProfile','-NonInteractive','-File',str(wrapper),'-PayloadBase64',payload],cwd=R,env=env,stdout=out,stderr=err,creationflags=0x08000000)
 return p,pidfile,out,err
def finish(name,item,expected_reason,expected_exit):
 p,pidfile,out,err=item
 try:code=p.wait(timeout=35)
 finally:out.close();err.close()
 report=json.loads((E/(name+'.process.json')).read_text(encoding='utf-8-sig'))
 assert report['reason']==expected_reason,(name,report)
 assert report['owned_job_closed'] and report['owned_process_exited'] and report['stream_cleanup']
 assert report['exit_code']==expected_exit,(name,report)
 assert code==(0 if not expected_reason and expected_exit==0 else 1)
 if pidfile.exists():
  identities=json.loads(pidfile.read_text(encoding='utf-8'));deadline=time.monotonic()+5
  while any(alive(i) for i in identities) and time.monotonic()<deadline:time.sleep(.1)
  assert not any(alive(i) for i in identities),'OWNED_DESCENDANT_SURVIVED'
 results[name]={'status':'PASS','process':report,'descendants_dead':True}
 print(json.dumps({name:'PASS'}),flush=True)
sentinel=subprocess.Popen([sys.executable,str(fixture),'sleep'],env=env,creationflags=0x08000000)
sentinel_identity={'pid':sentinel.pid,'birth':psutil.Process(sentinel.pid).create_time()}
try:
 finish('utf8',launch('utf8','utf8',15),'',0)
 assert (E/'utf8.stdout.txt').read_bytes()=='á ñ € 😀\n'.encode()
 assert (E/'utf8.stderr.txt').read_bytes()=='diagnóstico ü\n'.encode()
 finish('exit7',launch('exit7','exit7',15),'',7)
 finish('timeout-tree',launch('timeout-tree','tree',3),'AUDIT_GATE_TIMEOUT',None)
 parent=subprocess.Popen([sys.executable,str(fixture),'sleep'],env=env,creationflags=0x08000000)
 parent_identity={'pid':parent.pid,'birth':psutil.Process(parent.pid).create_time()}
 try:
  item=launch('parent-loss-tree','tree',20,parent.pid)
  deadline=time.monotonic()+15
  while not item[1].exists() and time.monotonic()<deadline:
   assert item[0].poll() is None,'WRAPPER_DIED_BEFORE_TREE';time.sleep(.1)
  assert item[1].exists(),'TREE_NOT_STARTED'
  assert alive(parent_identity);parent.terminate();parent.wait(timeout=5)
  finish('parent-loss-tree',item,'AUDIT_CONTROLLER_LOST',None)
 finally:
  if alive(parent_identity):parent.terminate();parent.wait(timeout=5)
 assert alive(sentinel_identity),'PREEXISTING_PROCESS_CHANGED'
 results['preexisting-process-preserved']={'status':'PASS','identity':sentinel_identity}
 write(E/'CERTIFIED.json',{'status':'PASS','wrapper_sha256':sha(wrapper),'tests':results,'no_inference':True,'no_bridge':True,'no_ledger':True,'scope':'isolated harmless process wrapper only; not F26'})
 print(json.dumps({'status':'PASS','evidence':str(E)}))
finally:
 if alive(sentinel_identity):sentinel.terminate();sentinel.wait(timeout=5)
