"""Document failed admission; never create a live attempt or change a ledger."""
import datetime,hashlib,json,pathlib,shutil
ROOT=pathlib.Path(__file__).resolve().parents[1];E=ROOT/'evidence/f24-attempt6-preflight-20261014'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
save=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
assert not (E/'FINAL.json').exists(),'CLOSURE_ALREADY_RECORDED'
assert read(E/'controlled-send/RESULT.json')['status']=='FAIL'
assert read(E/'integrity-final.json')['status']=='PASS'
assert read(E/'cleanup-final.json')['status']=='PASS'
passed=['web','frozen-evaluator','budget-cache','send-actuator','delivery','domain','idempotency','human','single-click','child-cleanup','launcher','reviewer-transport','completion','recovery']
tests={n:{'status':'PASS','evidence':n+'.stdout.txt'} for n in passed}
tests.update({'cleanup':{'status':'FAIL','reason':'HEARTBEAT_STALE again in recovered stale-heartbeat probe','evidence':'cleanup.stderr.txt'},'syntax-lock':{'status':'NOT_RUN'},'native-qwen-input':{'status':'NOT_RUN'},'runtime-dependencies':{'status':'PASS','evidence':'runtime-dependencies.json'}})
save(E/'PREFLIGHT.json',{'status':'FAIL','sealed':False,'F24_HARNESS_PREFLIGHT':'FAIL','tests':tests,'TOTAL_GATES_FROZEN':28,'gates_sha256':hashlib.sha256((ROOT/'docs/F24-GATES.json').read_bytes()).hexdigest(),'historical_files_preserved':955,'actual_messages_sent':0,'local_inferences':0,'attempt6_started':False})
failed_probe=ROOT/'sandbox/7b-cleanup22-heartbeat_stale-9f9796e0/.autopilot'
for p in failed_probe.rglob('*'):
 if p.is_file():dest=E/'cleanup/failing-probe-native'/p.relative_to(failed_probe);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
