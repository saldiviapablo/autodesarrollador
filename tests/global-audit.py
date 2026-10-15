"""F26 regression/audit preparation. Executes only after real2h and4h PASS.

No historical evidence is overwritten. No ChatGPT send, software update, push or
local inference is requested; the actual long native workloads bind live roles.
"""
from pathlib import Path
import argparse,base64,datetime,hashlib,json,os,re,subprocess,sys,time,uuid
R=Path(__file__).resolve().parents[2]
if not(R/'AGENTS.md').exists():R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tests'))
from endurance_controller import READ,write,sha,ps,q,PYTHON
PY=PYTHON;HP=sys.executable
def owns_fixture_metadata(auto,state,declared):
 try:relative=Path(auto).relative_to(R/'sandbox')
 except ValueError:return False
 if not relative.parts or Path(auto).name!='.autopilot':return False
 root=R/'sandbox'/relative.parts[0]
 if root.resolve() in declared:return True
 if not re.fullmatch(r'7b-[A-Za-z0-9_-]+-[0-9a-f]{8}',root.name):return False
 if state.get('objective')=='Implement correct addition with verified tests':return True
 return root.name.startswith('7b-prepare-') and state.get('objective')=='Explicit prepare generates run id'

def admit_sandbox_fixture(destination,declared,reuse=False):
 root=(R/'sandbox').resolve();destination=Path(destination).resolve()
 assert root.is_relative_to(R.resolve()) and destination!=root and destination.is_relative_to(root),'FRESH_OWNED_SANDBOX_REQUIRED'
 if reuse:assert destination in declared and destination.is_dir(),'ONLY_THIS_AUDITS_INITIALIZED_FIXTURE_MAY_BE_REUSED'
 else:assert not destination.exists(),'FRESH_OWNED_SANDBOX_REQUIRED'
 return destination

