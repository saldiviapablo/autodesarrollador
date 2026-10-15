"""Read-only capture after the single controlled send failed; never launch F24."""
import hashlib,json,pathlib,shutil,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1];E=ROOT/'evidence/f24-attempt6-preflight-20261014';C=E/'controlled-send'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
identity=read(C/'identity.json');id=identity['consultation_id'];key=hashlib.sha256(id.encode()).hexdigest();ledger=ROOT/'runtime/chatgpt-consultations'/(key+'.json');record=read(ledger)
for p in ledger.parent.glob(key+'*'):
 if p.is_file():shutil.copyfile(p,C/p.name)
auto=pathlib.Path(identity['project'])/'.autopilot'
for p in auto.rglob('*'):
 if p.is_file():dest=C/'native'/p.relative_to(auto);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
assert record['send_attempts']==0 and not any(x['to']=='DELIVERY_INTENT' for x in record.get('history',[]))
events=[json.loads(line) for line in ledger.with_suffix('.trace.jsonl').read_text().splitlines() if line.strip()]
assert not any(x['event'].startswith(('MOUSE_PRESSED','MOUSE_RELEASED','ENTER_KEY')) or x['event']=='DELIVERY_INTENT' for x in events)
result={'status':'FAIL','reason':'PREEXISTING_COMPOSER_NO_SEND','consultation_id':id,'physical_actions':0,'delivery_intent':False,'message_sent':False,'response_captured':False,'logical_retry':'NOT_RUN','no_resend':True,'test_repeated':False,'attempt6_started':False,'attempt7_created':False,'historical_attempt5_reconciled':False,'ledger_state':record['delivery_state'],'cleanup':read(C/'cleanup.json')}
save(C/'RESULT.json',result)
history=read(E/'history-before.json')['files'];bad=[p for p,h in history.items() if not(ROOT/p).is_file() or sha(ROOT/p)!=h]
protected=read(ROOT/'evidence/phase-24-attempt-5-20261014/protected-final.json')['hashes'];badprotected=[p for p,h in protected.items() if sha(pathlib.Path(p))!=h]
save(E/'integrity-final.json',{'status':'PASS' if not(bad or badprotected) else 'FAIL','historical_files':len(history),'historical_mismatches':bad,'protected_components':len(protected),'protected_mismatches':badprotected,'frozen_28_gates_sha256':sha(ROOT/'docs/F24-GATES.json'),'attempt5_ledger_unchanged':sha(ROOT/'runtime/chatgpt-consultations/6188f287744816b7f6d430d03b62076163f6bff4b3f2d9b720aeb7876e3e4f78.json')=='a19538782cfaf89052c6fd4123fc80a1143777d3998c66c13781dbe9baf30521'})
(E/'.gitattributes').write_text('* -text whitespace=-blank-at-eol,-blank-at-eof,space-before-tab,cr-at-eol\n',encoding='utf-8')
print(json.dumps({'controlled_test':result,'integrity':read(E/'integrity-final.json')}))
