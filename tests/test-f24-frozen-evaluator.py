"""Exercise all 28 final evaluator inputs with labelled unit metadata, no E2E."""
import hashlib,json,pathlib,uuid
from f24_gates import evaluate,ROOT
E=ROOT/'evidence/f24-harness-preflight-20261014';web=json.loads((E/'web/GATE.json').read_text(encoding='utf-8'));p=pathlib.Path(web['project']);a=p/'.autopilot';u=E/'gate-unit';u.mkdir(exist_ok=True)
def put(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value),encoding='utf-8')
out=json.loads((E/'web/actual-wrapper-output.json').read_text(encoding='utf-8'))
put(a/'logs/worker.stdout.txt',{'data':{'WorkerOutput':out}})
cid='deterministic-gate-'+uuid.uuid4().hex
put(a/'RUN-PLAN.json',{'consultation':{'id':cid}})
put(a/'evidence/roles.json',{r:{'status':'SUCCESS'} for r in ('supervisor','worker','reviewer')})
put(a/'RESTARTS.json',{'worker':1});put(a/'evidence/completion-gate.json',{'changed_files':['invoice.py']})
put(a/'evidence/checks.json',{'tests':[{'status':'PASS'}],'builds':[{'status':'PASS'}]})
put(a/'reports/runner-result.json',{'status':'COMPLETED','technical_status':'SUCCESS','reason':''})
put(a/'checkpoints/synthetic/ checkpoint-manifest.json'.replace(' ',''),{'unit_fixture':True})
events=['RUN_STARTED','MODEL_HEALTH_READY','WORKER_DIAGNOSIS_CONFIRMED','RECOVERY_RECONCILED','RUN_RECOVERED_FROM_DISK','RUN_STARTED']
(a/'EVENTS.jsonl').write_text('\n'.join(json.dumps({'type':t,'unit_fixture':True}) for t in events),encoding='utf-8')
put(u/'resources-live.json',{'samples':[{}, {}, {}],'gpu':[{}]});put(u/'approval.json',{'hashes':{str(ROOT/'config/security.yaml'):hashlib.sha256((ROOT/'config/security.yaml').read_bytes()).hexdigest()}})
flags=['real_launcher_started','prepare','preflight','single_approval','runner_completed','immutable_tests_preserved','native_tests_pass_before_crash','watchdog_checkpoint','disk_recovery','clock_preserved_across_recovery','chatgpt_real','chatgpt_utf8','chatgpt_idempotency','independent_reviewer_accepted','reviewer_readonly','completion_gate','final_cleanup','native_cleanup','duration_normal_budget','attempt_2_preserved'];checks=dict.fromkeys(flags,True)
directory=ROOT/'runtime/chatgpt-consultations';name=hashlib.sha256(cid.encode()).hexdigest();ledger=directory/(name+'.json');trace=directory/(name+'.trace.jsonl')
try:
 put(ledger,{'send_attempts':1,'delivery_state':'COMPLETED','history':[{'to':'SENT_CONFIRMED'},{'to':'COMPLETED'}],'synthetic_unit_fixture':True})
 trace.write_text('\n'.join(json.dumps({'event':t}) for t in ('SENT_CONFIRMED','RESPONSE_WAIT_START','RESPONSE_CAPTURED')),encoding='utf-8')
 result=evaluate(p,u,checks,{'synthetic':True});assert result['status']=='PASS',result
 assert len(result['gates'])==28
 checks['completion_gate']=False;negative=evaluate(p,u,checks,{'synthetic':True});assert not negative['gates']['completion'] and negative['status']=='FAIL';checks['completion_gate']=True
 checks['chatgpt_idempotency']=False;negative=evaluate(p,u,checks,{'synthetic':True});assert not negative['gates']['response'] and negative['status']=='FAIL'
 put(E/'frozen-evaluator.json',{'status':'PASS','total_gates':28,'complete_metadata_shape':'PASS','failed_native_completion_denied':True,'resend_proof_missing_denied':True,'unit_metadata_only':True,'not_live_E2E_evidence':True,'inferences':0,'messages':0});print('FROZEN_EVALUATOR PASS 28 gates; metadata fixture only')
finally:
 for path in (ledger,trace):
  if path.exists():path.unlink()