def prepare_bridge_integrity_fixture(destination):
 # This is the unchanged historical test's pre-suite fixture, not a new
 # security approval. Bind to the reviewed bridge commit, then prove it does
 # not change while deterministic reconciliation/send-path tests execute.
 destination=Path(destination)
 assert destination.is_dir() and not (destination/'integrity-before.json').exists(),'FRESH_BRIDGE_INTEGRITY_FIXTURE_REQUIRED'
 approved=subprocess.check_output(['git','show','fe8126d:tools/chatgpt-bridge.js'],cwd=R)
 current=(R/'tools/chatgpt-bridge.js').read_bytes()
 assert approved.replace(b'\r\n',b'\n')==current.replace(b'\r\n',b'\n'),'APPROVED_BRIDGE_CHANGED'
 write(destination/'integrity-before.json',{'protected':{'tools/chatgpt-bridge.js':hashlib.sha256(current).hexdigest()},'source':'Reviewed fe8126d source verified before deterministic suites; current raw bytes captured for nonmutation check'})

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--final',action='store_true');args=parser.parse_args()
 install=READ(R/'config/INSTALLATION-STATE.json');v=install['validation_8'];assert v.get('f25')==v.get('4h')=='PASS','ACTUAL_2H_AND_4H_REQUIRED'
 if args.final:assert all(v.get(n)=='PASS' for n in ['f26','f27','f28']),'ALL_ACTUAL_FINAL_PHASES_REQUIRED'
 assert READ(R/'runtime/overnight/endurance-active.json')['status']!='RUNNING','NO_AUDIT_DURING_ACTIVE_STAGE'
 active_pointer=R/'runtime/overnight/audit-active.json'
 if active_pointer.exists():assert READ(active_pointer).get('status')!='RUNNING','EXISTING_OR_INTERRUPTED_AUDIT_REQUIRES_DISK_RECONCILIATION_NO_DUPLICATE'
 assert not subprocess.check_output(['git','status','--porcelain=v1'],cwd=R,text=True).strip(),'CLEAN_GIT_REQUIRED'
 E=R/'evidence'/(('final-global-audit-' if args.final else 'phase-26-audit-')+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'));E.mkdir(exist_ok=False)
 birth=ps('(Get-Process -Id '+str(os.getpid())+').StartTime.ToUniversalTime().Ticks')
 audit_state={'kind':'AUDIT_TEST_ORCHESTRATION_NOT_NATIVE_STATE','phase':'FINAL_GLOBAL_AUDIT' if args.final else 'F26','status':'RUNNING','controller_pid':os.getpid(),'controller_birth_ticks':birth,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'evidence':str(E),'completed_suites':0,'current_suite':'freeze source/history manifests','next_action':'Observe this exact PID/birth. Do not duplicate after quota interruption. Native STATE remains authoritative.'}
 write(active_pointer,audit_state)
 (E/'.gitattributes').write_text('* -text whitespace=-blank-at-eol,-blank-at-eof,space-before-tab,cr-at-eol\n',encoding='utf-8')
 previous={str(p.relative_to(R)):sha(p) for p in (R/'evidence').rglob('*') if p.is_file() and E not in p.parents}
 write(E/'HISTORICAL-MANIFEST.json',previous)
 tracked=subprocess.check_output(['git','ls-files','runner','scripts','tools','tests','schemas','config'],cwd=R,text=True).splitlines()
 sources={n:sha(R/n) for n in tracked if (R/n).is_file()}
 write(E/'SOURCE-MANIFEST.json',sources)
 write(E/'ADMISSION.json',{'kind':'FINAL_GLOBAL_AUDIT' if args.final else 'F26_AUDIT','git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'controller_pid':os.getpid(),'controller_birth_ticks':birth,'python_optimize_flag':sys.flags.optimize,'source_files':len(sources),'historical_files':len(previous),'audit_script_sha256':sha(__file__),'wrapper_sha256':sha(Path(__file__).with_name('run-owned-audit-gate.ps1')),'adapter_sha256':sha(Path(__file__).with_name('relocate-audit-test.py')),'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'native_inference_requested':False,'bridge_send_requested':False})
 sandbox_before={p.resolve() for p in (R/'sandbox').iterdir() if p.is_dir()}
 write(E/'SANDBOX-BASELINE.json',sorted(map(str,sandbox_before)))
 declared_fixture_roots=set()
 def owned_fixture_locks():
  found=[]
  for p in (R/'sandbox').iterdir():
   if not p.is_dir() or p.is_symlink() or p.is_junction() or p.resolve() in sandbox_before:continue
   assert p.resolve().is_relative_to((R/'sandbox').resolve())
   for current,dirs,files in os.walk(p,followlinks=False):
    dirs[:]=[n for n in dirs if n!='.git' and not(Path(current)/n).is_symlink() and not(Path(current)/n).is_junction()]
    if Path(current).name=='.autopilot' and 'LOCK.json' in files:found.append(Path(current))
  return found
 def cleanup_fixture_metadata():
  receipts=[]
  for a in owned_fixture_locks():
   # These are new test-only directories; preserve measured state/metadata before
   # the normal terminal transition and exact-owner metadata release. Never touch
   # any pre-existing historical run/sandbox.
   state=READ(a/'STATE.json');lock=READ(a/'LOCK.json');assert state['run_id']==lock['run_id']
   # Never turn an unrelated newly created project into a test fixture merely
   # because it was created during this audit. Exact explicit F26 roots or the
   # established labelled factory's name/objective must both identify it.
   assert owns_fixture_metadata(a,state,declared_fixture_roots),'UNOWNED_NEW_METADATA_PRESERVED:'+str(a)
   d=E/'fixture-cleanup'/hashlib.sha256(str(a).encode()).hexdigest();d.mkdir(parents=True)
   for n in ['STATE.json','STATE.md','LOCK.json','EVENTS.jsonl']:
    if (a/n).exists():(d/(n+'.before')).write_bytes((a/n).read_bytes())
   result=ps('. '+q(R/'runner/core.ps1')+';. '+q(R/'runner/cleanup.ps1')+';$auto='+q(a)+';$s=Get-Content -LiteralPath (Join-Path $auto "STATE.json") -Raw -Encoding UTF8|ConvertFrom-Json;$l=Get-Content -LiteralPath (Join-Path $auto "LOCK.json") -Raw -Encoding UTF8|ConvertFrom-Json;$path=Test-WorkspacePathGuard -TargetFilePath $auto -WorkspacePath '+q(R/'sandbox')+' -Operation WRITE;if(-not $path.Allowed){throw "FIXTURE_PHYSICAL_SCOPE_DENIED"};if(@(Get-RunnerSurvivors $auto).Count){throw "FIXTURE_PROCESS_SURVIVES"};$owner=Get-Process -Id $l.owner_pid -ErrorAction SilentlyContinue;if($owner -and $owner.StartTime.ToUniversalTime() -le ([datetimeoffset]$l.started_at).UtcDateTime.AddSeconds(1)){throw "FIXTURE_OWNER_STILL_ALIVE_PRESERVED"};if($s.status -notin @("COMPLETED","FAILED","ABORTED","STALLED","BLOCKED_REQUIRES_HUMAN")){$s.status="ABORTED";$s.current_task="Terminal audit fixture cleanup; no active native run";$null=Write-AtomicState -StateObj $s -AutopilotDir $auto};Remove-RunnerOwnedLock $auto $s.run_id $l.owner_pid;@{status="PASS";auto=$auto;lock_removed=(-not(Test-Path -LiteralPath (Join-Path $auto "LOCK.json")));terminal=$s.status}')
   assert result['status']=='PASS' and result['lock_removed'];receipts.append(result)
  write(E/'FIXTURE-CLEANUP.json',{'status':'PASS','new_fixture_locks_released':receipts,'preexisting_historical_sandboxes_modified':False})
 results={};env=dict(os.environ,PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',F24_PREFLIGHT_E=str(E/'deterministic'),F24_HARNESS='tests/test-phase24-attempt11-live.py',OVERNIGHT_REVIEWER_E=str(E/'reviewer'),CHATGPT_TEST_EVIDENCE_DIR=str(E/'chatgpt'),PSModulePath='C:/Windows/System32/WindowsPowerShell/v1.0/Modules')
 for n in ['deterministic','reviewer','chatgpt']:(E/n).mkdir()
 prepare_bridge_integrity_fixture(E/'chatgpt')
 def run(name,argv,timeout=120,marker=None):
  audit_state.update(current_suite=name,updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat());write(active_pointer,audit_state)
  start=time.monotonic();payload=base64.b64encode(json.dumps({'evidence':str(E),'name':name,'argv':list(map(str,argv)),'timeout':timeout,'controller_pid':os.getpid(),'controller_birth_ticks':birth},ensure_ascii=False).encode()).decode()
  p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-File',str(Path(__file__).with_name('run-owned-audit-gate.ps1')),'-PayloadBase64',payload],cwd=R,env=env,capture_output=True,timeout=timeout+75,creationflags=0x08000000)
  (E/(name+'.wrapper.stdout.txt')).write_bytes(p.stdout);(E/(name+'.wrapper.stderr.txt')).write_bytes(p.stderr)
  process=READ(E/(name+'.process.json'));output=(E/(name+'.stdout.txt')).read_bytes();error=(E/(name+'.stderr.txt')).read_bytes()
  ok=p.returncode==0 and process['status']=='PASS' and process['owned_job_closed'] and process['owned_process_exited'] and (marker is None or marker.encode() in output)
  results[name]={'status':'PASS' if ok else 'FAIL','process':process,'duration_seconds':time.monotonic()-start,'argv':list(map(str,argv))}
  write(E/'PROGRESS.json',results);print(json.dumps({name:results[name]['status']}),flush=True)
  audit_state.update(completed_suites=len(results));write(active_pointer,audit_state)
  assert ok,name+': '+error[-1500:].decode('utf-8',errors='replace')+' '+str(process['reason'])
 def relocated(name,directory=None,timeout=120):
  argv=[PY,str(Path(__file__).with_name('relocate-audit-test.py')),'--test',name,'--output',str(E/('relocated-'+name))]
  if directory:argv+=['--directory',directory]
  run('relocated-'+name,argv,timeout)
 def psfile(name,script,*args,timeout=120,marker=None,reuse_owned_sandbox=False):
  if '-SandboxDir' in args:
   destination=admit_sandbox_fixture(args[args.index('-SandboxDir')+1],declared_fixture_roots,reuse_owned_sandbox)
   declared_fixture_roots.add(destination);write(E/'DECLARED-FIXTURE-ROOTS.json',sorted(map(str,declared_fixture_roots)))
  run(name,['powershell.exe','-NoProfile','-NonInteractive','-File',R/script,*args],timeout,marker)
 failure=None
 try:
  psfile('central-config','scripts/verify-config.ps1','-LogFile',str(E/'central-config.log.txt'))
  continuity=R/'sandbox'/('f26-continuity-'+uuid.uuid4().hex[:8])
  for kind,script in [('state','test-fase10-state.ps1'),('recovery-memory','test-fase11-recovery.ps1'),('security','test-fase15-security.ps1')]:
   extra=['-LogFile',str(E/(kind+'.log.txt'))] if kind!='security' else []
   destination=continuity if kind in ['state','recovery-memory'] else R/'sandbox'/('f26-security-'+uuid.uuid4().hex[:8])
   psfile(kind,'tests/'+script,'-SandboxDir',str(destination),'-EvidenceDir',str(E/kind),*extra,timeout=180,reuse_owned_sandbox=kind=='recovery-memory')
  psfile('checkpoint-integrity','tests/test-checkpoint-integrity.ps1','-SandboxDir',str(R/'sandbox'/('f26-checkpoint-'+uuid.uuid4().hex[:8])))
  psfile('anti-loop-timeouts','tests/test-fase16-anti-loop.ps1','-EvidenceDir',str(E/'anti-loop'),timeout=180)
  psfile('inference-lock','tests/test-inference-lock.ps1','-EvidenceDir',str(E/'lock'),'-LogFile',str(E/'lock.log.txt'),timeout=180)
  psfile('domain-powershell','tests/test-chatgpt-domain-lock.ps1')
  psfile('bridge-child-timeout-cleanup','tests/test-chatgpt-child-cleanup.ps1')
  psfile('budget-state-merge','tests/test-runner-budget-merge.ps1')
  run('atomic-budget-smoke',[PY,Path(__file__).with_name('test-audit-budget-smoke.py'),E/'budget-race'],120)
  psfile('reviewer-core','tests/test-reviewer-core.ps1','-EvidenceRoot',str(E/'reviewer'))
  for name in ['domain-lock','conversation','composer-identity','composer-prepare','pointer-preflight','send-actuator','single-physical-click','delivery','idempotency','human-reconciliation','fresh-chat','transaction']:
   run('chatgpt-'+name,['node.exe',R/'tests'/('test-chatgpt-'+name+'.js')],60)
  run('controlled-utf8-deterministic',['node.exe',R/'tests/test-controlled-send-utf8.js'],60)
  for name in ['test-reviewer-contract.py','test-hermes-prompt-transport.py','test-research-handoff.py','test-qwen-research-model-input.py','test-recovery-continuation.py','test-phase20.py','test-phase22.py','test-endurance-controller.py','test-windows-launcher-adapter.py','test-f24-frozen-evaluator.py','test-f24-runtime-dependencies.py']:
   # Schema/transport modules need the canonical main Python; controller uses psutil.
   exe=HP if name in ['test-endurance-controller.py','test-phase22.py','test-f24-runtime-dependencies.py'] else PY
   run(name,[exe,R/'tests'/name],180)
  run('audit-entry-guards',[HP,Path(__file__).with_name('test-audit-entry-guards.py')],60)
  run('audit-secret-comparison',[HP,Path(__file__).with_name('test-audit-secret-scan.py')],60)
  if args.final:run('pilot-controller-controls',[HP,R/'tests/test-pilot-controllers.py'],60)
  for name,directory,timeout in [
   ('test-phase23-pathguard.py','evidence/phase-23-attempt-3',180),
   ('test-phase23-prepare-admission.py','evidence/phase-23-attempt-3',180),
   ('test-phase23-prepare-boundary.py','evidence/phase-23-attempt-3',90),
   ('test-phase17-admission.py',None,140),('test-phase18-controls.py','evidence/phase-18',160),
   ('test-phase18-progress-lock.py',None,90),('test-phase19.py','evidence/phase-19',90),
   ('test-phase21.py','evidence/phase-21',160),('test-phase22-report-failure.py',None,90),
   ('test-chatgpt-state-schema.py',None,60),('verify-regression-environment.py',None,60),
  ]:relocated(name,directory,timeout)
  # SHA/policy/role bindings use the approved F23 security fix and current live
  # certified bridge, rather than obsolete pre-fix source hashes from7A.
  cfg=json.loads(subprocess.check_output([PY,str(R/'scripts/mcp-sandbox-server.py'),'--dump-yaml-json',str(R/'config/system.yaml')],encoding='utf-8'))
  security=json.loads(subprocess.check_output([PY,str(R/'scripts/mcp-sandbox-server.py'),'--dump-yaml-json',str(R/'config/security.yaml')],encoding='utf-8'))
  checks={};check=lambda n,x:checks.update({n:bool(x)})
  required={'7A.1':['T-7A-MEM-001','T-7A-MEM-002','T-7A-SKILL-001','T-7A-SKILL-002','T-7A-HIERARCHY-001','T-7A-HOOK-001'],'7A.2':['T-7A-MCP-001','T-7A-MCP-002','T-7A-MCP-003','T-7A-MCP-004','T-7A-MCP-005','T-7A-PLUGIN-001','T-7A-PLUGIN-002'],'7A.3':[f'T-7A-DOC-{i:03}' for i in range(1,6)],'7A.4':[f'T-7A-BROWSER-{i:03}' for i in range(1,6)],'7A.5':['T-7A-BOT-001','T-7A-BOT-002','T-7A-SUBAGENT-001'],'7A.6':[f'T-7A-WT-{i:03}' for i in range(1,4)],'7A.7':['T-7A-CRON-001','T-7A-CRON-002'],'7A.8':[f'T-7A-DASH-{i:03}' for i in range(1,4)],'7A.9':['T-7A-GATEWAY-001','T-7A-GATEWAY-002'],'7A.10':['T-7A-UPDATE-001','T-7A-UPDATE-002']}
  for number in range(1,11):
   name=f'evidence/phase-7a{number}/phase-7a{number}-summary.json' if number<=4 else 'evidence/phase-7a5/SUMMARY.json' if number==5 else f'evidence/phase-7a{number}/tests.json';record=READ(R/name);tests=record.get('tests',record.get('data',{}).get('tests',{}));check(f'7A.{number}-mandatory-history',(record.get('status')=='PASS' or record.get('all_passed') is True) and bool(tests) and all(x=='PASS' for x in tests.values()) and all(tests.get(n)=='PASS' for n in required[f'7A.{number}']))
  for number in range(3,11):check(f'7A.{number}-prior-smoke',READ(R/f'evidence/phase-7a{number}/regression-smoke.json')['status']=='PASS')
  check('F23-certified-history',install['phases_8']['23']=='PASS' and READ(R/'evidence/hermes-prompt-transport-20261014/fix-and-f23-gate.json')['status']=='PASS')
  check('F24-all28-current',READ(R/'evidence/phase-24-attempt-11-20261015/FINAL.json')['GATES_PASS']==28 and READ(R/'evidence/phase-24-attempt-11-20261015/FROZEN-GATE-RESULT.json')['status']=='PASS')
  for n in ['config/security.yaml','scripts/inference-lock.ps1','scripts/hermes-pre-tool-hook.py','scripts/hermes-memory-guard.ps1','scripts/progress-guard.ps1','schemas/run-contract.schema.json']:
   old=subprocess.check_output(['git','show','8502d79:'+n],cwd=R);check('original-frozen-'+n,old.replace(b'\r\n',b'\n')==(R/n).read_bytes().replace(b'\r\n',b'\n'))
  for n in ['scripts/security-guard.ps1','scripts/hermes-mcp-plugin-guard.ps1','scripts/canonical_path.py']:
   old=subprocess.check_output(['git','show','6e0a507:'+n],cwd=R);check('approved-pathguard-'+n,old.replace(b'\r\n',b'\n')==(R/n).read_bytes().replace(b'\r\n',b'\n'))
  for n in ['scripts/governed-worktree.py','scripts/gateway-notify.py','scripts/controlled-update.py','scripts/governed-cron.py','scripts/invoke-governed-cron.ps1','scripts/jobs/health-snapshot.py','config/cron-catalog.json','scripts/governed-dashboard.py','scripts/invoke-native-dashboard.ps1','config/VERSIONS.lock']:
   approved=subprocess.check_output(['git','show','597431b:'+n],cwd=R);check('approved-7A-component-'+n,approved.replace(b'\r\n',b'\n')==(R/n).read_bytes().replace(b'\r\n',b'\n'))
  check('model-pins',[cfg['llama'][n] for n in ['alias','host','port','ctx_size','parallel']]==['qwen36','127.0.0.1',8080,65536,1])
  for key,minimum in [('f25',7200),('4h',14400)]:
   e=R/v[key+'_evidence'];s=READ(e/'SUMMARY.json');check(key+'-actual-duration',s['status']=='PASS' and s['duration_seconds']>=minimum and all(s['gates'].values()));check(key+'-independent-closure',READ(e/'INDEPENDENT-CLOSURE.json')['status']=='PASS')
   frozen=READ(e/'FROZEN.json')['sources']
   for n,h in frozen.items():
    if n.startswith(('runner/','scripts/','tools/')):check(key+'-current-source-'+n,sha(R/n)==h)
   for t in s['tasks']:check(key+'-native-task-'+str(t['index']),READ(Path(t['project'])/'.autopilot/STATE.json')['status']=='COMPLETED')
   first=Path(s['tasks'][0]['project'])/'.autopilot';chat=READ(first/'evidence/CHATGPT.json');retry=READ(first/'evidence/CHATGPT-RETRY.json');check(key+'-real-chatgpt-utf8',chat['status']=='SUCCESS' and chat['source_text_equals_dom_text'] and chat['composer_cleared']);check(key+'-real-idempotency',retry['status']=='ALREADY_SENT' and retry['additional_physical_sends']==0 and retry['ledger_unchanged'])
  if args.final:
   pilot=R/v['f27_evidence'];night=R/v['f28_evidence'];review=READ(v['f27_human_review_receipt']);n=READ(night/'SUMMARY.json');pg=READ(night/'PILOT-GATE.json')
   check('F27-human-final-review',review['method']=='HUMAN_FINAL_REVIEW' and review['decision']=='ACCEPTED' and bool(review.get('human_confirmation_reference')))
   check('F27-reviewed-files-unchanged',all(sha(Path(review['project'])/name)==h for name,h in review['reviewed_files'].items()))
   check('F27-native-completion',READ(Path(review['project'])/'.autopilot/STATE.json')['status']=='COMPLETED')
   check('F27-technical-closure',READ(pilot/'INDEPENDENT-TECHNICAL-CLOSURE.json')['status']=='PASS')
   check('F28-actual6to8h',n['status']=='PASS' and 21600<=n['duration_seconds']<=28800 and all(n['gates'].values()))
   check('F28-pilot-gate',pg['status']=='PASS' and all(pg['checks'].values()) and sha(v['f27_human_review_receipt'])==pg['review_receipt_sha256'])
   check('F28-independent-closure',READ(night/'INDEPENDENT-CLOSURE.json')['status']=='PASS')
   for t in n['tasks']:
    native=Path(t['project'])/'.autopilot';check('F28-native-'+str(t['index']),READ(native/'STATE.json')['status']=='COMPLETED' and READ(native/'evidence/completion-gate.json')['status']=='COMPLETED')
    check('F28-full-readonly-'+str(t['index']),READ(night/'tasks'/str(t['index']).zfill(3)/'reviewer-full-target.json')['status']=='PASS')
   chain=READ(night/'PILOT-CHAIN.json');check('F28-memory-chain',len(chain)==len(n['tasks']) and all(t['predecessor_unchanged'] and sha(Path(t['project'])/'module.py')==t['module_after_sha256'] and sha(Path(t['project'])/'artifact-report.json')==t['report_after_sha256'] for t in chain))
   frozen=READ(night/'FROZEN.json')['sources'];check('F28-runtime-current',all(sha(R/name)==h for name,h in frozen.items() if name.startswith(('runner/','scripts/','tools/'))))
   first=Path(n['tasks'][0]['project'])/'.autopilot';chat=READ(first/'evidence/CHATGPT.json');retry=READ(first/'evidence/CHATGPT-RETRY.json');check('F28-bridge-utf8-idempotent',chat['status']=='SUCCESS' and chat['source_text_equals_dom_text'] and chat['composer_cleared'] and retry['status']=='ALREADY_SENT' and retry['additional_physical_sends']==0)
  # Frozen binaries/native runtime and each protected security/plugin component.
  protected=READ(R/'evidence/phase-24-attempt-11-20261015/protected-final.json') if (R/'evidence/phase-24-attempt-11-20261015/protected-final.json').exists() else READ(R/'evidence/phase-24-attempt-5-20261014/protected-final.json')
  for n,h in protected['hashes'].items():check('protected-'+n,sha(n)==h)
  native=Path(cfg['document_extraction']['native_source_dir']);check('hermes-head',subprocess.check_output(['git','-C',str(native),'rev-parse','HEAD'],text=True).strip()==cfg['hermes']['commit']);check('hermes-checkout-clean',not subprocess.check_output(['git','-C',str(native),'status','--porcelain'],text=True).strip());check('hermes-0216',READ(native/'install-stamp.json')['baseVersion']=='0.21.6')
  for n,h in [('tools/read_extract.py',cfg['document_extraction']['native_read_extract_sha256']),('tools/file_tools.py',cfg['document_extraction']['native_file_tools_sha256']),('tools/browser_tool.py',cfg['native_browser']['native_module_sha256'])]:check('native-source-'+n,sha(native/n)==h)
  check('macros1-6',all(install['macrophases'][str(i)]=='PASS' for i in range(1,7)));check('7A',all(install['subphases_7a'][f'7A.{i}']=='PASS' for i in range(1,11)));check('7B',all(install['phases_7b'][str(i)]=='PASS' for i in range(17,23)))
  # Existing governed capability wrappers, fresh evidence outputs, no agent calls.
  for action,script,extra in [('VerifyHookIntegrity','hermes-memory-guard.ps1',''),('SanitizeText','hermes-memory-guard.ps1'," -Text ('sk-'+('X'*25))"),('TestMcpHealth','hermes-mcp-plugin-guard.ps1',''),('VerifyPluginIntegrity','hermes-mcp-plugin-guard.ps1',''),('CheckMcpToolCall','hermes-mcp-plugin-guard.ps1',' -McpToolName da_echo'),('CheckMcpToolCall','hermes-mcp-plugin-guard.ps1',' -McpToolName da_forbidden_test')]:
   r=ps('((& '+q(R/'scripts'/script)+' -Action '+action+extra+') -join "`n")|ConvertFrom-Json');write(E/(action+('-deny' if 'forbidden' in extra else '')+'.json'),r)
   if action=='SanitizeText':check('secret-sanitization',r['was_modified'] and r['sanitized_text']=='[REDACTED]')
   elif 'forbidden' in extra:check('mcp-deny',not r['allowed'])
   elif action=='TestMcpHealth':check('mcp-health',r['health_state']=='HEALTHY')
   else:check(action,r['allowed'])
  psfile('documents-browser-smoke','scripts/verify-7a-prior-capabilities.ps1','-EvidencePath',str((E/'documents-browser.json').relative_to(R)),timeout=120)
  # Cron/UI/updates remain bound to their prior source-certified evidence. Actual
  # state/listeners and empty registries are inspected, not an old PASS alone.
  psfile('cron-dashboard','scripts/verify-capabilities-7a7-7a8.ps1','-EvidencePath',str((E/'cron-dashboard.json').relative_to(R)),timeout=90)
  worktree=R/'sandbox/phase7a6-worktrees';check('worktree-registry-empty',READ(worktree/'.autopilot/worktrees.json')=={});check('worktree-cleanup',subprocess.check_output(['git','-C',str(worktree),'worktree','list','--porcelain'],text=True).count('worktree ')==1)
  check('controlled-update-never-production',READ(R/'evidence/phase-7a10/tests.json')['actual_update_executed'] is False)
  cleanup_fixture_metadata()
  mutexes=ps(r'''$busy=@();$abandoned=@();foreach($name in @('DesarrolladorAutonomo_InferenceMutex','Local\DesarrolladorAutonomo_RunMutex','Local\DesarrolladorAutonomo_EnduranceStage')){$m=$null;$held=$false;try{$m=[Threading.Mutex]::OpenExisting($name);try{$held=$m.WaitOne(0)}catch [Threading.AbandonedMutexException]{$held=$true;$abandoned+=$name};if(-not $held){$busy+=$name}}catch [Threading.WaitHandleCannotBeOpenedException]{}finally{if($held){$m.ReleaseMutex()};if($m){$m.Dispose()}}};@{busy=$busy;abandoned_acquired_and_released=$abandoned}''');write(E/'PHYSICAL-MUTEXES.json',mutexes);check('all-physical-kernel-mutexes-free',not mutexes['busy'])
  cleanup=ps('. '+q(R/'runner/core.ps1')+';. '+q(R/'runner/cleanup.ps1')+';@{inference=(Test-RunnerInferenceReleased);ports=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object {$_.LocalPort -in @(8080,9119)}|Select-Object LocalPort,OwningProcess);mcp=@(Get-CimInstance Win32_Process|Where-Object {$_.Name -match "^python.*exe$" -and $_.CommandLine -match "mcp-sandbox-server.py"}|Select-Object ProcessId,CommandLine)}');write(E/'CLEANUP.json',cleanup);check('cleanup',cleanup['inference']=='FREE' and not cleanup['ports'] and not cleanup['mcp'] and not owned_fixture_locks())
  check('historical-evidence-unchanged',all(sha(R/n)==h for n,h in previous.items()))
  check('executed-sources-unchanged',all(sha(R/n)==h for n,h in sources.items()))
  write(E/'AUDIT-CHECKS.json',checks);assert all(checks.values()),'AUDIT_CHECKS_FAILED:'+','.join(n for n,x in checks.items() if not x)
 except Exception as exc:
  failure=str(exc)
  try:cleanup_fixture_metadata()
  except Exception as cleanup_error:failure+='; FIXTURE_CLEANUP_FAILED '+str(cleanup_error)
 status='PASS' if not failure else 'FAIL';write(E/'SUMMARY.json',{'status':status,'failure':failure,'tests':results,'historical_files':len(previous),'no_push':True,'new_dependencies':[]});audit_state.update(status=status,failure=failure,current_suite=None,updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),next_action='Independent terminal verification, documentary closure and local commit before next phase' if status=='PASS' else 'Preserve this failure, diagnose/certify isolated correction and owned cleanup before a fresh audit');write(active_pointer,audit_state);print(json.dumps({'status':status,'failure':failure,'evidence':str(E)}),flush=True);return 0 if status=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
