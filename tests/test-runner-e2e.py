"""Live E2E. Run with the existing native Hermes Python (psutil already installed)."""
import argparse,hashlib,importlib.util,json,pathlib,subprocess,time,urllib.request
import psutil
ROOT=pathlib.Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('f',ROOT/'tests/runner-fixtures.py');f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=['22','final'],required=True);a=ap.parse_args()
cfg=json.loads(subprocess.check_output(['C:/Python314/python.exe',str(ROOT/'scripts/mcp-sandbox-server.py'),'--dump-yaml-json',str(ROOT/'config/system.yaml')],text=True))
e=ROOT/('evidence/phase-22' if a.stage=='22' else 'evidence/e2e-7b');e.mkdir(exist_ok=True)
p=f.project('native22' if a.stage=='22' else 'final7b-e2e',backend='live',phase_timeout=180,global_timeout=900)
plan_path=p/'.autopilot/RUN-PLAN.json';plan=json.loads(plan_path.read_text());plan['restart_budget']=1;plan_path.write_text(json.dumps(plan));f.approve(p)
assert not any(c.status=='LISTEN' and c.laddr.port==8080 for c in psutil.net_connections(kind='tcp')),'unexpected preexisting model listener'
model=None;runner=None;samples=[];seen={};injection=None;last_sample=0;last_gpu=0;gpu=[]
def read(path):
    try:return json.loads(path.read_text(encoding='utf-8-sig'))
    except (FileNotFoundError,PermissionError,json.JSONDecodeError):return None
try:
    if a.stage=='22':
        c=cfg['llama'];args=[c['executable'],'-m',c['model'],'--alias',c['alias'],'--host',c['host'],'--port',str(c['port']),'--ctx-size',str(c['ctx_size']),'--parallel',str(c['parallel']),'--cpu-moe','--n-gpu-layers',str(c['n_gpu_layers']),'--flash-attn','on','--cache-type-k',c['cache_type_k'],'--cache-type-v',c['cache_type_v'],'--jinja']
        model=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        deadline=time.monotonic()+180
        while time.monotonic()<deadline:
            assert model.poll() is None,'owned test model failed to start'
            try:
                with urllib.request.urlopen(c['health_endpoint'],timeout=2) as response:
                    if json.load(response)['status']=='ok':break
            except (OSError,ValueError):pass
            time.sleep(.3)
        else:raise AssertionError('test model health timeout')
    with (e/'native.stdout.txt').open('w',encoding='utf-8') as out,(e/'native.stderr.txt').open('w',encoding='utf-8') as err:
        runner=subprocess.Popen(['powershell.exe','-NoProfile','-NonInteractive','-File',str(ROOT/'runner/run.ps1'),'-ProjectRoot',str(p),'-Action','Start'],stdout=out,stderr=err)
        deadline=time.monotonic()+960
        while runner.poll() is None and time.monotonic()<deadline:
            now=time.monotonic();records=read(p/'.autopilot/PROCESSES.json')
            if records:
                for record in records['processes']:
                    try:
                        parent=psutil.Process(record['pid'])
                        if abs(parent.create_time()-(record['start_ticks']/1e7-62135596800))>.01:continue
                        for child in parent.children(recursive=True):
                            try:
                                command=' '.join(child.cmdline());seen[(child.pid,child.create_time())]={'pid':child.pid,'start_time':child.create_time(),'executable':child.exe(),'parent_role':record['name']}
                                if a.stage=='final' and injection is None and record['name']=='supervisor' and 'hermes_cli.main' in command and 'python' in child.name().lower():
                                    injection=seen[(child.pid,child.create_time())];(e/'injection.json').write_text(json.dumps(injection,indent=2)+'\n');child.kill()
                            except psutil.NoSuchProcess:pass
                    except psutil.NoSuchProcess:pass
            if now-last_sample>5:
                memory=psutil.virtual_memory();rss=0
                model_id=model.pid if model else next((x['pid'] for x in (records or {}).get('processes',[]) if x['name']=='llama'),None)
                if model_id:
                    try:rss=psutil.Process(model_id).memory_info().rss
                    except psutil.NoSuchProcess:pass
                samples.append({'elapsed_seconds':960-(deadline-now),'ram_total_bytes':memory.total,'ram_available_bytes':memory.available,'llama_working_set_bytes':rss});last_sample=now
            if now-last_gpu>60:
                v=subprocess.run(['nvidia-smi','--query-gpu=memory.used,memory.total','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=5);assert v.returncode==0,v.stderr;gpu.append(v.stdout.strip());last_gpu=now
            time.sleep(.2)
        assert runner.poll() is not None,'bounded live E2E deadline exceeded'
    report=read(p/'.autopilot/reports/runner-result.json');gate=read(p/'.autopilot/evidence/completion-gate.json');state=read(p/'.autopilot/STATE.json');heartbeat=read(p/'.autopilot/HEARTBEAT.json')
    assert runner.returncode==0 and report['status']==state['status']==heartbeat['status']=='COMPLETED',report
    assert gate['status']=='COMPLETED' and all(gate['checks'].values()),gate
    assert report['cleanup']['owned_survivors']==[] and not report['cleanup']['errors'] and report['cleanup']['run_mutex_released'] and report['cleanup']['inference_mutex']=='FREE',report
    assert (p/'.autopilot/reports/FINAL.md').exists() and not(p/'.autopilot/LOCK.json').exists()
    for identity in seen.values():
        try:assert abs(psutil.Process(identity['pid']).create_time()-identity['start_time'])>.01,identity
        except psutil.NoSuchProcess:pass
    if a.stage=='22':assert model.poll() is None and report['cleanup']['external_model_preserved']
    else:assert injection and report['retries']['supervisor']==1 and max(report['retries'].values())<=1,report
    hashes={str(v.relative_to(ROOT)):hashlib.sha256(v.read_bytes()).hexdigest() for v in (ROOT/'runner').iterdir() if v.suffix in ('.py','.ps1')}
    result={'status':'PASS','project':str(p),'stage':a.stage,'native_roles_observed':seen and sorted(set(v['parent_role'] for v in seen.values())),'native_chain':'Supervisor -> Qwen Code -> actual tests -> independent Reviewer -> Completion Gate -> reports -> cleanup','gate':gate,'report':report,'resources':samples,'vram_mib_used_total':gpu,'controlled_fault':injection,'owned_descendants_survived':0,'compatible_external_model_preserved':a.stage=='22','source_hashes':hashes,'dependencies_added':[]}
finally:
    if runner and runner.poll() is None:runner.kill();runner.wait(timeout=10)
    if model and model.poll() is None:model.terminate();model.wait(timeout=10)
assert not any(c.status=='LISTEN' and c.laddr.port==8080 for c in psutil.net_connections(kind='tcp'))
(e/'native.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'PASS','stage':a.stage,'duration_seconds':report['duration_seconds'],'controlled_fault':injection,'compatible_external_model_preserved':a.stage=='22'}))
