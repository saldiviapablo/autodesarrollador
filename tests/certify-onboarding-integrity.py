"""Final integrity for the bounded planner and Prepare transport-only change."""
import ast,copy,hashlib,json,pathlib,socket,subprocess,sys,time
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import project_onboarding as data
import project_launcher_ui as ui
E=R/'evidence'/('onboarding-final-integrity-'+time.strftime('%Y%m%d-%H%M%S'));E.mkdir()
checks={};details={};started=time.monotonic()
def before(name):return subprocess.check_output(['git','show','7f9631f:'+name],cwd=R).decode('utf-8-sig')
def sha(path):
    h=hashlib.sha256()
    with pathlib.Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def function(source,name):return next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name==name)
def dump(node):return ast.dump(node,include_attributes=False)
original=before('runner/prepare.py');current=(R/'runner/prepare.py').read_text(encoding='utf-8-sig')
checks['canonical_admission_and_cleanup_ast_unchanged']=all(dump(function(original,n))==dump(function(current,n)) for n in ('admission','identity','cleanup','atomic'))
class TransportOnly(ast.NodeTransformer):
    def visit_Call(self,node):
        if isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='subprocess' and node.func.attr=='run':return ast.Call(func=ast.Name(id='STDIN_TRANSPORT',ctx=ast.Load()),args=[],keywords=[])
        return self.generic_visit(node)
checks['prepare_execute_only_subprocess_transport_changed']=dump(TransportOnly().visit(copy.deepcopy(function(original,'execute'))))==dump(TransportOnly().visit(copy.deepcopy(function(current,'execute'))))
anchor=". (Join-Path $PSScriptRoot 'core.ps1')"
checks['normal_runner_start_body_exactly_unchanged']=before('runner/run.ps1').split(anchor,1)[1]==(R/'runner/run.ps1').read_text(encoding='utf-8-sig').split(anchor,1)[1]
apply=(R/'runner/prepare-apply.ps1').read_text(encoding='utf-8-sig')
checks['two_prepare_revalidations_retained']=apply.count('--validate-only')==2 and apply.index('PREPARE_APPLY_STARTED')>apply.rindex('--validate-only')
frozen=['config/system.yaml','config/security.yaml','config/VERSIONS.lock','runner/core.ps1','runner/contract.py','runner/completion.py','runner/cleanup.ps1','runner/watchdog-monitor.ps1','schemas/run-contract.schema.json','schemas/runner-plan.schema.json','schemas/autopilot-state.schema.json','scripts/inference-lock.ps1','scripts/hermes-pre-tool-hook.py','scripts/security-guard.ps1','scripts/state-manager.ps1','scripts/invoke-hermes.ps1','scripts/invoke-hermes-role.ps1','scripts/invoke-qwen-code.ps1','scripts/invoke-delegation.ps1','tools']
checks['frozen_guards_budgets_and_normal_wrappers_unchanged']=subprocess.run(['git','diff','--exit-code','7f9631f','--',*frozen],cwd=R,capture_output=True).returncode==0
protected=data.read(R/'evidence/launcher-integrity-20261015-234108/RESULT.json')['details']['protected']
details['protected']={p:{'expected':v['expected'],'actual':sha(p)} for p,v in protected.items()}
checks['six_protected_hashes']=all(v['actual']==v['expected'] for v in details['protected'].values())
historical=data.read(R/'evidence/final-global-audit-20261015-184713/HISTORICAL-MANIFEST.json');changed=[p for p,v in historical.items() if sha(R/p)!=v]
details.update(historical_files=len(historical),historical_changes=changed);checks['historical_evidence_unchanged']=not changed
for port in (8080,9119):
    with socket.socket() as s:s.settimeout(.5);checks['port_'+str(port)+'_free']=s.connect_ex(('127.0.0.1',port))!=0
for name in ('Local\\DesarrolladorAutonomo_RunMutex','DesarrolladorAutonomo_InferenceMutex'):
    lock=ui.Mutex(name);lock.close();checks[name+'_FREE']=True
receipt=data.read(R/'runtime/project-launcher/LONG-PLANNER-TEST.json');bound=data.read(pathlib.Path(receipt['final_certification'])/'UNAPPROVED-BOUND.json')
checks['owned_model_exited']=ui.birth(bound['planner']['model_pid'])!=bound['planner']['model_start_ticks']
code="[Console]::OutputEncoding=New-Object Text.UTF8Encoding($false);Get-CimInstance Win32_Process | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"
raw=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',code],capture_output=True,env=ui.ENV,timeout=15);rows=json.loads(raw.stdout.decode('utf-8-sig'))
owned_paths=[str(R/n).lower() for n in ('runner/plan-objective.ps1','scripts/onboarding_hermes.py','runner/prepare-apply.ps1')]
survivors=[x['ProcessId'] for x in rows if any(p in (x.get('CommandLine') or '').lower() for p in owned_paths)]
checks['no_own_preflight_or_prepare_processes']=not survivors;details['survivors']=survivors
checks['supervisor_profile_unchanged']=data.main({'action':'planner_runtime'})['status']=='PASS'
result={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'details':details,'duration_seconds':time.monotonic()-started,'inferences':0,'gui_actions':0,'old_E2E_phases_repeated':[]}
(E/'.gitattributes').write_bytes(b'* -text\n');(E/'RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'checks':checks,'evidence':str(E)},ensure_ascii=False),flush=True);raise SystemExit(0 if result['status']=='PASS' else 1)
