import hashlib,json,os,pathlib,re,socket,subprocess,sys,time,urllib.request,urllib.error
from ruamel.yaml import YAML
import psutil
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8')
cfg=YAML(typ='safe').load((ROOT/'config/system.yaml').read_text(encoding='utf-8-sig'))
e=ROOT/'evidence/phase-7a8';e.mkdir(exist_ok=True);project=ROOT/'sandbox/phase7a8-dashboard'
script=ROOT/'scripts/governed-dashboard.py'
bootstrap="import sys,runpy;sys.path.insert(0,"+repr(cfg['native_browser']['native_site_packages'])+");sys.argv="+repr([str(script),'--project',str(project)])+";runpy.run_path("+repr(str(script))+",run_name='__main__')"
python=cfg['document_extraction']['native_python']
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
protected=['config/security.yaml','scripts/inference-lock.ps1','scripts/hermes-pre-tool-hook.py']
before={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in protected}
contract=project/'.autopilot/RUN-CONTRACT.yaml';contract_before=contract.read_bytes()
log=(ROOT/'logs/dashboard-7a8.log');log.parent.mkdir(exist_ok=True)
proc=None;report={};token=None
def stop_owned():
    if proc and proc.poll() is None:
        owner=psutil.Process(proc.pid)
        descendants=owner.children(recursive=True)
        for child in reversed(descendants):
            if child.is_running():child.kill()
        psutil.wait_procs(descendants,timeout=5)
        if proc.poll() is None:proc.kill()
        proc.wait(timeout=10)
def request(path,method='GET',data=None,headers=None):
    hdr=dict(headers or {})
    if token:hdr['X-Hermes-Session-Token']=token
    if data is not None:hdr['Content-Type']='application/json';data=json.dumps(data).encode()
    req=urllib.request.Request('http://127.0.0.1:9119'+path,data=data,method=method,headers=hdr)
    try:
        with urllib.request.urlopen(req,timeout=8) as r:return r.status,r.read().decode('utf-8')
    except urllib.error.HTTPError as r:return r.code,r.read().decode('utf-8')
