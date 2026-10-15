"""F27 local disposable pilot. Technical completion never fabricates human review.

Prepared for execution only after F26 PASS. Shares the already-certified test
model owner/monitor with endurance; productive Runner/guards remain unchanged.
"""
from pathlib import Path
import datetime,json,os,shutil,subprocess,sys,time,uuid
import psutil
R=Path(__file__).resolve().parents[2]
if not(R/'AGENTS.md').exists():R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tests'))
from endurance_controller import Stage,READ,write,sha,ps,q,PYTHON
from pilot_workload import pilot_fixture
class Pilot(Stage):
 def __init__(self):
  super().__init__('F27')
  # Stage creates a fresh dedicated case. Its path is within the user's
  # explicitly authorized workspace/sandbox; no personal repository is chosen.
  self.model_out=None;self.model_err=None
 def _persist_locked(self):
  v={'kind':'PILOT_TEST_ORCHESTRATION_NOT_NATIVE_STATE','stage':'F27','stage_id':self.id,'status':self.terminal or ('FAIL' if self.failure else 'RUNNING'),'controller_pid':os.getpid(),'controller_birth':psutil.Process().create_time(),'started_at':self.wall,'elapsed_seconds':time.monotonic()-self.started if self.started else 0,'current_native_project':str(self.active) if self.active else None,'tasks':self.tasks,'evidence':str(self.E),'failure':self.failure,'human_review':'NOT_PERFORMED','next_action':'Observe existing native Runner; no duplicate or frozen-source edits' if not self.terminal else 'Review technical report/diff/output, then obtain actual final human review required07§30. No F27 PASS or F28 before that review.'}
  write(self.E/'STATE.json',v)
  if self.admitted:write(R/'runtime/overnight/pilot-active.json',v)
 def guard(self):
  if self.resource_failure:raise RuntimeError(self.resource_failure)
  if self.owner and self.owner.poll() is not None:raise RuntimeError('MODEL_OWNER_TERMINATED')
  if self.started and time.monotonic()-self.started>1900:raise RuntimeError('PILOT_NORMAL_GLOBAL_BUDGET_EXHAUSTED')
 def fixture(self,index):return pilot_fixture()
 def run_task(self,index):
  import threading
  done=threading.Event();snapshots=[];seen=set();observer_errors=[]
  def snapshot(p):
   files={}
   for root,dirs,names in os.walk(p):
    dirs[:]=[d for d in dirs if d not in ['.git','.autopilot','__pycache__']]
    for name in names:
     f=Path(root)/name;files[f.relative_to(p).as_posix()]=sha(f)
   return {'files':files,'git_head':self.git(p,'rev-parse','HEAD')}
  def observe():
   while not done.wait(.1):
    p=self.active
    if not p:continue
    try:records=READ(p/'.autopilot/PROCESSES.json')
    except (OSError,ValueError):continue
    for item in records.get('processes',[]):
     if item['name']=='reviewer' and item['pid'] not in seen:
      try:snapshots.append({'pid':item['pid'],'target':snapshot(p)});seen.add(item['pid'])
      except Exception as exc:observer_errors.append(str(exc));return
  watcher=threading.Thread(target=observe,daemon=True);watcher.start();completed=False
  try:Stage.run_task(self,index);completed=True
  finally:done.set();watcher.join(timeout=10)
  if completed:
   p=Path(self.tasks[-1]['project']);after=snapshot(p);assert snapshots and not observer_errors and snapshots[-1]['target']==after,'FULL_PILOT_REVIEWER_READONLY_NOT_PROVEN'
   write(self.E/'tasks'/str(index+1).zfill(3)/'reviewer-full-target.json',{'status':'PASS','scope':'Final accepted Reviewer; earlier baselines preserved, legitimate intervening Worker corrections are not Reviewer writes','before':snapshots,'final_accepted_reviewer_pid':snapshots[-1]['pid'],'after':after,'git_head_unchanged':True,'all_target_content_unchanged':True,'excluded_runtime_directories':['.autopilot','.git internals (HEAD checked independently)','__pycache__']})
 def prepare_task(self,index):
  self.assert_sources();v=self.fixture(index);P=self.case/('pilot-'+str(index+1).zfill(3));P.mkdir();self.active=P
  for n,text in v['files'].items():(P/n).write_text(text,encoding='utf-8')
  for args in [('init','-q'),('config','user.name','DA Local Pilot'),('config','user.email','sandbox@example.invalid'),('checkout','-b','agent/'+self.id),('add','--',*v['files']),('commit','-q','-m','Backed up noncritical local pilot before autonomous work')]:self.git(P,*args)
  e=self.E/'tasks'/str(index+1).zfill(3);e.mkdir(parents=True)
  self.backup=sha(P/'module.py');shutil.copytree(P,e/'pilot-original-backup',ignore=shutil.ignore_patterns('.git','__pycache__'));write(e/'pilot-original-git.json',{'head':self.git(P,'rev-parse','HEAD'),'branch':self.git(P,'branch','--show-current'),'status':self.git(P,'status','--porcelain=v1'),'tracked_files':{n:sha(P/n) for n in v['files']},'git_repository_preserved_in_actual_sandbox':str(P/'.git'),'git_internals_excluded_from_evidence_export':True})
  initial=subprocess.run([PYTHON,'test_module.py'],cwd=P,capture_output=True,timeout=30);(e/'initial-test.stdout.txt').write_bytes(initial.stdout);(e/'initial-test.stderr.txt').write_bytes(initial.stderr)
  if self.phase=='F27' or index==0:assert initial.returncode!=0
  pins=[{'path':n,'sha256':sha(P/n)} for n in v.get('immutable_files',['test_module.py','build.py','sample-records.json'])]
  criterion=v.get('criterion','Exact validated report totals/rounding, Unicode JSON/Markdown CLI, immutable complete acceptance, tests/build and documentation')
  plan={'schema_version':'1.0','backend':'live','task':'First run python test_module.py; diagnose any failure. '+v['task'],'allowed_files':v.get('allowed_files',['module.py','README.md','artifact-report.json','REPORT.md']),'tests':[{'id':'unit','argv':['python','test_module.py'],'marker':'ENDURANCE_TEST_PASS','timeout_seconds':30}],'builds':[{'id':'build','argv':['python','build.py'],'marker':'ENDURANCE_BUILD_PASS','timeout_seconds':30}],'criteria':[{'criterion':criterion,'test_id':'unit'}],'artifacts':[{'path':n} for n in v.get('artifacts',['module.py','README.md','artifact-report.json','REPORT.md'])],'immutable_files':pins,'phase_timeout_seconds':300,'global_timeout_seconds':1800,'restart_budget':2,'max_cycles':5}
  if self.phase=='F27' or index==0:plan['research']={'url':'https://docs.python.org/3/library/decimal.html','diagnose_before_fetch':True}
  if self.phase=='F28' and index==0:plan.update(sandbox_crash_boundary=True,consultation={'id':self.id+'-consult-'+uuid.uuid4().hex[:12],'question':'Auditoría breve de reportes JSON con Decimal ROUND_HALF_UP y comparación de totales/estados. Riesgos de entrada inválida, no finitos y preservación UTF-8. Máximo100palabras; incluye áéíóú ñ.','response_timeout_seconds':60,'after_recovery':True,'new_conversation':True})
  planpath=self.case/('RUN-PLAN-input-'+str(index)+'.json');write(planpath,plan)
  result=ps('& '+q(R/'runner/run.ps1')+' -Action Prepare -ProjectRoot '+q(P)+' -Objective '+q(v['objective'])+' -AcceptanceCriteria '+q(criterion)+' -PlanPath '+q(planpath)+' | ConvertFrom-Json');assert result['status']=='PASS'
  a=P/'.autopilot';cp=a/'RUN-CONTRACT.yaml';code="import pathlib,sys,yaml;p=pathlib.Path(sys.argv[1]);v=yaml.safe_load(p.read_text(encoding='utf-8-sig'));v['time_budget_minutes']=30;p.write_text(yaml.safe_dump(v,sort_keys=False,allow_unicode=True),encoding='utf-8')";subprocess.run([PYTHON,'-c',code,str(cp)],check=True,capture_output=True)
  state=READ(a/'STATE.json');state['max_cycles']=5;write(a/'STATE.json',state);ps('. '+q(R/'scripts/state-manager.ps1')+';$s=Get-Content -LiteralPath '+q(a/'STATE.json')+' -Raw -Encoding UTF8|ConvertFrom-Json;$null=Write-AtomicState -StateObj $s -AutopilotDir '+q(a)+' -ValidateTransition $false;@{status="PASS"}')
  self.git(P,'add','--','QWEN.md');self.git(P,'commit','-q','-m','Generated native memory baseline before single approval')
  preflight=ps('& '+q(R/'runner/run.ps1')+' -Action Preflight -ProjectRoot '+q(P)+' | ConvertFrom-Json');assert preflight['status']=='PASS'
  info=json.loads(subprocess.check_output([PYTHON,str(R/'runner/contract.py'),'inspect','--project',str(P)],encoding='utf-8'));approval=json.loads(subprocess.check_output([PYTHON,str(R/'runner/contract.py'),'approve','--project',str(P),'--digest',info['digest']],encoding='utf-8'))
  for n,value in [('fixture.json',v),('prepare.json',result),('preflight.json',preflight),('approval.json',approval)]:write(e/n,value)
  self.persist();return P,e,v,approval
 def run_pilot(self):
  cleanup=False;integrity=False
  try:
   lease=self.k.WaitForSingleObject(self.mutex,0);assert lease in [0,0x80],'EXISTING_TEST_STAGE_PRESERVED';self.held=True;self.admitted=True;assert self.k.SetThreadExecutionState(0x80000001)
   self.freeze();self.persist();ticks=ps('(Get-Process -Id '+str(os.getpid())+').StartTime.ToUniversalTime().Ticks')
   self.model_out=(self.E/'model-owner.stdout.txt').open('w',encoding='utf-8');self.model_err=(self.E/'model-owner.stderr.txt').open('w',encoding='utf-8')
   self.owner=subprocess.Popen(['powershell.exe','-NoProfile','-NonInteractive','-File',str(R/'tests/endurance-model-owner.ps1'),'-ControllerPid',str(os.getpid()),'-ControllerBirthTicks',str(ticks),'-EvidenceRoot',str(self.E),'-Workspace',str(self.case)],stdout=self.model_out,stderr=self.model_err,creationflags=0x08000000)
   end=time.monotonic()+180
   while True:
    try:
     if READ(self.E/'model-ready.json').get('status')=='PASS':break
    except (OSError,ValueError):pass
    if self.owner.poll() is not None or time.monotonic()>end:raise RuntimeError('MODEL_ADMISSION_FAILED')
    time.sleep(.25)
   self.started=time.monotonic();self.wall=datetime.datetime.now(datetime.timezone.utc).isoformat()
   import threading
   self.watcher=threading.Thread(target=self.monitor,daemon=True);self.watcher.start();self.persist()
   # The shared task driver reserves slot0 for prolonged-stage crash/consultation.
   # This pilot uses slot1: one normal complete native launcher/Runner workload.
   self.run_task(1);self.guard()
  except Exception as exc:
   self.failure=str(exc)
   if self.active and (self.active/'.autopilot').exists():shutil.copytree(self.active/'.autopilot',self.E/'failure-native')
  finally:
   try:cleanup=self.cleanup()
   except Exception as exc:self.failure=(self.failure or '')+'; CLEANUP '+str(exc)
   for handle in [self.model_out,self.model_err]:
    if handle:handle.close()
   try:
    self.assert_sources();bad=[n for n,h in self.history.items() if sha(R/n)!=h];protected=[n for n,h in self.protected.items() if sha(n)!=h];integrity=not bad and not protected;write(self.E/'INTEGRITY.json',{'status':'PASS' if integrity else 'FAIL','historical_mismatches':bad,'protected_mismatches':protected})
   except Exception as exc:self.failure=(self.failure or '')+'; INTEGRITY '+str(exc)
  if self.resource_failure:self.failure=self.failure or self.resource_failure
  technical=not self.failure and cleanup and integrity and len(self.tasks)==1
  self.terminal='TECHNICAL_PASS_AWAITING_HUMAN_REVIEW' if technical else 'FAIL';self.persist()
  s={'status':self.terminal,'F27':'BLOCKED_REQUIRES_HUMAN' if technical else 'FAIL','failure':self.failure,'stage_id':self.id,'tasks':self.tasks,'duration_seconds':time.monotonic()-self.started if self.started else None,'cleanup':cleanup,'integrity':integrity,'human_review':'NOT_PERFORMED','source_authorization':'Overnight user approval for a dedicated disposable safe pilot inside workspace/sandbox; no personal project','no_push':True}
  write(self.E/'resources.json',{'samples':self.samples,'gpu':self.gpu});write(self.E/'SUMMARY.json',s);print(json.dumps({'status':self.terminal,'evidence':str(self.E)}),flush=True);return 0 if technical else 1
def main():
 v=READ(R/'config/INSTALLATION-STATE.json')['validation_8'];assert v.get('f26')=='PASS' and v.get('f25')==v.get('4h')=='PASS','F26_AND_PROLONGED_GATES_REQUIRED'
 assert not subprocess.check_output(['git','status','--porcelain=v1'],cwd=R,text=True).strip(),'CLEAN_WORKTREE_REQUIRED'
 assert READ(R/'runtime/overnight/endurance-active.json')['status']!='RUNNING'
 prior=R/'runtime/overnight/pilot-active.json'
 if prior.exists():assert READ(prior)['status']!='RUNNING','EXISTING_PILOT_REQUIRES_DISK_RECONCILIATION'
 raise SystemExit(Pilot().run_pilot())
if __name__=='__main__':main()
