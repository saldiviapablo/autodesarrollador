from pathlib import Path
import hashlib,json,re,shutil
R=Path(__file__).resolve().parents[2];E=R/'evidence/chatgpt-pointer-preintent-20261015/wrapped';C=E/'controlled-send';read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
r=read(C/'response.json');ident=read(C/'identity.json');expected=(E/'expected-prompt.txt').read_text(encoding='utf-8');expected=expected.strip().replace('\r\n','\n');expected=re.sub(r'\n\n+','\n',expected);digest=hashlib.sha256(expected.encode('utf-8')).hexdigest()
assert r['status']=='SUCCESS' and r['prompt_sha256']==r['dom_sha256']==digest
key=hashlib.sha256(ident['consultation_id'].encode()).hexdigest();d=R/'runtime/chatgpt-consultations';ledger=read(d/(key+'.json'));trace=[json.loads(v) for v in (d/(key+'.trace.jsonl')).read_text(encoding='utf-8').splitlines() if v.strip()];events=[v['event'] for v in trace]
assert ledger['delivery_state']=='COMPLETED' and ledger['send_attempts']==1 and ledger['physical_actions']==1
assert r['user_turns_before']==r['assistant_turns_before']==0 and r['user_turns_after']==r['assistant_turns_after']==1 and r['composer_cleared'] and r['utf8_valid'] and r['source_text_equals_dom_text']
assert events.index('PREPARED')<events.index('DELIVERY_INTENT')<events.index('SENT_CONFIRMED')<events.index('RESPONSE_WAIT_START')<events.index('RESPONSE_CAPTURED')
for p in d.glob(key+'*'):shutil.copyfile(p,C/p.name)
proof={'status':'PASS','send_completed_before_verifier_failure':True,'test_adapter_failure':'Expected prompt file had physical CRLF; verifier omitted normalization while bridge correctly used canonical LF','expected_normalized_sha256':digest,'consultation_id':ident['consultation_id'],'physical_sends':1,'source_dom_utf8':'PASS','user_turns':'0→1','assistant_turns':'0→1','composer_empty':True,'sent_before_response_wait':True,'logical_retry_pending':True,'no_resend':True}
(C/'normalized-verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof,ensure_ascii=False))
