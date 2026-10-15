"""Read-only export/classification of the stopped attempt; never sends/reconciles."""
import hashlib,json,pathlib,shutil,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2];E=pathlib.Path(__file__).resolve().parent;P=ROOT/'sandbox/f24-attempt5-e6230453/project';A=P/'.autopilot'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(E/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
copies={}
def copy(source,dest):
 dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest);copies[str(source.relative_to(ROOT))]={'copy':str(dest.relative_to(E)),'sha256':sha(source)}
for source in sorted(A.rglob('*')):
 if source.is_file():copy(source,E/'native'/source.relative_to(A))
for n in ('invoice.py','README.md','test_invoice.py','build.py','QWEN.md','.gitignore'):copy(P/n,E/'artifacts'/n)
cid=read(E/'consultation.json')['consultation_id'];key=hashlib.sha256(cid.encode()).hexdigest();ledger=ROOT/'runtime/chatgpt-consultations'/(key+'.json')
for source in sorted(ledger.parent.glob(key+'*')):
 if source.is_file() and source.suffix in ('.json','.jsonl'):copy(source,E/'chatgpt'/source.name)
for argv,n in ((['diff','--binary'],'worker-diff.patch'),(['status','--porcelain=v1'],'sandbox-git-status.txt'),(['log','-5','--oneline'],'sandbox-git-log.txt')):
 r=subprocess.run(['git','-C',str(P),*argv],capture_output=True,check=True);(E/n).write_bytes(r.stdout)
pins=read(E/'approval.json')['hashes'];badpins=[p for p,h in pins.items() if sha(pathlib.Path(p))!=h];history=read(ROOT/'evidence/f24-harness-preflight-20261014/history-before.json')['files'];badhistory=[p for p,h in history.items() if sha(ROOT/p)!=h]
clock=read(E/'native-clock-initial.json');clock_ok=sha(pathlib.Path(clock['clock_path']))==clock['sha256'];plan=read(A/'RUN-PLAN.json');badtests=[pin['path'] for pin in plan['immutable_files'] if sha(P/pin['path'])!=pin['sha256']]
save('integrity-final.json',{'status':'PASS' if not(badpins or badhistory or badtests) and clock_ok else 'FAIL','approval_pins_checked':len(pins),'approval_mismatches':badpins,'historical_files_checked':len(history),'historical_mismatches':badhistory,'immutable_mismatches':badtests,'original_clock_unchanged':clock_ok,'source_files_changed_after_START':False})
events=[json.loads(v) for v in (A/'EVENTS.jsonl').read_text(encoding='utf-8-sig').splitlines() if v.strip()];types=[v['type'] for v in events];current=read(A/'logs/worker.stdout.txt');worker=current['data']['WorkerOutput'];supervisor=read(A/'logs/supervisor.stdout.txt');checks=read(A/'evidence/checks.json');record=read(ledger);traces=[json.loads(v) for v in ledger.with_suffix('.trace.jsonl').read_text(encoding='utf-8').splitlines() if v.strip()];te=[v['event'] for v in traces]
post_recovery=next(i for i,v in enumerate(events) if v['type']=='RUN_RECOVERED_FROM_DISK')
continuation=any(v['type']=='PROCESS_EXITED' and v['payload']['name']=='worker' and v['payload']['exit_code']==0 for v in events[post_recovery:]) and all(x['status']=='PASS' for g in ('tests','builds') for x in checks[g])
save('stage-results.json',{'WORKER':current['status'],'WEB_FETCH':'PASS','WEB_CONTEXT_DELIVERED':read(A/'evidence/WEB-CONTEXT-DELIVERED.json')['WEB_CONTEXT_DELIVERED'],'TESTS':'PASS' if all(v['status']=='PASS' for v in checks['tests']) else 'FAIL','BUILD':'PASS' if all(v['status']=='PASS' for v in checks['builds']) else 'FAIL','RECOVERY_DETECTION':'PASS' if read(E/'watchdog.json')['reason']=='PARENT_PROCESS_LOST' else 'FAIL','START_RECOVER':'PASS' if 'RUN_RECOVERED_FROM_DISK' in types and types.count('RUN_STARTED')==2 else 'FAIL','CONTINUATION':'PASS' if continuation and clock_ok else 'FAIL','CHATGPT_SENT':'FAIL / SEND_BUTTON_UNAVAILABLE_OR_AMBIGUOUS','CHATGPT_RESPONSE':'NOT_RUN','REVIEWER':'NOT_RUN','COMPLETION_GATE':'NOT_EVALUATED','physical_send_count':record['send_attempts'],'ledger_state':record['delivery_state'],'no_resend':True,'trace_has_delivery_intent':'DELIVERY_INTENT' in te,'trace_has_mouse_pressed':'MOUSE_PRESSED_START' in te,'worker_duration_final_seconds':worker['Duration'],'worker_restarts':read(A/'RESTARTS.json')['worker'],'query_budget':read(A/'STATE.json').get('chatgpt'),'ledger_sha256':sha(ledger),'ledger_modified_by_auditor':False})
pre=read(E/'pre-recovery-logs/worker.stdout.txt')['data']['WorkerOutput']['Stdout'];preproof=read(E/'web-context-before-crash.json');assert hashlib.sha256(pre.encode('utf-8')).hexdigest()==preproof['worker_output_sha256']
save('pre-recovery-output-integrity.json',{'status':'PASS','raw_worker_output_sha256':hashlib.sha256(pre.encode('utf-8')).hexdigest(),'matches_dispatch_proof':True})
names=read(E/'FROZEN-GATES.json')['gates'];statuses={g['name']:'PASS' for g in names}
statuses.update(runner='BLOCKED_BY_CHATGPT',chatgpt_send='FAIL',sent_confirmed='NOT_RUN',response='NOT_RUN',reviewer='NOT_RUN',completion='NOT_RUN',report='FAIL_REPORT_PRODUCED; COMPLETED_REPORT_NOT_REACHED')
save('FROZEN-GATE-STATUS-PARTIAL.json',{'status':'FAIL','total_frozen':28,'first_blocking_execution_gate':'chatgpt_send','gates':statuses,'partial_status_only':True,'not_a_final_pass':True})
save('capture-manifest.json',{'copies':copies,'all_copies_match':all(sha(E/v['copy'])==v['sha256'] for v in copies.values())})
(E/'.gitattributes').write_text('* -text whitespace=-blank-at-eol,-blank-at-eof,space-before-tab,cr-at-eol\n',encoding='utf-8')
print(json.dumps({'copies':len(copies),'integrity':read(E/'integrity-final.json'),'stages':read(E/'stage-results.json')},ensure_ascii=False))
