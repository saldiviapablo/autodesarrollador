"""Real-duration test workload controller over the unchanged authoritative Runner.

Uses only native Prepare/approval/launcher/Watchdog/Start-Recover/Completion.
No inference API is called by this controller. All roles keep the native mutex.
"""
from pathlib import Path
import argparse,base64,ctypes,datetime as dt,hashlib,json,os,shutil,subprocess,sys,threading,time,uuid,urllib.request
import psutil
from endurance_workloads import fixture
R=Path(__file__).resolve().parents[2]
if not (R/'AGENTS.md').exists():R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tests'))
from windows_launcher_adapter import launch_batch
PYTHON='C:/Python314/python.exe'
DURATIONS={'F25':7200,'4H':14400,'F28':21600}
READ=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.'+uuid.uuid4().hex+'.writing');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 try:
  for attempt in range(6):
   try:os.replace(tmp,p);return
   except PermissionError:
    if attempt==5:raise
    time.sleep(.03)
 finally:
  if tmp.exists():tmp.unlink()
def q(v):return "'"+str(v).replace("'","''")+"'"

def launch_native(project,*,recover=False,stdout,stderr):
 # The visible batch launcher accepts PROJECT_ROOT only. Recovery is the native
 # run.ps1 -Action Start -Recover path, as certified in the complete F24 E2E.
 if not recover:return launch_batch(R/'INICIAR-DESARROLLADOR-AUTONOMO.bat',[str(project)],cwd=R,env=os.environ.copy(),stdout=stdout,stderr=stderr)
 return subprocess.Popen(['powershell.exe','-NoProfile','-NonInteractive','-File',str(R/'runner/run.ps1'),'-ProjectRoot',str(project),'-Action','Start','-Recover'],cwd=R,env=os.environ.copy(),stdout=stdout,stderr=stderr,creationflags=0x08000000)
def ps(body,timeout=90):
 code="$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules';$env:PYTHONUTF8='1';$env:PYTHONDONTWRITEBYTECODE='1';[Console]::OutputEncoding=[Text.Encoding]::UTF8;$r=& {"+body+"};Write-Output 'STAGE_JSON';$r|ConvertTo-Json -Depth 28 -Compress"
 p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-OutputFormat','Text','-EncodedCommand',base64.b64encode(code.encode('utf-16le')).decode()],capture_output=True,timeout=timeout,creationflags=0x08000000)
 # Windows PowerShell may encode its diagnostic stream with the OEM code page.
 # Preserve raw diagnostics; the authoritative JSON stream still requires UTF-8.
 output=p.stdout.decode('utf-8')
 if p.stderr:
  d=R/'logs/overnight/adapter-diagnostics';d.mkdir(parents=True,exist_ok=True);(d/(uuid.uuid4().hex+'.stderr.raw')).write_bytes(p.stderr)
 if p.returncode:raise RuntimeError('NATIVE_ADAPTER_FAILED: '+p.stderr[-1000:].decode('utf-8',errors='replace')+output[-500:])
 return json.loads(output.rsplit('STAGE_JSON',1)[1].strip())
def validate_stage(stage,elapsed,tasks,resource,integrity,cleanup):
 return {'real_duration':elapsed>=DURATIONS[stage], 'night_upper_bound':stage!='F28' or elapsed<=28800,
 'several_tasks':len(tasks)>=3,'varied_workloads':len({t['workload'] for t in tasks})>=3,
 'native_completion_every_task':bool(tasks) and all(t.get('status')=='PASS' for t in tasks),
 'actual_recovery':bool(tasks) and tasks[0].get('actual_recovery') is True,
 'checkpoints_each_task':bool(tasks) and all(t.get('checkpoints',0)>=1 for t in tasks),
 'native_clocks_preserved':bool(tasks) and all(t.get('clock_preserved') is True for t in tasks),
 'reviewers_readonly':bool(tasks) and all(t.get('reviewer_readonly') is True for t in tasks),
 'continuous_monitoring':resource.get('samples',0)>=DURATIONS[stage]//10 and isinstance(resource.get('max_sample_gap'),(int,float)) and resource['max_sample_gap']<=30,
 'no_sustained_critical_ram':resource.get('critical') is False,'integrity':integrity,'cleanup':cleanup}
