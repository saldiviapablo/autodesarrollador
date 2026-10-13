import ctypes,importlib.util,json,pathlib,subprocess,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('fixtures',ROOT/'tests/runner-fixtures.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
p=f.project('restart-budget',delay=30,phase_timeout=1,global_timeout=60)
plan=p/'.autopilot/RUN-PLAN.json';data=json.loads(plan.read_text());data['restart_budget']=1;plan.write_text(json.dumps(data));f.approve(p)
r=f.start(p,timeout=70);result=json.loads((p/'.autopilot/reports/runner-result.json').read_text(encoding='utf-8-sig'))
assert result['status']=='FAILED' and 'BUDGET_EXHAUSTED' in result['reason'],result
assert json.loads((p/'.autopilot/RESTARTS.json').read_text())['supervisor']==1
stale=f.project('heartbeat-stale',delay=20,phase_timeout=25,global_timeout=70)
plan=stale/'.autopilot/RUN-PLAN.json';data=json.loads(plan.read_text());data['heartbeat_stale_seconds']=1;plan.write_text(json.dumps(data));f.approve(stale)
proc=subprocess.Popen(['powershell.exe','-NoProfile','-NonInteractive','-File',str(ROOT/'runner/run.ps1'),'-ProjectRoot',str(stale),'-Action','Start'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
deadline=time.monotonic()+15
while not(stale/'.autopilot/WATCHDOG.json').exists() and time.monotonic()<deadline:time.sleep(.1)
assert (stale/'.autopilot/WATCHDOG.json').exists()
kernel=ctypes.WinDLL('kernel32');kernel.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong];kernel.OpenProcess.restype=ctypes.c_void_p
nt=ctypes.WinDLL('ntdll');nt.NtSuspendProcess.argtypes=[ctypes.c_void_p]
handle=kernel.OpenProcess(0x0800,False,proc.pid);assert handle
assert nt.NtSuspendProcess(handle)==0
kernel.CloseHandle.argtypes=[ctypes.c_void_p];kernel.CloseHandle(handle)
proc.wait(timeout=15)
state=json.loads((stale/'.autopilot/STATE.json').read_text(encoding='utf-8-sig'));assert state['status']=='FAILED',state
assert (stale/'.autopilot/reports/watchdog-failure.json').exists() and not(stale/'.autopilot/LOCK.json').exists()
report={'status':'PASS','tests':{'T-WATCH-001':'PASS','T-WATCH-002':'PASS','T-WATCH-005':'PASS'},'heartbeat_independent_watchdog':True,'owned_parent_suspended_and_reaped':True,'restart_budget_limit':1,'restart_budget_observed':1,'terminal_after_budget_exhausted':'FAILED','projects':[str(p),str(stale)]}
e=ROOT/'evidence/phase-18';e.mkdir(exist_ok=True);(e/'controls.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
