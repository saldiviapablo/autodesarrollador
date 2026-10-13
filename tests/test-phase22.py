"""Actual owned process teardown, external preservation, crash and disk recovery."""
import ctypes,datetime,importlib.util,json,pathlib,subprocess,time
ROOT=pathlib.Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('f',ROOT/'tests/runner-fixtures.py');f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
e=ROOT/'evidence/phase-22';e.mkdir(exist_ok=True);cases={}
kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong];kernel.OpenProcess.restype=ctypes.c_void_p;kernel.CloseHandle.argtypes=[ctypes.c_void_p];kernel.GetProcessTimes.argtypes=[ctypes.c_void_p]+[ctypes.POINTER(ctypes.c_ulonglong)]*4
def read(p):
    for _ in range(30):
        try:return json.loads(p.read_text(encoding='utf-8-sig'))
        except (PermissionError,json.JSONDecodeError):time.sleep(.1)
    raise AssertionError(str(p))
def alive(record):
    h=kernel.OpenProcess(0x1000,False,record['pid'])
    if not h:return False
    t=[ctypes.c_ulonglong() for _ in range(4)];ok=kernel.GetProcessTimes(h,*[ctypes.byref(v) for v in t]);kernel.CloseHandle(h)
    return bool(ok and t[0].value+504911232000000000==record['start_ticks'])
def verify(p,name,terminal):
    report=read(p/'.autopilot/reports/runner-result.json');assert report['status']==terminal,report
    assert not (p/'.autopilot/LOCK.json').exists()
    assert not any(alive(v) for v in report['processes']),report
    state=read(p/'.autopilot/STATE.json');hb=read(p/'.autopilot/HEARTBEAT.json');assert state['status']==hb['status']==terminal
    assert report['cleanup']['owned_survivors']==[] and report['cleanup']['inference_mutex']=='FREE',report
    cases[name]={'status':'PASS','terminal':terminal,'project':str(p),'reason':report['reason'],'cleanup':report['cleanup']}
    return report
for name,kwargs in [('failure',{}),('timeout',{'delay':30,'global_timeout':2}),('stalled',{}),('checkpoint_write_failure',{})]:
    p=f.project('cleanup22-'+name,**kwargs)
    if name=='stalled':
        path=p/'.autopilot/STATE.json';d=read(path);d['progress']['no_progress_cycles']=3;path.write_text(json.dumps(d))
    if name=='checkpoint_write_failure':
        folder=p/'.autopilot/checkpoints';folder.rename(p/'.autopilot/checkpoints.saved');folder.write_text('controlled obstruction')
    f.approve(p);r=f.start(p,60);report=verify(p,name,'STALLED' if name=='stalled' else 'FAILED')
    assert report['cleanup']['run_mutex_released'] and report['cleanup']['run_lock_removed']
    if name=='checkpoint_write_failure':assert 'FINALIZATION_FAILED' in report['reason']
external=subprocess.Popen(['C:/Python314/python.exe','-m','http.server','8080','--bind','127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
    time.sleep(.5);p=f.project('cleanup22-external',backend='live',global_timeout=30);f.approve(p);r=f.start(p,60)
    report=verify(p,'blocked_external','BLOCKED_REQUIRES_HUMAN');assert external.poll() is None
    assert (p/'.autopilot/reports/BLOCKED.md').exists();cases['blocked_external']['external_process_preserved']=True
finally:external.terminate();external.wait(timeout=10)
def running(name,stale=False):
    p=f.project('cleanup22-'+name,delay=10,phase_timeout=15,global_timeout=90)
    if stale:
        path=p/'.autopilot/RUN-PLAN.json';d=read(path);d['heartbeat_stale_seconds']=1;path.write_text(json.dumps(d))
    f.approve(p);proc=subprocess.Popen(['powershell.exe','-NoProfile','-NonInteractive','-File',str(ROOT/'runner/run.ps1'),'-ProjectRoot',str(p),'-Action','Start'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    deadline=time.monotonic()+20
    while time.monotonic()<deadline:
        if (p/'.autopilot/WATCHDOG.json').exists() and 'PROCESS_STARTED' in (p/'.autopilot/EVENTS.jsonl').read_text(encoding='utf-8-sig'):return p,proc
        assert proc.poll() is None,'Runner exited before injection';time.sleep(.1)
    proc.kill();raise AssertionError('test startup deadline')
p,proc=running('stop');r=f.powershell('runner/stop.ps1','-ProjectRoot',p);assert r.returncode==0,r.stderr;proc.wait(timeout=20);verify(p,'controlled_stop','ABORTED')
for name,stale in [('parent_crash',False),('heartbeat_stale',True)]:
    p,proc=running(name,stale)
    if stale:
        nt=ctypes.WinDLL('ntdll');nt.NtSuspendProcess.argtypes=[ctypes.c_void_p];h=kernel.OpenProcess(0x0800,False,proc.pid);assert h;assert nt.NtSuspendProcess(h)==0;kernel.CloseHandle(h)
    else:proc.kill()
    proc.wait(timeout=15);deadline=time.monotonic()+20
    while time.monotonic()<deadline and not (p/'.autopilot/reports/watchdog-failure.json').exists():time.sleep(.1)
    assert (p/'.autopilot/reports/watchdog-failure.json').exists();time.sleep(.5);verify(p,name,'FAILED')
    if stale:
        r=f.powershell('runner/run.ps1','-ProjectRoot',p,'-Action','Start','-Recover',timeout=75)
        report=verify(p,'disk_recovery_after_crash','FAILED');assert report['technical_status']=='SUCCESS',(report,r.stderr)
        assert not (p/'.autopilot/WATCHDOG-SIGNAL.json').exists()
p=f.project('cleanup22-clock',global_timeout=10);info=f.approve(p);clock=ROOT/'runtime/run-clocks'/pathlib.Path(info['receipt_path']).name;clock.parent.mkdir(exist_ok=True);clock.write_text(json.dumps({'run_id':info['contract']['run_id'],'started_at':(datetime.datetime.now().astimezone()-datetime.timedelta(minutes=1)).isoformat()}));f.start(p,40);report=verify(p,'persisted_wall_clock','FAILED');assert report['reason']=='GLOBAL_TIMEOUT'
mutex_command=r'$m=New-Object Threading.Mutex($false,"Local\DesarrolladorAutonomo_RunMutex");$held=$false;try{try{$held=$m.WaitOne(0)}catch [Threading.AbandonedMutexException]{$held=$true};if(-not $held){exit 2}}finally{if($held){$m.ReleaseMutex()};$m.Dispose()}'
r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',mutex_command],capture_output=True,text=True,timeout=15);assert r.returncode==0,r.stderr
result={'status':'PASS','cases':cases,'physical_run_mutex_free':True,'pid_reuse_checked_by_birth_time':True,'unknown_processes_killed':0,'success_path_native_evidence':'pending native F22 test'}
(e/'tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'PASS','cases':list(cases)}))
