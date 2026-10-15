"""Isolated model ownership/adoption/parent-loss certification; zero inference.

Prepared only. Refuses to execute before F24 PASS. Each component case has its
own owner process and model lifecycle; no prolonged phase is claimed here.
"""
from pathlib import Path
import json,os,psutil,subprocess,time,uuid,shutil,hashlib
from endurance_controller import R,ps,q,READ,write,PYTHON
def alive(identity):
 try:return abs(psutil.Process(identity['pid']).create_time()-(identity['start_ticks']/1e7-62135596800))<.01
 except psutil.NoSuchProcess:return False
def start_owner(e,workspace,parent):
 e.mkdir(parents=True);ticks=ps('(Get-Process -Id '+str(parent.pid)+').StartTime.ToUniversalTime().Ticks')
 out=(e/'owner.stdout.txt').open('w',encoding='utf-8');err=(e/'owner.stderr.txt').open('w',encoding='utf-8')
 owner=subprocess.Popen(['powershell.exe','-NoProfile','-NonInteractive','-File',str(Path(__file__).with_name('endurance-model-owner.ps1')),'-ControllerPid',str(parent.pid),'-ControllerBirthTicks',str(ticks),'-EvidenceRoot',str(e),'-Workspace',str(workspace)],stdout=out,stderr=err,creationflags=0x08000000)
 try:
  end=time.monotonic()+180
  while True:
   try:
    if READ(e/'model-ready.json').get('status')=='PASS':break
   except (OSError,ValueError):pass
   if owner.poll() is not None:raise RuntimeError('MODEL_OWNER_ADMISSION_FAILED: '+str(READ(e/'model-cleanup.json')))
   if time.monotonic()>end:raise RuntimeError('MODEL_OWNER_READY_TIMEOUT')
   time.sleep(.2)
  return owner,READ(e/'model-identity.json'),out,err
 except:
  (e/'MODEL-STOP').write_text('component startup cleanup',encoding='utf-8')
  try:owner.wait(timeout=30)
  except subprocess.TimeoutExpired:owner.kill();owner.wait(timeout=5)
  out.close();err.close();raise
