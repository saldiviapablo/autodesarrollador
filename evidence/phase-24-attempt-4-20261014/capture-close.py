"""Read-only export of the stopped attempt. Never invokes Runner or bridge."""
import datetime, hashlib, json, pathlib, shutil, subprocess
ROOT = pathlib.Path(__file__).resolve().parents[2]
E = pathlib.Path(__file__).resolve().parent
P = ROOT / 'sandbox/f24-attempt4-2fbcc7d8/project'
A = P / '.autopilot'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name, value): (E/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
copies = {}
for source in sorted(A.rglob('*')):
    if source.is_file():
        dest=E/'native'/source.relative_to(A);dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,dest);copies[str(source.relative_to(ROOT))]={'copy':str(dest.relative_to(E)),'sha256':sha(source)}
for name in ('invoice.py','README.md','test_invoice.py','build.py','QWEN.md','.gitignore'):
    source=P/name;dest=E/'artifacts'/name;dest.parent.mkdir(exist_ok=True)
    shutil.copy2(source,dest);copies[str(source.relative_to(ROOT))]={'copy':str(dest.relative_to(E)),'sha256':sha(source)}
for argv,name in ((['diff','--binary'],'worker-diff.patch'),(['status','--porcelain=v1'],'sandbox-git-status.txt'),(['log','-5','--oneline'],'sandbox-git-log.txt')):
    r=subprocess.run(['git','-C',str(P),*argv],capture_output=True,check=True)
    (E/name).write_bytes(r.stdout)
approval=read(E/'approval.json');mismatch=[path for path,digest in approval['hashes'].items() if sha(pathlib.Path(path))!=digest]
pins=read(A/'RUN-PLAN.json')['immutable_files'];immutable=[x for x in pins if sha(P/x['path'])!=x['sha256']]
clock=read(E/'native-clock-initial.json');clock_ok=sha(pathlib.Path(clock['clock_path']))==clock['sha256']
old=read(ROOT/'evidence/f24-frontiers-20261014/historical-preservation-before.json')
historical=[path for path,digest in old['files'].items() if sha(ROOT/path)!=digest]
save('integrity-final.json',{'status':'PASS' if not(mismatch or immutable or historical) and clock_ok else 'FAIL','approval_pins_checked':len(approval['hashes']),'approval_mismatches':mismatch,'immutable_mismatches':immutable,'native_clock_unchanged':clock_ok,'historical_files_checked':len(old['files']),'historical_mismatches':historical,'old_ledgers_read_only':True})
cid=read(E/'consultation.json')['consultation_id']
ledger=ROOT/'runtime/chatgpt-consultations'/(hashlib.sha256(cid.encode()).hexdigest()+'.json')
save('consultation-not-run.json',{'consultation_id':cid,'ledger_exists':ledger.exists(),'physical_sends':0,'bridge_executed':False,'trace_exists':ledger.with_suffix('.trace.jsonl').exists(),'reason':'native WEB consumption gate failed before consultation stage'})
worker=read(A/'logs/worker.stdout.txt');output=worker['data']['WorkerOutput'];events=json.loads(output['Stdout']);envelope=read(A/'evidence/WEB-HANDOFF.json');packet=read(A/'packet-worker.json')
produced=json.dumps([e for e in events if e.get('type') in ('assistant','result')],ensure_ascii=False)
tool_results=[c for e in events if e.get('type')=='user' for c in e.get('message',{}).get('content',[]) if isinstance(c,dict) and c.get('type')=='tool_result']
save('worker-tool-results.json',tool_results)
original=read(A/'reports/runner-result.json.previous')
save('STOP-CLASSIFICATION.json',{'F24':'FAIL / MANDATORY_TEST_FAILED','native_root_cause':original['reason'],'harness_stop_reason':read(E/'SUMMARY.json')['failure'],'native_original_duration_seconds':original['duration_seconds'],'worker_status':worker['status'],'worker_final_duration_seconds':output['Duration'],'worker_restart_1':'TIMEOUT (305.45s reported by wrapper, configured timeout 300s)','worker_restarts_used':read(A/'RESTARTS.json')['worker'],'web_result_provided':True,'marker_in_actual_worker_packet':envelope['research_marker'] in json.dumps(packet),'source_hash_in_actual_worker_packet':envelope['source_sha256'] in json.dumps(packet),'marker_in_model_output':envelope['research_marker'] in produced,'source_hash_in_model_output':envelope['source_sha256'] in produced,'web_consumption_proven':False,'tests_build_worker_observations_only':'13 tests PASS and build PASS in captured tool results; native post-consumption checks not reached','controlled_crash':'NOT_RUN','START_Recover':'NOT_RUN','ChatGPT':'NOT_RUN / physical sends 0','Reviewer':'NOT_RUN','Completion_Gate':'NOT_EVALUATED','resume_attempt4':False,'F25_started':False})
save('capture-manifest.json',{'copies':copies,'all_copies_match':all(sha(E/v['copy'])==v['sha256'] for v in copies.values())})
(E/'.gitattributes').write_text('* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\nartifacts/QWEN.md -text whitespace=-blank-at-eol,-blank-at-eof,space-before-tab,cr-at-eol\ninitial-test.txt -text whitespace=-blank-at-eol,-blank-at-eof,space-before-tab,cr-at-eol\nnative/logs/check-unit.stderr.txt -text whitespace=-blank-at-eol,-blank-at-eof,space-before-tab,cr-at-eol\nworker-diff.patch -text whitespace=-blank-at-eol,-blank-at-eof,space-before-tab,cr-at-eol\n',encoding='utf-8')
print(json.dumps({'copies':len(copies),'integrity':read(E/'integrity-final.json'),'stop':read(E/'STOP-CLASSIFICATION.json')},ensure_ascii=False))
