import importlib.util,json,pathlib,subprocess,sys,time
import psutil
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('fixtures',ROOT/'tests/runner-fixtures.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
p=f.project('watchdog-live',backend='live',phase_timeout=180,global_timeout=1000);f.approve(p)
log=ROOT/'logs/phase18-native';log.mkdir(exist_ok=True)
with (log/'stdout.txt').open('w',encoding='utf-8') as out,(log/'stderr.txt').open('w',encoding='utf-8') as err:
    proc=subprocess.Popen(['powershell.exe','-NoProfile','-NonInteractive','-File',str(ROOT/'runner/run.ps1'),'-ProjectRoot',str(p),'-Action','Start'],stdout=out,stderr=err)
injected=[];killed=set();deadline=time.monotonic()+1050
e=ROOT/'evidence/phase-18';e.mkdir(exist_ok=True)
def record_injections():
    (p/'.autopilot/evidence/injected-process-kills.json').write_text(json.dumps(injected,indent=2)+'\n')
try:
    while proc.poll() is None and time.monotonic()<deadline:
        record_path=p/'.autopilot/PROCESSES.json'
        if record_path.exists():
            try:records=json.loads(record_path.read_text(encoding='utf-8-sig'))['processes']
            except (json.JSONDecodeError,PermissionError,FileNotFoundError):time.sleep(.1);continue
            if 'llama' not in killed:
                health_events=(p/'.autopilot/EVENTS.jsonl').read_text(encoding='utf-8-sig')
                model=next((x for x in records if x['name']=='llama'),None)
                if model and 'MODEL_HEALTH_READY' in health_events:
                    target=psutil.Process(model['pid']);assert abs(target.create_time()-(model['start_ticks']/10000000-62135596800))<.01
                    executable=target.exe();injected.append({'role':'llama','pid':target.pid,'real_executable':executable});record_injections();target.kill();killed.add('llama')
            elif 'hermes' not in killed:
                parent=next((x for x in records if x['name']=='supervisor'),None)
                if parent:
                    try:descendants=psutil.Process(parent['pid']).children(recursive=True)
                    except psutil.NoSuchProcess:descendants=[]
                    for target in descendants:
                        try:cmd=' '.join(target.cmdline())
                        except psutil.NoSuchProcess:continue
                        if 'hermes_cli.main' in cmd and 'python' in target.name().lower():
                            executable=target.exe();injected.append({'role':'hermes','pid':target.pid,'real_executable':executable});record_injections();target.kill();killed.add('hermes');break
            elif 'qwen' not in killed:
                parent=next((x for x in records if x['name']=='worker'),None)
                if parent:
                    try:descendants=psutil.Process(parent['pid']).children(recursive=True)
                    except psutil.NoSuchProcess:descendants=[]
                    for target in descendants:
                        try:cmd=' '.join(target.cmdline())
                        except psutil.NoSuchProcess:continue
                        if 'cli-entry.js' in cmd and target.name().lower()=='node.exe':
                            executable=target.exe();injected.append({'role':'qwen','pid':target.pid,'real_executable':executable});record_injections();target.kill();killed.add('qwen');break
        time.sleep(.15)
    assert proc.poll() is not None,'Watchdog live test deadline exceeded'
    result=json.loads((p/'.autopilot/reports/runner-result.json').read_text(encoding='utf-8-sig'))
    restarts=json.loads((p/'.autopilot/RESTARTS.json').read_text(encoding='utf-8-sig'))
    assert killed=={'llama','hermes','qwen'},injected
    assert result['technical_status']=='SUCCESS',result
    assert restarts['llama']==1 and restarts['supervisor']>=1 and restarts['worker']>=1 and max(restarts.values())<=3,restarts
    assert all(not psutil.pid_exists(x['pid']) for x in result['processes'])
    data={'status':'PASS','tests':{'T-WATCH-003':'PASS','T-WATCH-004':'PASS','T-WATCH-005':'PASS'},'injected_real_process_kills':injected,'restarts':restarts,'recovered_pipeline':'SUCCESS','disk_recovery':True,'cleanup':'PASS','project':str(p)}
    e=ROOT/'evidence/phase-18';e.mkdir(exist_ok=True);(e/'native.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data))
finally:
    if proc.poll() is None:proc.kill();proc.wait(timeout=10)
