"""Capture the explicit fresh-chat STOP; do not send/reconcile or start a run."""
import hashlib,json,pathlib,shutil
ROOT=pathlib.Path(__file__).resolve().parents[1];E=ROOT/'evidence/f24-admission-repair-20261014';C=E/'controlled-send'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
save=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
 return h.hexdigest()
identity=read(C/'identity.json');id=identity['consultation_id'];key=hashlib.sha256(id.encode()).hexdigest();directory=ROOT/'runtime/chatgpt-consultations'
assert not(directory/(key+'.json')).exists(),'LEDGER_MUST_NOT_BE_RESERVED_BEFORE_FRESH'
for p in directory.glob(key+'*'):
 if p.is_file():shutil.copyfile(p,C/p.name)
traces=[json.loads(n) for n in (directory/(key+'.trace.jsonl')).read_text().splitlines() if n.strip()]
assert not any(r['event'] in ['DELIVERY_INTENT','MOUSE_PRESSED_START','ENTER_KEYDOWN_START','SENT_CONFIRMED'] for r in traces)
assert sum(r['event']=='NEW_CHAT_NAVIGATION_START' for r in traces)==1
observation=read(E/'live-after-new-chat.json')['observation'];assert observation['composer_sha256']=='449d9d63fff353617d1d5f0f54ce75cf61186f1e8f2251586a8455a119ce056e'
auto=pathlib.Path(identity['project'])/'.autopilot'
for p in auto.rglob('*'):
 if p.is_file():dest=C/'native'/p.relative_to(auto);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
history=read(E/'history-before.json')['files'];bad=[n for n,h in history.items() if not(ROOT/n).is_file() or sha(ROOT/n)!=h]
assert not bad,bad
protected=read(ROOT/'evidence/phase-24-attempt-5-20261014/protected-final.json')['hashes'];badprotected=[]
for n,h in protected.items():
 print(json.dumps({'integrity_check':pathlib.Path(n).name}),flush=True)
 if sha(pathlib.Path(n))!=h:badprotected.append(n)
save(E/'integrity-final.json',{'status':'PASS' if not badprotected else 'FAIL','historical_files':len(history),'historical_mismatches':bad,'protected_hashes':protected,'protected_mismatches':badprotected,'attempt5_ledger_unchanged':sha(directory/'6188f287744816b7f6d430d03b62076163f6bff4b3f2d9b720aeb7876e3e4f78.json')=='a19538782cfaf89052c6fd4123fc80a1143777d3998c66c13781dbe9baf30521','catalog_sha256':sha(ROOT/'docs/F24-GATES.json')})
assert not badprotected
save(C/'RESULT.json',{'status':'FAIL','reason':'FRESH_CHAT_NOT_EMPTY_OR_NOT_READY_NO_CLEAR','fresh_chat_ready':False,'test_consultation_id':id,'ledger_reserved':False,'new_chat_navigation_clicks':1,'send_actions':0,'delivery_intent':False,'response_captured':False,'historical_draft_sha256':observation['composer_sha256'],'historical_draft_unchanged':True,'historical_ledger_modified':False,'preparation_failure_before_navigation_preserved':True,'no_retry_after_new_chat_retained_draft':True,'cleanup':read(C/'cleanup.json')})
(E/'.gitattributes').write_text('* -text whitespace=-blank-at-eol,-blank-at-eof,space-before-tab,cr-at-eol\n',encoding='utf-8')
print(json.dumps({'status':'PASS','capture':'fresh chat STOP','historical_files':len(history)}),flush=True)
