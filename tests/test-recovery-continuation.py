"""Real owned crash, guardian, checkpoint restoration and native START-Recover.

Probe roles are deterministic, explicitly not live inference or E2E completion.
"""
import hashlib,importlib.util,json,pathlib,subprocess,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('fixture',ROOT/'tests/runner-fixtures.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
E=ROOT/'evidence/f24-frontiers-20261014/recovery';E.mkdir(exist_ok=True)
def read(path):
    for _ in range(20):
        try:return json.loads(path.read_text(encoding='utf-8-sig'))
        except (OSError,ValueError):time.sleep(.1)
    raise AssertionError(str(path))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
p=f.project('frontier-recovery',delay=3,phase_timeout=15,global_timeout=120);a=p/'.autopilot';approval=f.approve(p)
clock=ROOT/'runtime/run-clocks'/pathlib.Path(approval['receipt_path']).name
proc=subprocess.Popen(['powershell.exe','-NoProfile','-NonInteractive','-File',str(ROOT/'runner/run.ps1'),'-ProjectRoot',str(p),'-Action','Start'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
    end=time.monotonic()+20
    while time.monotonic()<end:
        if (a/'PROCESSES.json').exists() and any(i['name']=='supervisor' for i in read(a/'PROCESSES.json')['processes']):break
        time.sleep(.1)
    assert proc.poll() is None
    budget=f.powershell('scripts/consultar-chatgpt.ps1','-MockResponse','sandbox response','-Question','sandbox budget probe','-ConsultationId','sandbox-recovery-budget','-StatePath',a/'STATE.json',timeout=20)
    assert budget.returncode==0,budget.stderr
    time.sleep(.5)
    assert read(a/'STATE.json')['chatgpt']['queries_used']==1,'Runner lost managed consultant budget reservation'
    chk=f.powershell('scripts/create-autopilot-checkpoint.ps1','-ProjectPath',p,'-CheckpointId','chk-continuation-test','-Reason','Owned crash boundary test')
    assert chk.returncode==0,chk.stderr
    clock_hash=sha(clock);proc.kill();proc.wait(timeout=5)
    end=time.monotonic()+25
    while not(a/'reports/watchdog-failure.json').exists() and time.monotonic()<end:time.sleep(.1)
    assert read(a/'reports/watchdog-failure.json')['reason']=='PARENT_PROCESS_LOST'
    end=time.monotonic()+10
    while (a/'LOCK.json').exists() and time.monotonic()<end:time.sleep(.1)
    assert not(a/'LOCK.json').exists()
    # Force checkpoint fallback, preserving the pre-injection state in evidence.
    for name in ('STATE.json','STATE.previous.json'):
        (E/('before-corruption-'+name)).write_bytes((a/name).read_bytes());(a/name).write_text('{controlled corruption',encoding='utf-8')
    resumed=f.powershell('runner/run.ps1','-ProjectRoot',p,'-Action','Start','-Recover',timeout=65)
    (E/'resume.stdout.txt').write_text(resumed.stdout,encoding='utf-8');(E/'resume.stderr.txt').write_text(resumed.stderr,encoding='utf-8')
    events=[json.loads(l) for l in (a/'EVENTS.jsonl').read_text(encoding='utf-8-sig').splitlines()]
    assert any(v['type']=='RUN_RECOVERED_FROM_DISK' for v in events),resumed.stderr
    assert any('checkpoint' in json.dumps(v.get('payload',{})).lower() and v['type']=='RECOVERY_RECONCILED' for v in events)
    assert sha(clock)==clock_hash
    assert read(a/'STATE.json')['chatgpt']['queries_used']==1
    report=read(a/'reports/runner-result.json');assert report['tests'][0]['status']=='PASS',report
    assert report['cleanup']['owned_survivors']==[] and report['cleanup']['inference_mutex']=='FREE'
    assert not(a/'LOCK.json').exists()
    result={'status':'PASS','RECOVERY_DETECTION':'PASS','RECOVERY_CONTINUATION':'PASS','checkpoint_restored':True,'original_clock_unchanged':True,'continued_worker_and_tests':True,'concurrent_budget_reservation_preserved':True,'terminal':report['status'],'terminal_explanation':'Probe backend deliberately cannot certify live completion','cleanup':report['cleanup'],'project':str(p),'inference_calls':0}
    (E/'GATE.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');(E/'events.json').write_text(json.dumps(events,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
finally:
    if proc.poll() is None:proc.kill();proc.wait(timeout=5)