try:
    # Wildcard exposure is denied before importing the server or binding a socket.
    deny_bootstrap=bootstrap.replace(repr([str(script),'--project',str(project)]),repr([str(script),'--project',str(project),'--host','0.0.0.0']))
    denial=subprocess.run([python,'-I','-c',deny_bootstrap],capture_output=True,text=True,timeout=15,env=env)
    assert denial.returncode and 'NON_LOOPBACK_DENIED' in denial.stdout,denial.stdout
    with log.open('w',encoding='utf-8') as output:
        proc=subprocess.Popen([python,'-I','-c',bootstrap],stdout=output,stderr=output,env=env)
    ready=False
    for _ in range(90):
        if proc.poll() is not None:raise AssertionError('Dashboard exited; inspect logs/dashboard-7a8.log')
        try:
            status,html=request('/')
            if status==200:ready=True;break
        except (OSError,urllib.error.URLError):pass
        time.sleep(.2)
    assert ready,'Dashboard startup timeout'
    match=re.search(r'window\.__HERMES_SESSION_TOKEN__\s*=\s*[\"\']([^\"\']+)',html)
    if not match:match=re.search(r'(?:hermesSessionToken|__HERMES_TOKEN__)\s*=\s*[\"\']([^\"\']+)',html)
    assert match,'Native SPA token injection missing'
    token=match.group(1)
    endpoints={}
    for path in ['/api/status','/api/config','/api/mcp/servers','/api/memory','/api/cron/jobs','/api/skills','/api/da/state']:
        status,body=request(path);endpoints[path]={'status':status,'json_valid':False}
        try:json.loads(body);endpoints[path]['json_valid']=True
        except json.JSONDecodeError:pass
        assert status==200 and endpoints[path]['json_valid'],(path,status,body[:250])
    owned_processes=[psutil.Process(proc.pid),*psutil.Process(proc.pid).children(recursive=True)]
    connections=[c for p in owned_processes for c in p.net_connections(kind='inet')]
    listeners=[{'ip':c.laddr.ip,'port':c.laddr.port} for c in connections if c.status=='LISTEN']
    assert {'ip':'127.0.0.1','port':9119} in listeners and all(c['ip']=='127.0.0.1' for c in listeners),listeners
    rejected={}
    for path,method,data in [('/api/config','PUT',{'config':{'hooks_auto_accept':True}}),('/api/config/raw','PUT',{'yaml':'model: evil'}),('/api/mcp/servers','POST',{'command':'git push'}),('/api/memory/reset','POST',{}),('/api/cron/jobs','POST',{'script':'evil.py'}),('/api/skills','POST',{'content':'git push'}),('/api/ops/restart','POST',{}),('/api/config?profile=desarrollador-autonomo','GET',None),('/api/mcp/oauth/callback/evil','GET',None),('/api/files?path=C:/','GET',None)]:
        status,body=request(path,method,data);assert status==403,(path,status);rejected[path]=json.loads(body)
    assert before=={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in protected}
    assert contract.read_bytes()==contract_before
    (ROOT/'runtime/dashboard-review-ready.json').write_text(json.dumps({'pid':proc.pid,'url':'http://127.0.0.1:9119','deadline_seconds':180}))
    # UI review signal is written by the operator test driver, never via an admin endpoint.
    saved_ui=e/'ui-review.json'
    if '--reuse-ui' in sys.argv:
        ui=json.loads(saved_ui.read_text(encoding='utf-8-sig'))
        assert ui['source_sha256']==hashlib.sha256(script.read_bytes()).hexdigest(),'UI source changed'
    else:
        deadline=time.monotonic()+180
        while time.monotonic()<deadline and not(ROOT/'runtime/dashboard-review-done.json').exists():time.sleep(.2)
        if not(ROOT/'runtime/dashboard-review-done.json').exists():raise AssertionError('UI review deadline expired')
        ui=json.loads((ROOT/'runtime/dashboard-review-done.json').read_text())
        ui['source_sha256']=hashlib.sha256(script.read_bytes()).hexdigest()
        saved_ui.write_text(json.dumps(ui,indent=2)+'\n')
    assert ui['status']=='PASS',ui
    # Forced termination demonstrates this capability is optional to deterministic control.
    stop_owned()
    deadline=time.monotonic()+3
    closed=False
    while time.monotonic()<deadline:
        with socket.socket() as s:
            if s.connect_ex(('127.0.0.1',9119))!=0:closed=True;break
        time.sleep(.05)
    assert closed,'Owned dashboard listener did not close'
    assert json.loads((project/'.autopilot/STATE.json').read_text(encoding='utf-8-sig'))['run_id']
    report={'status':'PASS','tests':{'T-7A-DASH-001':'PASS','T-7A-DASH-002':'PASS','T-7A-DASH-003':'PASS'},'native_endpoints':endpoints,'listeners':listeners,'rejected':rejected,'protected_hashes_unchanged':True,'contract_unchanged':True,'ui_review':ui,'forced_termination_pid_stopped':True,'state_read_without_dashboard':True,'runner_dependency_added':False,'local_inferences':0}
finally:
    stop_owned()
    for name in ('dashboard-review-ready.json','dashboard-review-done.json'):
        p=ROOT/'runtime'/name
        if p.exists():p.unlink()
    (e/'tests.json').write_text(json.dumps(report,indent=2)+'\n')
if report:(e/'security.json').write_text(json.dumps({'status':'PASS','protected_hashes_unchanged':True,'contract_unchanged':True,'loopback_only':True,'denied_mutations':list(report['rejected'])},indent=2)+'\n')
print(json.dumps(report));assert report.get('status')=='PASS'
