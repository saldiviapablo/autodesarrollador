"""Fresh unit STATE only: atomic bridge budgets, mock transport and no resend."""
from pathlib import Path
import base64,concurrent.futures,hashlib,importlib.util,json,os,subprocess,sys,uuid
R=Path(__file__).resolve().parents[2]
if not (R/'AGENTS.md').exists():R=Path(__file__).resolve().parents[1]
E=Path(sys.argv[1]).resolve();assert E.is_relative_to((R/'evidence').resolve()) and not E.exists();E.mkdir()
spec=importlib.util.spec_from_file_location('budget_fixture',R/'tests/runner-fixtures.py');fixtures=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixtures)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
ledger=R/'runtime/chatgpt-consultations';before={p.name:sha(p) for p in ledger.iterdir() if p.is_file()}
def fixture(name,max_queries):
 p=fixtures.project(name);a=p/'.autopilot';state=a/'STATE.json';value=json.loads(state.read_text(encoding='utf-8-sig'));value['chatgpt']={'queries_used':0,'max_queries':max_queries};state.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return p,state
def call(state,name,maximum,mock=True):
 quote=lambda x:"'"+str(x).replace("'","''")+"'"
 code="$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules';[Console]::OutputEncoding=[Text.Encoding]::UTF8;$result=& "+quote(R/'scripts/consultar-chatgpt.ps1')+' -Question '+quote('Labelled unit budget fixture; no network')+' -StatePath '+quote(state)+' -ConsultationId '+quote(name)+' -MaxQueries '+str(maximum)
 if mock:code+=' -MockResponse '+quote('AUDIT_MOCK_NO_NETWORK')
 code+=';$result|ConvertTo-Json -Depth 30 -Compress'
 args=['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(code.encode('utf-16le')).decode()]
 r=subprocess.run(args,capture_output=True,timeout=55,creationflags=0x08000000)
 (E/(name+'.stdout.txt')).write_bytes(r.stdout);(E/(name+'.stderr.txt')).write_bytes(r.stderr)
 assert r.returncode==0,r.stderr.decode('utf-8',errors='replace')
 return json.loads(r.stdout.decode('utf-8-sig'))
P,state=fixture('audit-budget-race',2);ids=['audit-mock-budget-'+uuid.uuid4().hex for _ in range(4)]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(lambda name:call(state,name,2),ids))
statuses=[r['Status'] if 'Status' in r else r['status'] for r in results];after=json.loads(state.read_text(encoding='utf-8-sig'))
assert statuses.count('SUCCESS')==2 and statuses.count('CHATGPT_BUDGET_EXCEEDED')==2 and after['chatgpt']=={'queries_used':2,'max_queries':2},statuses
install=json.loads((R/'config/INSTALLATION-STATE.json').read_text(encoding='utf-8-sig'));completed=json.loads((R/install['validation_8']['f25_evidence']/'tasks/001/native/evidence/CHATGPT.json').read_text(encoding='utf-8-sig'))['consultation_id']
old_state=state.read_bytes();retry=call(state,completed,2,False)
assert retry['Status']=='ALREADY_SENT' and retry['ResultObj']['no_resend'] and state.read_bytes()==old_state
invalid=state.with_name('invalid-budget-state.json');bad=json.loads(state.read_text(encoding='utf-8-sig'));bad['bypass']=True;invalid.write_text(json.dumps(bad),encoding='utf-8')
denied=call(invalid,'audit-invalid-'+uuid.uuid4().hex,2);assert denied['Status']=='INVALID_STATE_DENY'
P2,state2=fixture('audit-budget-policy-cap',5);cap=call(state2,'audit-cap-'+uuid.uuid4().hex,999);current=json.loads(state2.read_text(encoding='utf-8-sig'));assert cap['Status']=='SUCCESS' and current['chatgpt']=={'queries_used':1,'max_queries':5}
assert before=={p.name:sha(p) for p in ledger.iterdir() if p.is_file()},'MOCK_OR_LOGICAL_RETRY_MUTATED_LEDGER'
report={'status':'PASS','unit_fixtures_only':True,'race_processes':4,'granted':2,'blocked':2,'policy_cap':5,'invalid_schema':'DENY','completed_retry_at_exhausted_budget':'ALREADY_SENT','state_unchanged_by_logical_retry':True,'ledger_files_unchanged':True,'physical_sends':0,'new_ledger_reservations':0,'projects':[str(P),str(P2)],'cleanup':'Normal audit fixture terminal transition and owned LOCK release after suites'}
(E/'RESULT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
