import concurrent.futures,json,pathlib,subprocess,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1]
state_path=ROOT/'sandbox/chatgpt-idempotency/.autopilot/STATE.json'
state=json.loads(state_path.read_text(encoding='utf-8-sig'));state['chatgpt']={'queries_used':0,'max_queries':2};state_path.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
def call(_):
    p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-File',str(ROOT/'tests/chatgpt-budget-worker.ps1'),'-StatePath',str(state_path),'-Id','race-'+uuid.uuid4().hex],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=40)
    assert p.returncode==0,p.stderr
    return json.loads(p.stdout.strip().lstrip('\ufeff'))['status']
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:statuses=list(pool.map(call,range(4)))
after=json.loads(state_path.read_text(encoding='utf-8-sig'))
assert statuses.count('SUCCESS')==2 and statuses.count('CHATGPT_BUDGET_EXCEEDED')==2,statuses
assert after['chatgpt']['queries_used']==2
result={'status':'PASS','processes':4,'granted':2,'blocked':2,'max_queries':2,'queries_used':2,'real_network_queries':0,'state_mutex_serialization':True}
(ROOT/'evidence/chatgpt-idempotency/budget-race.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
