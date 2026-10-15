"""Post-run read-only audit/export. Never changes a sandbox, clock or ledger."""
import hashlib,json,pathlib,shutil,subprocess
R=pathlib.Path(__file__).resolve().parents[2];E=pathlib.Path(__file__).resolve().parent;C=R/'evidence/f24-transaction-cert-20261014'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
save=lambda n,v:(E/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
fixture=read(E/'fixture.json');P=pathlib.Path(fixture['project']);A=P/'.autopilot';summary=read(E/'SUMMARY.json');copies={}
def copy(p,d):
 d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,d);copies[p.relative_to(R).as_posix()]={'copy':d.relative_to(E).as_posix(),'sha256':sha(p)}
for p in sorted(A.rglob('*')):
 if p.is_file():copy(p,E/'native'/p.relative_to(A))
for name in ['invoice.py','README.md','test_invoice.py','build.py','QWEN.md','.gitignore']:copy(P/name,E/'artifacts'/name)
cid=read(E/'consultation.json')['consultation_id'];key=hashlib.sha256(cid.encode()).hexdigest();ledgerPath=R/'runtime/chatgpt-consultations'/(key+'.json')
ledger=read(ledgerPath) if ledgerPath.exists() else {}
for p in ledgerPath.parent.glob(key+'*'):
 if p.is_file():copy(p,E/'chatgpt'/p.name)
for args,n in [(['diff','--binary'],'worker-diff.patch'),(['status','--porcelain=v1'],'sandbox-git-status.txt'),(['log','-5','--oneline'],'sandbox-git-log.txt')]:
 r=subprocess.run(['git','-C',str(P),*args],capture_output=True,check=True);(E/n).write_bytes(r.stdout)
pins=read(E/'approval.json')['hashes'];badpins=[p for p,h in pins.items() if sha(pathlib.Path(p))!=h]
history=read(C/'history-before.json')['files'];badhistory=[p for p,h in history.items() if sha(R/p)!=h]
clock=read(E/'native-clock-initial.json');clockOK=sha(pathlib.Path(clock['clock_path']))==clock['sha256']
plan=read(A/'RUN-PLAN.json');badtests=[p['path'] for p in plan['immutable_files'] if sha(P/p['path'])!=p['sha256']]
protected=read(R/'evidence/phase-24-attempt-5-20261014/protected-final.json')['hashes'];badprotected=[]
for p,h in protected.items():
 print(json.dumps({'protected_hash_check':pathlib.Path(p).name}),flush=True)
 if sha(pathlib.Path(p))!=h:badprotected.append(p)
save('integrity-final.json',{'status':'PASS' if not(badpins or badhistory or badtests or badprotected) and clockOK else 'FAIL','approval_pins_checked':len(pins),'approval_mismatches':badpins,'historical_files_checked':len(history),'historical_mismatches':badhistory,'immutable_mismatches':badtests,'protected_hashes':protected,'protected_mismatches':badprotected,'original_clock_unchanged':clockOK,'configuration':'qwen36/127.0.0.1:8080/ctx65536/parallel1','no_pinned_source_modified_after_START':not badpins})
checks=read(A/'evidence/checks.json') if (A/'evidence/checks.json').exists() else {};roles=read(A/'evidence/roles.json') if (A/'evidence/roles.json').exists() else {};report=read(A/'reports/runner-result.json');chat=read(A/'evidence/CHATGPT.json') if (A/'evidence/CHATGPT.json').exists() else {};retry=read(A/'evidence/CHATGPT-RETRY.json') if (A/'evidence/CHATGPT-RETRY.json').exists() else {};gate=read(A/'evidence/completion-gate.json') if(A/'evidence/completion-gate.json').exists() else {}
events=[json.loads(l) for l in (A/'EVENTS.jsonl').read_text(encoding='utf-8-sig').splitlines() if l.strip()];types=[e['type'] for e in events];c=summary['checks']
recoveryIndex=next((i for i,e in enumerate(events) if e['type']=='RUN_RECOVERED_FROM_DISK'),len(events));post=events[recoveryIndex:]
continued=any(e['type']=='PROCESS_EXITED' and e['payload'].get('name')=='worker' and e['payload'].get('exit_code')==0 for e in post) and all(x['status']=='PASS' for group in ['tests','builds'] for x in checks.get(group,[])) and clockOK
workerLog=read(A/'logs/worker.stdout.txt') if (A/'logs/worker.stdout.txt').exists() else {}
stages={'WORKER':roles.get('worker',{}).get('status','NOT_RUN'),'WEB_FETCH':'PASS' if 'WEB_FETCHED' in types else 'NOT_RUN','WEB_CONTEXT_DELIVERED':'PASS' if (A/'evidence/WEB-CONTEXT-DELIVERED.json').exists() and read(A/'evidence/WEB-CONTEXT-DELIVERED.json').get('WEB_CONTEXT_DELIVERED') else 'NOT_PROVEN','TESTS':'PASS' if checks.get('tests') and all(x['status']=='PASS' for x in checks['tests']) else 'FAIL_OR_NOT_RUN','BUILD':'PASS' if checks.get('builds') and all(x['status']=='PASS' for x in checks['builds']) else 'FAIL_OR_NOT_RUN','RECOVERY_DETECTION':'PASS' if c.get('watchdog_checkpoint') else 'NOT_RUN','START_RECOVER':'PASS' if c.get('disk_recovery') else 'NOT_RUN','CONTINUATION':'PASS' if c.get('disk_recovery') and c.get('clock_preserved_across_recovery') and 'RECOVERY_RECONCILED' in types and c.get('chatgpt_real') else 'NOT_PROVEN','CHATGPT_SEND_METHOD':chat.get('send_method','NOT_RUN'),'CHATGPT_PHYSICAL_ACTIONS':ledger.get('send_attempts',0),'CHATGPT_SENT':'PASS' if chat.get('message_sent') else ledger.get('delivery_state','NOT_RUN'),'CHATGPT_RESPONSE':'PASS' if chat.get('response_received') else 'NOT_RUN','REVIEWER':'ACCEPTED' if c.get('independent_reviewer_accepted') else 'NOT_ACCEPTED_OR_NOT_RUN','COMPLETION_GATE':gate.get('status','NOT_RUN'),'ledger_state':ledger.get('delivery_state','NOT_SEEN'),'logical_retry':retry.get('status','NOT_RUN'),'additional_sends':retry.get('additional_physical_sends'),'report_status':report.get('status')}
save('stage-results.json',stages)
stages['WORKER']=workerLog.get('status',stages['WORKER'])
stages['START_RECOVER']='PASS' if 'RUN_RECOVERED_FROM_DISK' in types and types.count('RUN_STARTED')==2 else 'NOT_RUN'
stages['CONTINUATION']='PASS' if continued else 'NOT_PROVEN'
stages['CHATGPT_SENT']='FAIL / '+chat.get('error','NOT_RUN') if chat.get('status')=='ERROR' else stages['CHATGPT_SENT']
save('stage-results.json',stages)
save('capture-manifest.json',{'copies':copies,'all_copies_match':all(sha(E/v['copy'])==v['sha256'] for v in copies.values())})
(E/'.gitattributes').write_text('* -text whitespace=-blank-at-eol,-blank-at-eof,space-before-tab,cr-at-eol\n',encoding='utf-8')
print(json.dumps({'summary':summary,'stages':stages,'integrity':read(E/'integrity-final.json'),'copies':len(copies)},ensure_ascii=False),flush=True)