class Stage:
 def __init__(self,phase):
  self.phase=phase;self.admitted=False;self.persistence_lock=threading.RLock();self.id=phase.lower()+'-'+dt.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6]
  self.E=R/'evidence'/('endurance-'+self.id);self.case=R/'sandbox'/('endurance-'+self.id)
  self.E.mkdir(exist_ok=False);self.case.mkdir(exist_ok=False)
  self.tasks=[];self.samples=[];self.gpu=[];self.failure=None;self.terminal=None;self.active=None;self.native=None;self.native_birth=None;self.owner=None;self.started=None;self.wall=None;self.monitor_stop=threading.Event();self.resource_failure=None;self.seen={};self.last_gpu=0
  self.k=ctypes.WinDLL('kernel32',use_last_error=True)
  self.k.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_wchar_p];self.k.CreateMutexW.restype=ctypes.c_void_p
  self.k.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_uint32];self.k.ReleaseMutex.argtypes=[ctypes.c_void_p];self.k.CloseHandle.argtypes=[ctypes.c_void_p]
  self.k.SetThreadExecutionState.argtypes=[ctypes.c_uint32];self.k.SetThreadExecutionState.restype=ctypes.c_uint32
  self.mutex=self.k.CreateMutexW(None,False,'Local\\DesarrolladorAutonomo_EnduranceStage');self.held=False
 def event(self,name,**v):
  row={'at':dt.datetime.now(dt.timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-self.started if self.started else None,'event':name,**v}
  with (self.E/'EVENTS.jsonl').open('a',encoding='utf-8') as h:h.write(json.dumps(row,ensure_ascii=False)+'\n')
  print(json.dumps(row,ensure_ascii=False),flush=True)
 def persist(self):
  with self.persistence_lock:self._persist_locked()
 def _persist_locked(self):
  value={'kind':'TEST_WORKLOAD_ORCHESTRATION_NOT_NATIVE_STATE','stage':self.phase,'stage_id':self.id,'status':self.terminal or ('RUNNING' if not self.failure else 'FAIL'),'controller_pid':os.getpid(),'controller_birth':psutil.Process().create_time(),'started_at':self.wall,'duration_required':DURATIONS[self.phase],'elapsed_seconds':time.monotonic()-self.started if self.started else 0,'current_native_project':str(self.active) if self.active else None,'completed_tasks':self.tasks,'evidence':str(self.E),'failure':self.failure,'next_action':'Observe existing controller; do not duplicate or modify frozen sources. Native .autopilot/STATE remains authoritative.' if not self.terminal else 'Read SUMMARY and byte-exported native evidence. Close documentation/commit; advance only if all gates PASS.'}
  write(self.E/'STATE.json',value)
  if self.admitted:write(R/'runtime/overnight/endurance-active.json',value)
 def freeze(self):
  tracked=subprocess.check_output(['git','ls-files','runner','scripts','tools','tests','schemas','config'],cwd=R,text=True).splitlines();self.sources={n:sha(R/n) for n in tracked if (R/n).is_file()}
  bases=[R/n for n in ['evidence','runtime/run-clocks','runtime/run-approvals','runtime/chatgpt-consultations']]+[p for p in (R/'sandbox').iterdir() if p.is_dir() and (p.name.startswith('f24-') or p.name.startswith('endurance-')) and p!=self.case]
  self.history={p.relative_to(R).as_posix():sha(p) for base in bases for p in base.rglob('*') if p.is_file() and self.E not in p.parents}
  # Frozen safety components use the previously verified canonical hashes.
  self.protected=READ(R/'evidence/phase-24-attempt-5-20261014/protected-final.json')['hashes']
  for p,h in self.protected.items():assert sha(p)==h,'PROTECTED_COMPONENT_CHANGED'
  write(self.E/'FROZEN.json',{'sources':self.sources,'history':self.history,'protected':self.protected})
 def assert_sources(self):
  bad=[n for n,h in self.sources.items() if sha(R/n)!=h]
  if bad:raise RuntimeError('FROZEN_SOURCE_CHANGED: '+','.join(bad))
 def monitor(self):
  while not self.monitor_stop.wait(5):
   try:
    now=time.monotonic();m=psutil.virtual_memory();model=READ(self.E/'model-identity.json');proc=psutil.Process(model['pid']);expected=model['start_ticks']/1e7-62135596800
    if abs(proc.create_time()-expected)>.01:raise RuntimeError('MODEL_IDENTITY_CHANGED')
    sample={'at':dt.datetime.now(dt.timezone.utc).isoformat(),'elapsed_seconds':now-self.started,'ram_available_bytes':m.available,'pagefile':psutil.swap_memory()._asdict(),'llama_working_set_bytes':proc.memory_info().rss,'processes':len(psutil.pids()),'current_native_project':str(self.active) if self.active else None}
    with urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=2) as response:sample['model_health']=json.load(response)['status']
    if sample['model_health']!='ok':raise RuntimeError('MODEL_HEALTH_LOST')
    try:sample['inference_owner']=READ(R/'runtime/locks/inference-owner.json')
    except (OSError,ValueError):sample['inference_owner']='FREE_OR_TRANSITION'
    if self.active:
     a=self.active/'.autopilot'
     for n in ['STATE.json','HEARTBEAT.json','RESTARTS.json']:
      try:sample[n]=READ(a/n)
      except (OSError,ValueError):pass
    self.samples.append(sample)
    with (self.E/'resource-samples.jsonl').open('a',encoding='utf-8') as h:h.write(json.dumps(sample,ensure_ascii=False)+'\n');h.flush();os.fsync(h.fileno())
    if len(self.samples)>=3 and all(v['ram_available_bytes']<150*1024**2 for v in self.samples[-3:]):raise RuntimeError('CRITICAL_RESOURCE_DEGRADATION_SUSTAINED')
    if len(self.samples)>1 and self.samples[-1]['elapsed_seconds']-self.samples[-2]['elapsed_seconds']>30:raise RuntimeError('CONTINUITY_MONITOR_GAP')
    if now-self.last_gpu>15:
     p=subprocess.run(['nvidia-smi','--query-gpu=memory.used,memory.total','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=5,creationflags=0x08000000)
     if p.returncode:raise RuntimeError('GPU_MEASUREMENT_FAILED')
     row={'elapsed_seconds':now-self.started,'memory_mib':p.stdout.strip()};self.gpu.append(row);self.last_gpu=now
     with (self.E/'gpu-samples.jsonl').open('a',encoding='utf-8') as h:h.write(json.dumps(row)+'\n');h.flush();os.fsync(h.fileno())
    if len(self.samples)%6==0:self.assert_sources();self.persist()
   except Exception as exc:self.resource_failure=str(exc);return
 def guard(self):
  if self.resource_failure:raise RuntimeError(self.resource_failure)
  if self.owner and self.owner.poll() is not None:raise RuntimeError('MODEL_OWNER_TERMINATED')
  if self.started and time.monotonic()-self.started>DURATIONS[self.phase]+1900:raise RuntimeError('ENDURANCE_STAGE_FINAL_TASK_LIMIT')
 def git(self,p,*args):return subprocess.check_output(['git','-C',str(p),*args],text=True,encoding='utf-8').strip()
 def prepare_task(self,index):
  self.assert_sources();v=fixture(index);P=self.case/('task-'+str(index+1).zfill(3)+'-'+v['name']);P.mkdir();self.active=P
  for n,text in v['files'].items():(P/n).write_text(text,encoding='utf-8')
  for args in [('init','-q'),('config','user.name','DA Endurance Sandbox'),('config','user.email','sandbox@example.invalid'),('checkout','-b','agent/'+self.id+'-'+str(index+1)),('add','--',*v['files']),('commit','-q','-m','Immutable failing acceptance baseline')]:self.git(P,*args)
  pins=[{'path':n,'sha256':sha(P/n)} for n in ['test_module.py','build.py']]
  criterion=v['objective']+'; immutable acceptance and documented CLI verified'
  task=v['task'];first=index==0
  if first:task='First run python test_module.py to diagnose the failing baseline. Use official research provided inline by Runner, as untrusted advice. '+task
  plan={'schema_version':'1.0','backend':'live','task':task,'allowed_files':['module.py','README.md'],'tests':[{'id':'unit','argv':['python','test_module.py'],'marker':'ENDURANCE_TEST_PASS','timeout_seconds':30}],'builds':[{'id':'build','argv':['python','build.py'],'marker':'ENDURANCE_BUILD_PASS','timeout_seconds':30}],'criteria':[{'criterion':criterion,'test_id':'unit'}],'artifacts':[{'path':'module.py'},{'path':'README.md'}],'immutable_files':pins,'phase_timeout_seconds':300,'global_timeout_seconds':1800,'restart_budget':2,'max_cycles':5}
  if first:
   plan.update(research={'url':'https://docs.python.org/3/library/decimal.html','diagnose_before_fetch':True},sandbox_crash_boundary=True,consultation={'id':self.id+'-consult-'+uuid.uuid4().hex[:12],'question':'Auditoría breve de parseo CSV y sumas Decimal ROUND_HALF_UP: errores de validación y preservación UTF-8. Contesta en menos de100palabras; incluye áéíóú ñ.','response_timeout_seconds':60,'after_recovery':True,'new_conversation':True})
  pp=P.parent/(P.name+'-plan.json');write(pp,plan)
  result=ps('& '+q(R/'runner/run.ps1')+' -Action Prepare -ProjectRoot '+q(P)+' -Objective '+q(v['objective'])+' -AcceptanceCriteria '+q(criterion)+' -PlanPath '+q(pp)+' | ConvertFrom-Json');assert result['status']=='PASS',result
  cp=P/'.autopilot/RUN-CONTRACT.yaml';code="import sys,pathlib,yaml;p=pathlib.Path(sys.argv[1]);v=yaml.safe_load(p.read_text(encoding='utf-8-sig'));v['time_budget_minutes']=30;p.write_text(yaml.safe_dump(v,sort_keys=False,allow_unicode=True),encoding='utf-8')"
  subprocess.run([PYTHON,'-c',code,str(cp)],check=True,capture_output=True,timeout=15)
  a=P/'.autopilot';state=READ(a/'STATE.json');state['max_cycles']=5;write(a/'STATE.json',state)
  ps('. '+q(R/'scripts/state-manager.ps1')+';$s=Get-Content -LiteralPath '+q(a/'STATE.json')+' -Raw -Encoding UTF8|ConvertFrom-Json;$null=Write-AtomicState -StateObj $s -AutopilotDir '+q(a)+' -ValidateTransition $false;@{status="PASS"}')
  self.git(P,'add','--','QWEN.md');self.git(P,'commit','-q','-m','Generated QWEN memory baseline before approval');self.guard()
  preflight=ps('& '+q(R/'runner/run.ps1')+' -Action Preflight -ProjectRoot '+q(P)+' | ConvertFrom-Json');assert preflight['status']=='PASS'
  info=json.loads(subprocess.check_output([PYTHON,str(R/'runner/contract.py'),'inspect','--project',str(P)],encoding='utf-8'))
  approval=json.loads(subprocess.check_output([PYTHON,str(R/'runner/contract.py'),'approve','--project',str(P),'--digest',info['digest']],encoding='utf-8'))
  e=self.E/'tasks'/str(index+1).zfill(3);e.mkdir(parents=True);write(e/'fixture.json',v);write(e/'prepare.json',result);write(e/'preflight.json',preflight);write(e/'approval.json',approval)
  self.persist();return P,e,v,approval
 def run_task(self,index):
  P,e,v,approval=self.prepare_task(index);a=P/'.autopilot';clock=R/'runtime/run-clocks'/Path(approval['receipt_path']).name;clock_bytes=None;crash=False;review_before=None;review_pid=None;failure_events=set()
  def target():return {n:sha(P/n) for n in ['module.py','README.md','test_module.py','build.py','QWEN.md','.gitignore']}
  def events():return [json.loads(line) for line in (a/'EVENTS.jsonl').read_text(encoding='utf-8-sig').splitlines() if line.strip()]
  for segment in [1,2] if index==0 else [1]:
   self.guard()
   out=(e/('segment-'+str(segment)+'.stdout.txt')).open('w',encoding='utf-8');err=(e/('segment-'+str(segment)+'.stderr.txt')).open('w',encoding='utf-8')
   self.native=launch_native(P,recover=segment==2,stdout=out,stderr=err)
   self.native_birth=psutil.Process(self.native.pid).create_time();native_parents={};self.event('NATIVE_TASK_STARTED',index=index+1,segment=segment,project=str(P),run_id=approval['contract']['run_id'])
   while self.native.poll() is None:
    self.guard()
    if (a/'EVENTS.jsonl').exists():
     try:observed_events=events()
     except (OSError,ValueError):observed_events=[]
     for event in observed_events:
      if event['type']=='PROCESS_EXITED' and event['payload'].get('exit_code')!=0 and event['seq'] not in failure_events:
       failure_events.add(event['seq']);name=event['payload'].get('name');d=e/'role-failures'/str(event['seq']);d.mkdir(parents=True)
       capture={}
       for suffix in ['stdout.txt','stderr.txt']:
        source=a/'logs'/(name+'.'+suffix)
        if source.exists():shutil.copyfile(source,d/source.name);capture[source.name]=sha(d/source.name)
       write(d/'CAPTURE.json',{'native_event':event,'files':capture,'captured_at':dt.datetime.now(dt.timezone.utc).isoformat()})
    try:records=READ(a/'PROCESSES.json')
    except (OSError,ValueError):records={}
    pid=records.get('runner_pid')
    if pid:
     try:
      p=psutil.Process(pid)
      if any(x.pid==self.native.pid for x in p.parents()):native_parents[pid]=p.create_time()
     except psutil.NoSuchProcess:pass
    if clock.exists() and clock_bytes is None:clock_bytes=clock.read_bytes();write(e/'clock-initial.json',{'path':str(clock),'sha256':sha(clock)})
    if index==0 and segment==1 and not crash and (a/'evidence/checks.json').exists():
     checks=READ(a/'evidence/checks.json')
     if checks.get('tests') and checks.get('builds') and all(x['status']=='PASS' for g in ['tests','builds'] for x in checks[g]):
      parent=psutil.Process(records['runner_pid']);assert native_parents.get(parent.pid)==parent.create_time(),'UNOWNED_CRASH_TARGET'
      parent.suspend();ps('$null=& '+q(R/'scripts/create-autopilot-checkpoint.ps1')+' -ProjectPath '+q(P)+' -CheckpointId '+q('chk-endurance-before-crash-'+uuid.uuid4().hex[:8])+' -Reason '+q('Actual checks PASS before approved controlled parent crash')+';@{status="PASS"}')
      shutil.copytree(a,e/'pre-recovery-native');write(e/'injection.json',{'pid':parent.pid,'birth':parent.create_time(),'checks':checks,'at':dt.datetime.now(dt.timezone.utc).isoformat()});parent.kill();crash=True;self.event('OWNED_PARENT_CRASH',index=index+1)
    for item in records.get('processes',[]):
     if item['name']=='reviewer' and item['pid']!=review_pid:review_pid=item['pid'];review_before=target();write(e/'reviewer-before.json',review_before)
    time.sleep(.2)
   self.native.wait(timeout=15);out.close();err.close()
   if index==0 and segment==1:
    if not crash:
     reason=READ(a/'reports/runner-result.json').get('reason') if (a/'reports/runner-result.json').exists() else (e/'segment-1.stderr.txt').read_text(encoding='utf-8',errors='replace')[-1500:]
     raise RuntimeError('NATIVE_FAILURE_BEFORE_RECOVERY_BOUNDARY: '+str(reason))
    end=time.monotonic()+45
    while not (a/'reports/watchdog-failure.json').exists() and time.monotonic()<end:self.guard();time.sleep(.25)
    assert READ(a/'reports/watchdog-failure.json')['reason']=='PARENT_PROCESS_LOST';self.event('WATCHDOG_CONFIRMED');continue
   assert self.native.returncode==0,'NATIVE_TASK_FAILED: '+str(READ(a/'reports/runner-result.json').get('reason'))
  self.native=None
  report=READ(a/'reports/runner-result.json');gate=READ(a/'evidence/completion-gate.json');checks=READ(a/'evidence/checks.json');state=READ(a/'STATE.json');rows=events();types=[x['type'] for x in rows]
  assert report['status']==state['status']=='COMPLETED' and report['technical_status']=='SUCCESS' and not report['reason']
  assert gate['status']=='COMPLETED' and all(gate['checks'].values())
  assert checks['tests'] and checks['builds'] and all(x['status']=='PASS' for g in ['tests','builds'] for x in checks[g])
  assert clock_bytes==clock.read_bytes(),'RUN_CLOCK_CHANGED'
  assert review_before==target(),'REVIEWER_NOT_READONLY'
  assert not report['cleanup']['errors'] and not report['cleanup']['owned_survivors'] and not (a/'LOCK.json').exists()
  assert report['cleanup']['inference_mutex']=='FREE' and report['cleanup']['run_mutex_released'] is True and report['cleanup']['run_lock_removed'] is True
  plan=READ(a/'RUN-PLAN.json');assert all(sha(P/p['path'])==p['sha256'] for p in plan['immutable_files'])
  assert 'MODEL_ADOPTED_EXTERNAL' in types and report['cleanup']['external_model_preserved'] is True
  recovered=False
  if index==0:
   ri=types.index('RUN_RECOVERED_FROM_DISK');recovered=types.count('RUN_STARTED')==2 and any(r['type']=='PROCESS_EXITED' and r['payload'].get('name')=='worker' and r['payload'].get('exit_code')==0 for r in rows[ri:]);assert recovered
   chat=READ(a/'evidence/CHATGPT.json');retry=READ(a/'evidence/CHATGPT-RETRY.json');assert chat['status']=='SUCCESS' and chat['message_sent'] and chat['response_received'] and chat['source_text_equals_dom_text'] and chat['composer_cleared']
   assert retry['status']=='ALREADY_SENT' and retry['additional_physical_sends']==0 and retry['ledger_unchanged']
  shutil.copytree(a,e/'native');shutil.copytree(P,e/'artifacts',ignore=shutil.ignore_patterns('.git','.autopilot','__pycache__'))
  (e/'worker-diff.patch').write_bytes(subprocess.check_output(['git','-C',str(P),'diff','--binary']))
  checkpoint_count=len(list((a/'checkpoints').glob('*/checkpoint-manifest.json')));assert checkpoint_count>=1
  result={'status':'PASS','index':index+1,'workload':v['name'],'project':str(P),'run_id':approval['contract']['run_id'],'duration_seconds':report['duration_seconds'],'actual_recovery':recovered,'clock_preserved':True,'reviewer_readonly':True,'completion_checks':gate['checks'],'restarts':READ(a/'RESTARTS.json'),'checkpoints':checkpoint_count}
  write(e/'RESULT.json',result);self.tasks.append(result);self.event('NATIVE_TASK_COMPLETED',**result);self.active=None;self.persist()
 def cleanup(self):
  errors=[]
  self.monitor_stop.set()
  if hasattr(self,'watcher'):self.watcher.join(timeout=10)
  if self.native and self.native.poll() is None and self.active:
   try:ps('& '+q(R/'runner/stop.ps1')+' -ProjectRoot '+q(self.active)+' | ConvertFrom-Json',30);self.native.wait(timeout=35)
   except Exception as exc:
    errors.append('NATIVE_STOP: '+str(exc))
    try:
     p=psutil.Process(self.native.pid)
     if abs(p.create_time()-self.native_birth)<.01:p.kill();p.wait(timeout=15)
    except psutil.NoSuchProcess:pass
  if self.owner:
   (self.E/'MODEL-STOP').write_text('owned stage controller finalization\n',encoding='utf-8')
   try:self.owner.wait(timeout=30)
   except subprocess.TimeoutExpired:
    self.owner.kill();self.owner.wait(timeout=10);errors.append('MODEL_OWNER_FORCED_STOP')
  if self.held:self.k.ReleaseMutex(self.mutex);self.held=False
  self.k.CloseHandle(self.mutex);self.k.SetThreadExecutionState(0x80000000)
  check=ps('. '+q(R/'runner/core.ps1')+';. '+q(R/'runner/cleanup.ps1')+';$busy=@();foreach($n in @("DesarrolladorAutonomo_InferenceMutex","Local\\DesarrolladorAutonomo_RunMutex")){$m=$null;$h=$false;try{$m=[Threading.Mutex]::OpenExisting($n);try{$h=$m.WaitOne(0)}catch [Threading.AbandonedMutexException]{$h=$true};if(-not $h){$busy+=$n}}catch [Threading.WaitHandleCannotBeOpenedException]{}finally{if($h){$m.ReleaseMutex()};if($m){$m.Dispose()}}};$listeners=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object {$_.LocalPort -in @(8080,9119)});@{mutexes_busy=$busy;listeners=@($listeners|Select-Object LocalAddress,LocalPort,OwningProcess)}')
  survivors=[]
  if (self.E/'model-identity.json').exists():
   identity=READ(self.E/'model-identity.json')
   try:
    pr=psutil.Process(identity['pid'])
    if abs(pr.create_time()-(identity['start_ticks']/1e7-62135596800))<.01:survivors.append(identity)
   except psutil.NoSuchProcess:pass
  for t in self.tasks+([{'project':str(self.active)}] if self.active else []):
   p=Path(t['project']);a=p/'.autopilot'
   # Prepare creates observational LOCK metadata before an actual Runner starts.
   # If launch admission itself failed, use the existing exact-owner release.
   if (a/'LOCK.json').exists():
    events=[json.loads(x) for x in (a/'EVENTS.jsonl').read_text(encoding='utf-8-sig').splitlines() if x.strip()]
    if not any(x['type']=='RUN_STARTED' for x in events):
     ps('. '+q(R/'runner/core.ps1')+';. '+q(R/'runner/cleanup.ps1')+';$s=Get-Content -LiteralPath '+q(a/'STATE.json')+' -Raw -Encoding UTF8|ConvertFrom-Json;$l=Get-Content -LiteralPath '+q(a/'LOCK.json')+' -Raw -Encoding UTF8|ConvertFrom-Json;Remove-RunnerOwnedLock '+q(a)+' $s.run_id $l.owner_pid;@{status="PASS"}')
   if (a/'PROCESSES.json').exists():
    records=READ(a/'PROCESSES.json')
    for it in records.get('processes',[]):
     try:
      pr=psutil.Process(it['pid'])
      if abs(pr.create_time()-(it['start_ticks']/1e7-62135596800))<.01:survivors.append(it)
     except psutil.NoSuchProcess:pass
   if (a/'LOCK.json').exists():errors.append('NATIVE_LOCK_REMAINS:'+str(p))
  result={'status':'PASS' if not errors and not survivors and not check['mutexes_busy'] and not check['listeners'] else 'FAIL','errors':errors,'survivors':survivors,**check,'preexisting_chrome_preserved':True}
  write(self.E/'CLEANUP.json',result);return result['status']=='PASS'
 def run(self):
  cleanup=False;integrity=False;elapsed=0
  try:
   held=self.k.WaitForSingleObject(self.mutex,0);assert held in [0,0x80],'ENDURANCE_STAGE_ALREADY_ACTIVE';self.held=True;self.admitted=True
   assert self.k.SetThreadExecutionState(0x80000001),'SLEEP_PREVENTION_FAILED'
   self.freeze();self.persist()
   controller_ticks=int((psutil.Process().create_time()+62135596800)*1e7)
   # Get exact .NET ticks rather than rounding Unix seconds at100ns precision.
   controller_ticks=ps('(Get-Process -Id '+str(os.getpid())+').StartTime.ToUniversalTime().Ticks')
   out=(self.E/'model-owner.stdout.txt').open('w',encoding='utf-8');err=(self.E/'model-owner.stderr.txt').open('w',encoding='utf-8')
   owner_script=Path(__file__).with_name('endurance-model-owner.ps1')
   self.owner=subprocess.Popen(['powershell.exe','-NoProfile','-NonInteractive','-File',str(owner_script),'-ControllerPid',str(os.getpid()),'-ControllerBirthTicks',str(controller_ticks),'-EvidenceRoot',str(self.E),'-Workspace',str(self.case)],stdout=out,stderr=err,creationflags=0x08000000)
   end=time.monotonic()+180
   while True:
    try:
     if READ(self.E/'model-ready.json').get('status')=='PASS':break
    except (OSError,ValueError):pass
    if self.owner.poll() is not None:raise RuntimeError('MODEL_OWNER_ADMISSION_FAILED')
    if time.monotonic()>end:raise RuntimeError('MODEL_READY_TIMEOUT')
    time.sleep(.25)
   self.started=time.monotonic();self.wall=dt.datetime.now(dt.timezone.utc).isoformat();write(self.E/'STAGE-CONTRACT.json',{'stage':self.phase,'required_real_seconds':DURATIONS[self.phase],'started_at':self.wall,'monotonic_start':self.started,'model_started_once':True,'per_native_run_global_seconds':1800,'per_phase_seconds':300,'restart_budget':2,'max_cycles':5,'human_interventions_after_start':0});self.event('STAGE_CLOCK_STARTED');self.persist()
   self.watcher=threading.Thread(target=self.monitor,daemon=True);self.watcher.start();index=0
   while time.monotonic()-self.started<DURATIONS[self.phase]:self.guard();self.run_task(index);index+=1
   self.guard();elapsed=time.monotonic()-self.started;self.event('REQUIRED_DURATION_REACHED',actual_seconds=elapsed)
  except Exception as exc:
   self.failure=str(exc);self.event('STAGE_FAILED',reason=self.failure)
   if self.active and (self.active/'.autopilot').exists():shutil.copytree(self.active/'.autopilot',self.E/'failure-native')
  finally:
   if self.started:elapsed=time.monotonic()-self.started
   try:cleanup=self.cleanup()
   except Exception as exc:self.failure=(self.failure or '')+'; CLEANUP_EXCEPTION '+str(exc)
   try:
    self.assert_sources();bad=[p for p,h in self.history.items() if sha(R/p)!=h];protected_bad=[p for p,h in self.protected.items() if sha(p)!=h];integrity=not bad and not protected_bad;write(self.E/'INTEGRITY.json',{'status':'PASS' if integrity else 'FAIL','historical_mismatches':bad,'protected_mismatches':protected_bad,'source_files':len(self.sources),'historical_files':len(self.history),'protected_components':len(self.protected)})
   except Exception as exc:self.failure=(self.failure or '')+'; INTEGRITY_EXCEPTION '+str(exc)
  gaps=[b['elapsed_seconds']-a['elapsed_seconds'] for a,b in zip(self.samples,self.samples[1:])]
  continuity_gaps=gaps+([self.samples[0]['elapsed_seconds'],elapsed-self.samples[-1]['elapsed_seconds']] if self.samples else [])
  resource={'samples':len(self.samples),'max_sample_gap':max(continuity_gaps,default=None),'critical':self.resource_failure is not None,'RAM_min_available_mib':min((r['ram_available_bytes'] for r in self.samples),default=0)/2**20,'pagefile_max_used_gib':max((r['pagefile']['used'] for r in self.samples),default=0)/2**30,'VRAM_max_mib':max((int(r['memory_mib'].split(',')[0]) for r in self.gpu),default=0),'llama_max_working_set_mib':max((r['llama_working_set_bytes'] for r in self.samples),default=0)/2**20}
  gates=validate_stage(self.phase,elapsed,self.tasks,resource,integrity,cleanup);status='PASS' if not self.failure and all(gates.values()) else 'FAIL';summary={'stage':self.phase,'stage_id':self.id,'status':status,'failure':self.failure,'duration_seconds':elapsed,'required_seconds':DURATIONS[self.phase],'tasks':self.tasks,'gates':gates,'resources':resource,'cleanup':cleanup,'integrity':integrity,'no_push':True}
  write(self.E/'resources.json',{'samples':self.samples,'gpu':self.gpu});write(self.E/'SUMMARY.json',summary);self.terminal=status;self.persist();self.event('STAGE_TERMINAL',status=status);return 0 if status=='PASS' else 1
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=DURATIONS,required=True);a=parser.parse_args()
 state=READ(R/'config/INSTALLATION-STATE.json')['validation_8'];assert state.get('f24_ready_for_f25') is True,'F24_MUST_PASS_BEFORE_ENDURANCE'
 if a.stage=='4H':assert state.get('f25')=='PASS','F25_REQUIRED'
 if a.stage=='F28':assert state.get('f26')=='PASS' and state.get('f27')=='PASS','AUDIT_AND_HUMAN_REVIEWED_PILOT_REQUIRED'
 if a.stage=='F28':raise RuntimeError('F28_REQUIRES_DEDICATED_CERTIFIED_PILOT_WORKLOAD; this controller currently certifies F25/4H isolated tasks only')
 prior=R/'runtime/overnight/endurance-active.json'
 if prior.exists():assert READ(prior).get('status')!='RUNNING','EXISTING_OR_INTERRUPTED_STAGE_REQUIRES_DISK_RECONCILIATION_NO_DUPLICATE'
 assert not subprocess.check_output(['git','status','--porcelain=v1'],cwd=R,text=True).strip(),'GIT_MUST_BE_CLEAN_BEFORE_STAGE'
 raise SystemExit(Stage(a.stage).run())
if __name__=='__main__':main()
