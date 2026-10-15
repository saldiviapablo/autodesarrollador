"""Certify unchanged F10/F11 suites on one fresh explicitly owned fixture."""
from pathlib import Path
import base64,datetime,json,os,subprocess,sys,uuid
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tests'))
from endurance_controller import READ,write,sha,ps,q
tag=datetime.datetime.now().strftime('%Y%m%d-%H%M%S');E=R/'evidence'/('audit-continuity-dependency-'+tag);P=R/'sandbox'/('f26-continuity-cert-'+uuid.uuid4().hex[:8]);E.mkdir(exist_ok=False);assert not P.exists()
sources={n:sha(R/n) for n in ['tests/test-fase10-state.ps1','tests/test-fase11-recovery.ps1','scripts/state-manager.ps1','scripts/recover-autopilot.ps1']}
birth=ps('(Get-Process -Id '+str(os.getpid())+').StartTime.ToUniversalTime().Ticks')
for name,script in [('state','test-fase10-state.ps1'),('recovery','test-fase11-recovery.ps1')]:
 request={'evidence':str(E),'name':name,'argv':['powershell.exe','-NoProfile','-NonInteractive','-File',str(R/'tests'/script),'-SandboxDir',str(P),'-EvidenceDir',str(E/name),'-LogFile',str(E/(name+'.log.txt'))],'timeout':180,'controller_pid':os.getpid(),'controller_birth_ticks':birth}
 payload=base64.b64encode(json.dumps(request).encode()).decode()
 result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-File',str(R/'tests/run-owned-audit-gate.ps1'),'-PayloadBase64',payload],cwd=R,capture_output=True,timeout=240,creationflags=0x08000000)
 (E/(name+'.wrapper.stdout.txt')).write_bytes(result.stdout);(E/(name+'.wrapper.stderr.txt')).write_bytes(result.stderr)
 receipt=READ(E/(name+'.process.json'));assert result.returncode==0 and receipt['status']=='PASS',(name,receipt,(E/(name+'.stderr.txt')).read_text(encoding='utf-8',errors='replace')[-1500:]);print(name+' PASS',flush=True)
a=P/'.autopilot';d=E/'fixture-before-cleanup';d.mkdir()
for n in ['STATE.json','STATE.md','EVENTS.jsonl','LOCK.json']:
 if (a/n).exists():(d/n).write_bytes((a/n).read_bytes())
cleanup=ps('. '+q(R/'runner/core.ps1')+';. '+q(R/'runner/cleanup.ps1')+';$auto='+q(a)+';$s=Get-Content -LiteralPath (Join-Path $auto "STATE.json") -Raw -Encoding UTF8|ConvertFrom-Json;$l=Get-Content -LiteralPath (Join-Path $auto "LOCK.json") -Raw -Encoding UTF8|ConvertFrom-Json;if(@(Get-RunnerSurvivors $auto).Count -or (Get-Process -Id $l.owner_pid -ErrorAction SilentlyContinue)){throw "FIXTURE_OWNER_OR_PROCESS_STILL_ALIVE"};if($s.status -notin @("COMPLETED","FAILED","ABORTED","STALLED","BLOCKED_REQUIRES_HUMAN")){$s.status="ABORTED";$s.current_task="Terminal F10/F11 dependency unit fixture";$null=Write-AtomicState -StateObj $s -AutopilotDir $auto};Remove-RunnerOwnedLock $auto $s.run_id $l.owner_pid;@{status="PASS";lock_removed=(-not(Test-Path -LiteralPath (Join-Path $auto "LOCK.json")));terminal=$s.status}')
assert cleanup['status']=='PASS' and cleanup['lock_removed'];assert all(sha(R/n)==h for n,h in sources.items())
write(E/'CERTIFIED.json',{'status':'PASS','suite_sources_unchanged':sources,'same_fresh_fixture':str(P),'F10':'PASS','F11':'PASS','cleanup':cleanup,'local_inferences':0,'physical_sends':0,'historical_evidence_modified':False,'scope':'Isolated fixture dependency; not F26'})
(E/'certification.snapshot.py').write_bytes(Path(__file__).read_bytes());(E/'.gitattributes').write_text('* -text whitespace=-blank-at-eol,-blank-at-eof,space-before-tab,cr-at-eol\n',encoding='utf-8');print(json.dumps({'status':'PASS','evidence':str(E)}))
