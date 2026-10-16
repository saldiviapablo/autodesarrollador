"""Read-only stream parsing and graceful preparation failure; no GUI/inference."""
import ast,base64,hashlib,json,os,pathlib,subprocess,sys,time,uuid
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import project_onboarding as data
BASE=R/'sandbox'/('launcher-failure-'+uuid.uuid4().hex[:8]);BASE.mkdir()
E=R/'evidence'/('launcher-failure-cert-'+time.strftime('%Y%m%d-%H%M%S'));E.mkdir()
env=dict(os.environ,PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',PSModulePath='C:/Windows/System32/WindowsPowerShell/v1.0/Modules')
checks={};details={}
def service(request):
    r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-File',str(R/'scripts/project-launcher-action.ps1')],input=json.dumps(request,ensure_ascii=False).encode('utf-8'),capture_output=True,env=env,timeout=100)
    return r,json.loads(r.stdout.decode('utf-8-sig'))
def git(p,*args):subprocess.run(['git','-C',str(p),*args],check=True,capture_output=True,env=env,timeout=20)

# Only the affected canonical-preparation case is repeated; the other original
# 19 tests remain certified. This new fixture deliberately rejects one commit.
tree=ast.parse((R/'tests/test-project-onboarding.py').read_text(encoding='utf-8'));node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='proposal')
ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),'fixture','exec'),ns)
p=BASE/'git-failure';p.mkdir();(p/'baseline.txt').write_text('Owned integration fixture\n')
git(p,'init','-q');git(p,'config','user.name','DA Fixture');git(p,'config','user.email','fixture@example.invalid');git(p,'add','--','baseline.txt');git(p,'commit','-q','-m','fixture baseline')
hook=p/'.git/hooks/pre-commit';hook.write_text('#!/bin/sh\nexit 1\n',encoding='utf-8')
b=data.bind_proposal(p,'Implement addition in this isolated failure fixture',ns['proposal']())
r,v=service(dict(b,action='approve_plan',decision='APPROVE',method='HUMAN_PLAN_REVIEW'));assert r.returncode==0,v
r,v=service(dict(b,action='prepare',approval_id=v['approval_id'],new_objective=False))
details['failure_response']=v;checks['git_error_observed']=r.returncode!=0 and 'GIT_OPERATION_FAILED:commit' in v['reason']
state=data.read(p/'.autopilot/STATE.json');hb=data.read(p/'.autopilot/HEARTBEAT.json')
checks['error_terminal_state']=state['status']==hb['status']=='BLOCKED_REQUIRES_HUMAN'
checks['error_lock_released']=not (p/'.autopilot/LOCK.json').exists()
checks['error_report_exists']=(p/'.autopilot/reports/runner-result.json').exists()
checks['error_checkpoint_exists']=bool(list((p/'.autopilot/checkpoints').iterdir()))
checks['no_worker_started']=not (p/'.autopilot/PROCESSES.json').exists()
checks['baseline_unchanged']=(p/'baseline.txt').read_text()=='Owned integration fixture\n'
checks['canonical_contract_not_approved_on_git_failure']=not data.contract.inspect(p)['contract']['authorized']
checks['cleanup_report_pass']=v.get('cleanup')=='PASS'
(E/'PREPARATION-FAILURE-CLEANUP.json').write_text(json.dumps({'checks':checks,'response':v,'project':str(p)},indent=2),encoding='utf-8')

# Existing project instructions must be preserved through canonical admission,
# not overwritten or removed to make the initializer accept the folder.
existing=BASE/'existing-qwen';existing.mkdir();original='# Reglas propias\nConservar UTF-8: á ñ € °\n'
(existing/'QWEN.md').write_text(original,encoding='utf-8')
bound=data.bind_proposal(existing,'Implement addition in the existing-guidance fixture',ns['proposal']())
r,grant=service(dict(bound,action='approve_plan',decision='APPROVE',method='HUMAN_PLAN_REVIEW'));assert r.returncode==0,grant
r,prepared=service(dict(bound,action='prepare',approval_id=grant['approval_id'],new_objective=False));assert r.returncode==0,prepared
checks['existing_qwen_preserved']=(existing/'QWEN.md').read_text(encoding='utf-8')==original
checks['existing_qwen_backup_verified']=any((d/'QWEN.md').read_text(encoding='utf-8')==original for d in (existing/'.autopilot-history').iterdir())
checks['canonical_generated_qwen_preserved']=(existing/'.autopilot/evidence/PREPARE-QWEN.md').exists()
checks['existing_qwen_prepare_cleanup']=not (existing/'.autopilot/LOCK.json').exists()

def stream(text='{"plan":{},"seed_files":{}}',session='owned-session'):
    return [{'type':'system','subtype':'init','session_id':session},{'type':'result','session_id':session,'text':text}]
cases=[('valid',stream(),True),('wrong_session',stream()[:1]+[dict(stream()[1],session_id='other')],False),
       ('missing_init',stream()[1:],False),('duplicate_result',stream()+stream()[1:],False),
       ('tool_call',stream()[:1]+[{'type':'tool_use'}]+stream()[1:],False),
       ('nested_tool',stream()[:1]+[{'type':'assistant','message':{'content':[{'type':'tool_use'}]}}]+stream()[1:],False),
       ('empty_result',stream(text=''),False)]
# Parse a real, already-certified Supervisor stream, without rerunning its phase.
historical=R/'sandbox/endurance-f27-20261015-165308-d37c78/pilot-002/.autopilot/evidence/roles.json'
before=data.contract.sha(historical);roles=data.read(historical);native=roles['supervisor']['data']['Stdout']
cases.append(('historical_native_format',native,True))
inputs=[]
for name,events,expected in cases:inputs.append({'name':name,'stream':events if isinstance(events,str) else '\n'.join(json.dumps(x) for x in events),'expected':expected})
quote=lambda x:"'"+str(x).replace("'","''")+"'"
code=("$ErrorActionPreference='Stop';. "+quote(R/'scripts/project-launcher-common.ps1')+
      ";[Console]::InputEncoding=New-Object Text.UTF8Encoding($false,$true);$cases=[Console]::In.ReadToEnd()|ConvertFrom-Json;"+
      "foreach($case in $cases){$ok=$false;$value=$null;try{$value=Read-LauncherPlannerStream $case.stream;$ok=$true}catch{};@{name=$case.name;pass=($ok -eq $case.expected);session_id=$value.session_id}|ConvertTo-Json -Compress}")
result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(code.encode('utf-16le')).decode()],input=json.dumps(inputs).encode('utf-8'),capture_output=True,env=env,timeout=30)
assert result.returncode==0,result.stderr
parsed=[json.loads(line) for line in result.stdout.decode('utf-8-sig').splitlines() if line.strip()]
for row in parsed:checks['stream_'+row['name']]=row['pass']
checks['historical_source_unchanged']=data.contract.sha(historical)==before
details.update(stream=parsed,historical_sha256=before,project=str(p),scope='Synthetic approval fixtures only; no inference, Start, GUI control or prior phase execution')
report={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'details':details}
(E/'RESULT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':report['status'],'checks':checks,'evidence':str(E)}),flush=True)
raise SystemExit(0 if report['status']=='PASS' else 1)