def main():
 assert READ(R/'config/INSTALLATION-STATE.json')['validation_8'].get('f24_ready_for_f25') is True,'F24_REQUIRED_BEFORE_MODEL_COMPONENT_CERTIFICATION'
 E=R/'evidence'/('endurance-owner-cert-'+uuid.uuid4().hex[:8]);E.mkdir()
 P=R/'sandbox'/('endurance-owner-cert-'+uuid.uuid4().hex[:8]);P.mkdir();project=P/'project';project.mkdir()
 for name,text in [('module.py','print("probe")\n'),('check.py','print("OWNER_COMPONENT_PROBE")\n'),('.gitignore','.autopilot/\n')]: (project/name).write_text(text,encoding='utf-8')
 for args in [['init','-q'],['config','user.name','DA Ownership Component'],['config','user.email','sandbox@example.invalid'],['add','--','module.py','check.py','.gitignore'],['commit','-q','-m','Ownership component baseline']]:subprocess.run(['git','-C',str(project),*args],check=True,capture_output=True)
 plan={'schema_version':'1.0','backend':'probe','task':'Ownership component only, no agent','allowed_files':['module.py'],'tests':[{'id':'unit','argv':['python','check.py'],'marker':'OWNER_COMPONENT_PROBE','timeout_seconds':10}],'builds':[],'criteria':[{'criterion':'owned external model adoption only','test_id':'unit'}],'artifacts':[{'path':'module.py'}],'immutable_files':[],'global_timeout_seconds':60,'phase_timeout_seconds':15,'restart_budget':0,'max_cycles':1};write(P/'plan.json',plan)
 prepared=ps('& '+q(R/'runner/run.ps1')+' -Action Prepare -ProjectRoot '+q(project)+' -Objective '+q('Model ownership component certification only')+' -AcceptanceCriteria '+q('owned external model adoption only')+' -PlanPath '+q(P/'plan.json')+' | ConvertFrom-Json');assert prepared['status']=='PASS'
 for args in [['add','--','QWEN.md'],['commit','-q','-m','Generated component QWEN memory baseline']]:subprocess.run(['git','-C',str(project),*args],check=True,capture_output=True)
 admission=json.loads(subprocess.check_output([PYTHON,str(R/'runner/contract.py'),'inspect','--project',str(project)],encoding='utf-8'))
 approval=json.loads(subprocess.check_output([PYTHON,str(R/'runner/contract.py'),'approve','--project',str(project),'--digest',admission['digest']],encoding='utf-8'));write(E/'approval.json',approval)
 owner=None;dummy=None;cases={}
 try:
  owner,identity,out,err=start_owner(E/'normal',P,psutil.Process())
  result=ps('. '+q(R/'runner/core.ps1')+';$script:Admission=Get-RunnerAdmission "validate" '+q(project)+' '+q(approval['digest'])+';$script:Cfg=((& C:/Python314/python.exe '+q(R/'scripts/mcp-sandbox-server.py')+' --dump-yaml-json '+q(R/'config/system.yaml')+') -join "`n")|ConvertFrom-Json;$script:Auto=$script:Admission.auto;$script:RunId=$script:Admission.contract.run_id;$script:Owned=@{};$script:ExternalModel=$null;Start-RunnerModel;if($script:ExternalModel.pid -ne '+str(identity['pid'])+'){throw "ADOPTION_IDENTITY_MISMATCH"};@{status="PASS";external_model=$script:ExternalModel;health=(Test-RunnerHealth);owned_process_count=$script:Owned.Count}')
  assert result['status']=='PASS' and result['health'] and result['owned_process_count']==0
  assert alive(identity),'NATIVE_ADOPTER_STOPPED_EXTERNAL_MODEL'
  write(E/'normal/native-adoption.json',result);(E/'normal/MODEL-STOP').write_text('normal component cleanup',encoding='utf-8');owner.wait(timeout=30);out.close();err.close();assert owner.returncode==0 and not alive(identity);cases['normal_adoption_cleanup']='PASS';owner=None
  dummy=subprocess.Popen([PYTHON,'-c','import time;time.sleep(150)'],creationflags=0x08000000);dummy_birth=psutil.Process(dummy.pid).create_time()
  owner,identity,out,err=start_owner(E/'controller-loss',P,psutil.Process(dummy.pid))
  assert abs(psutil.Process(dummy.pid).create_time()-dummy_birth)<.01;dummy.kill();dummy.wait(timeout=10);dummy=None
  owner.wait(timeout=30);out.close();err.close();cleanup=READ(E/'controller-loss/model-cleanup.json');assert owner.returncode==1 and cleanup['reason']=='CONTROLLER_LOST' and cleanup['model_exited'] and not alive(identity);cases['controller_loss_owned_model_job_cleanup']='PASS';owner=None
 finally:
  if dummy and dummy.poll() is None:dummy.kill();dummy.wait(timeout=10)
  if owner and owner.poll() is None:
   for e in [E/'normal',E/'controller-loss']:
    if e.exists():(e/'MODEL-STOP').write_text('component finalization',encoding='utf-8')
   try:owner.wait(timeout=30)
   except subprocess.TimeoutExpired:owner.kill();owner.wait(timeout=5)
  a=project/'.autopilot';ps('. '+q(R/'runner/core.ps1')+';. '+q(R/'runner/cleanup.ps1')+';$s=Get-Content -LiteralPath '+q(a/'STATE.json')+' -Raw -Encoding UTF8|ConvertFrom-Json;$s.status="ABORTED";$s.next_action="Ownership component closed; no full Runner/inference or duration phase claimed";$null=Write-AtomicState -StateObj $s -AutopilotDir '+q(a)+' -ValidateTransition $false;$lp=Join-Path '+q(a)+' "LOCK.json";if(Test-Path -LiteralPath $lp){$l=Get-Content -LiteralPath $lp -Raw -Encoding UTF8|ConvertFrom-Json;Remove-RunnerOwnedLock '+q(a)+' $s.run_id $l.owner_pid};@{status="PASS"}')
 assert len(cases)==2
 end=ps('. '+q(R/'runner/core.ps1')+';. '+q(R/'runner/cleanup.ps1')+';@{inference=(Test-RunnerInferenceReleased);ports=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object {$_.LocalPort -in @(8080,9119)}|Select-Object LocalPort,OwningProcess)}')
 assert end['inference']=='FREE' and not end['ports'] and not(project/'.autopilot/LOCK.json').exists()
 shutil.copytree(project/'.autopilot',E/'native-component');write(E/'CERTIFIED.json',{'status':'PASS','cases':cases,'cleanup':end,'local_inferences':0,'chatgpt_sends':0,'prolonged_phase_started':False,'model_pins':'qwen36/127.0.0.1:8080/ctx65536/parallel1','project':str(project),'scope':'Actual model owner lifecycle and production Start-RunnerModel adoption function, not a complete Runner workload'})
 print(json.dumps({'status':'PASS','evidence':str(E),'cases':cases}))
if __name__=='__main__':main()