result={'SEND_ACTUATOR_FIX':'PASS_DETERMINISTIC / LIVE_NOT_VALIDATED','LIVE_UI_PRECHECK':'PASS','PRIMARY_SEND_METHOD':'COMPOSER_SCOPED_SUBMIT','ENTER_FALLBACK_TEST':'PASS_DETERMINISTIC','CONTROLLED_REAL_SEND':'FAIL / PREEXISTING_COMPOSER_NO_SEND','F24_HARNESS_PREFLIGHT':'FAIL / cleanup recovery HEARTBEAT_STALE','ATTEMPT_6_RUN_ID':'NOT_CREATED','DURATION':'NOT_RUN',**{k:'NOT_RUN' for k in ['WORKER','WEB_FETCH','WEB_CONTEXT_DELIVERED','TESTS','BUILD','RECOVERY_DETECTION','START_RECOVER','CONTINUATION','CHATGPT_SEND_METHOD','CHATGPT_SENT','CHATGPT_RESPONSE','REVIEWER','COMPLETION_GATE','RAM_MIN','PAGEFILE_MAX','VRAM_MAX']},'CHATGPT_PHYSICAL_ACTIONS':0,'CLEANUP':'PASS','F24':'FAIL (historical ATTEMPT5 retained; ATTEMPT6 NOT_RUN)','READY_FOR_F25':'NO','controlled_test_consultation_id':read(E/'controlled-send/identity.json')['consultation_id'],'primary_stop_cause':'New-conversation navigation to root retained the historical draft; fail-closed before actuator selection or intent. One controlled test, no retry.','separate_preflight_failure':'Recovered probe retains heartbeat_stale_seconds=1 and was interrupted again with HEARTBEAT_STALE; technical_status INTERRUPTED, not required SUCCESS. No timeout/budget/test relaxation or rerun.','historical_attempt5_ledger_unchanged':True,'historical_files_preserved':955,'protected_hashes_verified':6,'new_dependencies':[],'F25_started':False,'attempt7_created':False,'push':False}
save(E/'FINAL.json',result)
report='''# F24 ATTEMPT 6 — admission stopped

ATTEMPT 6 was not created or started. The single controlled ChatGPT test failed before delivery; F24 remains FAIL and READY_FOR_F25 is NO.

## Delivery stop

The new actuator passed A–L deterministic tests: composer-local scope, unrelated global buttons, physical Enter fallback selected before intent, hash/conversation/streaming/focus guards, immutable method, one action, no cross-method fallback and irreversible confirmed sends. Existing delivery, UTF-8/domain, idempotency and human-reconciliation tests passed; the automatic reconciliation function remains unchanged.

Read-only inspection of Chrome PID 16576 verified the dedicated persistent HERMES-CHATGPT profile. The historical prompt SHA was `449d9d63fff353617d1d5f0f54ce75cf61186f1e8f2251586a8455a119ce056e`. Exactly one local submit and a focused composer were present. No UI writes or sends occurred during this inspection.

Controlled test `test-send-actuator-735b2b7cc7ad4173b62227a5d45a3f46` used the normal sanitizer, budget wrapper, ledger and bridge. The bridge navigated to the root URL to request a new conversation, but that navigation retained ATTEMPT5's draft. `PREEXISTING_COMPOSER_NO_SEND` stopped execution before inserting test text, selecting an actuator or recording intent. Trace: BRIDGE_START 2026-10-15T01:19:31.204Z; FAILURE 01:19:35.957Z; CLEANUP 01:19:36.050Z. Zero DELIVERY_INTENT, mouse or Enter events; send_attempts=0. The controlled test ledger remains UNKNOWN_DELIVERY/no_resend. No retry or reconciliation was performed. No response or real actuator delivery was validated. After navigation the historical composer hash still matched; focus was lost, which would independently prohibit Enter until legitimately focused in a future authorized preparation.

The causal defect is that root navigation does not guarantee a fresh empty composer. The existing safety guard worked. No second test conversation or ATTEMPT6/7 was attempted after this failure.

## Separate harness preflight failure

Fourteen preflight groups plus actual-runtime dependency imports passed. The cleanup suite failed its disk-recovery probe: its deliberately stale `heartbeat_stale_seconds=1` remained in the recovered probe and another HEARTBEAT_STALE interrupted it; expected technical_status SUCCESS was not reached. Its immutable report/events and stderr are preserved. Syntax-lock and native-Qwen-input checks were not reached; the preflight is FAIL and unsealed. No retest, budget extension, timeout modification or relaxed assertion was used.

The newly added controlled-test PowerShell source initially lacked a UTF-8 BOM, so Windows PowerShell 5 decoded its Unicode literal incorrectly. This was not the delivery stop: no test prompt was inserted. Executed source and actual prompt bytes are preserved; a BOM was added for future correct decoding, without executing another test. Production UTF-8 source/DOM/hash checks remain mandatory.

## Preservation and cleanup

All 955 historical files, including previous ledgers, ATTEMPT5 sandbox/evidence and previous preflight, retain exact SHA-256. ATTEMPT5 ledger SHA remains `a19538782cfaf89052c6fd4123fc80a1143777d3998c66c13781dbe9baf30521`; send_attempts=0. No old state, clock, budget, ledger or sandbox was modified. F23 PASS and previous classifications remain historical. The 28-gate catalog SHA remains `690949c59fbf278f1863a35f4b27b07f3ab3b99960420c939a628625fc526953`.

Six protected hashes, including the actual model, llama-server, hook, MCP and both plugin copies, match. No installations or version updates occurred. qwen36/127.0.0.1:8080/ctx65536/parallel1 remain unchanged; no local inference was run for this admission.

Final cleanup independently verified the controlled test, completion unit fixture and eight cleanup fixtures: zero owned process survivors, no metadata locks, Run Mutex and Inference Mutex FREE, no 8080/9119 listeners. The controlled-test STATE is ABORTED, clearly labelled as a closed probe; it does not claim full Runner completion. Preexisting Chrome remains open. F24 ATTEMPT6 metrics, Worker, web, recovery, Reviewer, Completion Gate and report are NOT_RUN; prior F24 metrics were preserved. No F25/F27/F28 or push.

## Results

```text
'''+ '\n'.join(k+' = '+str(result[k]) for k in list(result)[:27])+'''
```

Evidence: `evidence/f24-attempt6-preflight-20261014/FINAL.json`, `PREFLIGHT.json`, `live-ui-precheck.json`, `live-ui-after-stop.json`, `controlled-send/`, `cleanup/`, `cleanup-final.json`, `integrity-final.json` and `history-before.json`. Infrastructure commit: 8c01b07; closure commit follows in local Git. No push.
'''
(ROOT/'docs/F24-ATTEMPT-6-ADMISSION-STOP-REPORT.md').write_text(report,encoding='utf-8',newline='\n')
note='\n## Estado vigente — admisión F24 ATTEMPT 6 detenida — 2026-10-14\n\nActuador ChatGPT A–L y UI read-only PASS; prueba real controlada FAIL antes de envío: navegar a raíz conservó el borrador histórico, PREEXISTING_COMPOSER_NO_SEND, 0 intentos físicos. No retry/reconciliación. Preflight del harness FAIL por HEARTBEAT_STALE repetido en probe de recovery/cleanup. ATTEMPT6 NOT_RUN, sin nuevo run/clock/aprobación; no ATTEMPT7. ATTEMPT5 y 955 archivos históricos intactos. Cleanup final e integridad PASS; F24 conserva FAIL; READY_FOR_F25 NO. Informe: docs/F24-ATTEMPT-6-ADMISSION-STOP-REPORT.md; evidence/f24-attempt6-preflight-20261014/.\n'
for name in ('00-README.md','07-ROADMAP.md','MANIFEST.md','docs/IMPLEMENTATION-STATUS.md'):
 p=ROOT/name;s=p.read_text(encoding='utf-8-sig')
 if name in ('00-README.md','MANIFEST.md'):s=s.replace('FAIL / BLOCKED_REQUIRES_HUMAN (F23 PASS; F24 ATTEMPT 5 ChatGPT precheck FAIL, 0 envíos)','FAIL / BLOCKED_REQUIRES_HUMAN (F23 PASS; F24 FAIL, ATTEMPT6 NOT_RUN / admisión fallida)')
 if name=='00-README.md':s=s.replace('validación de Macrofase 8 detenida en F24 ATTEMPT 5 por precheck del botón ChatGPT','validación de Macrofase 8 detenida: F24 FAIL, admisión ATTEMPT6 fallida antes de START')
 if name=='07-ROADMAP.md':s=s.replace('F23 PASS; F24 ATTEMPT 5 ChatGPT precheck FAIL |','F23 PASS; F24 FAIL; ATTEMPT6 NOT_RUN / admisión fallida |')
 if name=='docs/IMPLEMENTATION-STATUS.md':s=s.replace('Reviewer/gate NOT_RUN. evidence/phase-24-attempt-5-20261014/. |','Reviewer/gate NOT_RUN. Admisión ATTEMPT6 FAIL antes de START (prueba ChatGPT y probe cleanup); sin nuevo run. evidence/f24-attempt6-preflight-20261014/. |')
 p.write_text(s.rstrip()+'\n'+note,encoding='utf-8',newline='\n')
p=ROOT/'config/INSTALLATION-STATE.json';state=read(p);v=state['validation_8'];assert v['f24_attempt']==5
v['f24_attempt6_admission']={'status':'FAIL_BEFORE_START','run_id':None,'send_actuator':'PASS_DETERMINISTIC_LIVE_UNVALIDATED','live_ui_precheck':'PASS','controlled_real_send':'FAIL_PREEXISTING_COMPOSER_NO_SEND','test_consultation_id':result['controlled_test_consultation_id'],'physical_actions':0,'harness_preflight':'FAIL_HEARTBEAT_STALE_RECOVERY_PROBE','retry_or_reconciliation':False,'attempt6_started':False,'attempt7_created':False,'cleanup':'PASS','integrity':'PASS','report':'docs/F24-ATTEMPT-6-ADMISSION-STOP-REPORT.md','evidence':'evidence/f24-attempt6-preflight-20261014/'}
state['updated_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();save(p,state)
print(json.dumps(result))
