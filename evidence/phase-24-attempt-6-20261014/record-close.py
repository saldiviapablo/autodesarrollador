"""Record failed ATTEMPT6 without changing the run, policies, clocks or ledgers."""
import datetime,json,pathlib,re
R=pathlib.Path(__file__).resolve().parents[2];E=pathlib.Path(__file__).resolve().parent;C=R/'evidence/f24-transaction-cert-20261014'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
save=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
assert not(E/'FINAL.json').exists()
s=read(E/'SUMMARY.json');st=read(E/'stage-results.json');integrity=read(E/'integrity-final.json');assert s['status']=='FAIL' and integrity['status']=='PASS' and read(E/'cleanup-independent.json')['status']=='PASS'
visibility=read(E/'turn-visibility.json')['result']['value'];assert visibility['url']=='https://chatgpt.com/' and all(x['rendered'] is False for role in ['user','assistant'] for x in visibility[role])
result={'PARTIAL_WORK_RESUMED':'YES','ROOT_CAUSE_FIXED':'PRE_SEND PASS / FRESH_CHAT_DOM_COUNTER FAIL','PRE_SEND_STATE_MACHINE':'PASS','FALSE_UNKNOWN_DELIVERY_FIXED':'PASS','OWNED_DRAFT_ROLLBACK':'PASS','LEGACY_ATTEMPT5_DRAFT_RECOVERY':'PASS','HISTORICAL_LEDGER_UNCHANGED':'YES','FRESH_CHAT_FIX':'FAIL / hidden old turns counted after navigation','UNICODE_GUARD':'PASS','HEARTBEAT_RECOVERY_FIX':'PASS','DETERMINISTIC_TESTS':'PASS','CONTROLLED_REAL_SEND':'PASS','F24_HARNESS_PREFLIGHT':'PASS (pre-START certification; native E2E failed)','ATTEMPT_6_RUN_ID':s['run_id'],'DURATION':s['duration_seconds'],'WORKER':st['WORKER'],'WEB_FETCH':st['WEB_FETCH'],'WEB_CONTEXT_DELIVERED':st['WEB_CONTEXT_DELIVERED'],'TESTS':'PASS / 13 immutable tests in both segments','BUILD':st['BUILD'],'RECOVERY_DETECTION':st['RECOVERY_DETECTION'],'START_RECOVER':st['START_RECOVER'],'CONTINUATION':st['CONTINUATION'],'CHATGPT_SEND_METHOD':'NOT_SELECTED','CHATGPT_PHYSICAL_ACTIONS':0,'CHATGPT_SENT':'FAIL / FRESH_CHAT_NOT_EMPTY_OR_NOT_READY_NO_CLEAR','CHATGPT_RESPONSE':'NOT_RUN','REVIEWER':'NOT_RUN','COMPLETION_GATE':'NOT_EVALUATED','RAM_MIN_MiB':s['RAM_min_available_mib'],'PAGEFILE_MAX_GiB':s['pagefile_max_used_gib'],'VRAM_MAX_MiB':s['VRAM_max_mib'],'CLEANUP':'PASS','INTEGRITY':'PASS','F24':'FAIL / BLOCKED_REQUIRES_HUMAN','READY_FOR_F25':'NO'}
save(E/'FINAL.json',result)
catalog=read(E/'FROZEN-GATES.json')['gates'];outcomes={g['name']:'PASS' for g in catalog}
outcomes.update(runner='NOT_COMPLETED / BLOCKED',chatgpt_send='FAIL / FRESH_CHAT_GATE',sent_confirmed='NOT_RUN',response='NOT_RUN',reviewer='NOT_RUN',completion='NOT_EVALUATED',report='TERMINAL_FAILURE_REPORT_PRODUCED; COMPLETED_REPORT_NOT_REACHED')
save(E/'FROZEN-GATE-STATUS-PARTIAL.json',{'status':'FAIL','total_gates_frozen':28,'first_blocking_execution_gate':'chatgpt_send','gates':outcomes,'partial_status_only':True,'native_final_evaluator_not_reached':True,'source':'native artifacts, checks, events, controlled injection, cleanup and immutable integrity audit; not simulated PASS'})
text='''# F24 ATTEMPT 6 — terminal STOP report

Date: 2026-10-15 (America/Buenos_Aires). F24 = FAIL. READY_FOR_F25 = NO. No ATTEMPT7, F25, F27/F28 or push.

## Resumed work and pre-START certification

The interrupted working tree was preserved, audited and completed. Transactional schema2 PREPARED/pre-send interruption/abort handling, owned-draft receipt validation, guarded rollback, conservative post-intent no_resend and strict Unicode guard passed deterministic suites. Empty/invalid/ambiguous ownership and forged cleanup receipts deny retry/clearing. Existing human reconciliation tests and the automatic reconciliation function remain compatible. Legacy schema1 records were not migrated.

ATTEMPT5's actual draft was recovered under LEGACY_PRE_SEND_RECOVERY before this E2E, with strict ownership/profile/domain/baseline/trace checks and three stable empty observations. Its ledger SHA remains `a19538782cfaf89052c6fd4123fc80a1143777d3998c66c13781dbe9baf30521`, send_attempts=0, historical UNKNOWN_DELIVERY. Current readouts label it legacy; no stored state was rewritten or recertified.

The controlled consultation `test-send-actuator-149e5c863a284648b50ad3cea075bf7c` passed from empty root/0/0: PREPARED before intent, one scoped submit, user+1, SENT_CONFIRMED before response wait, assistant+1, composer empty, UTF-8 response captured, COMPLETED and ALREADY_SENT retry with zero additional actions. Its budget remained 1/5. It did not certify the DOM extraction of retained hidden turns after leaving an existing conversation; that live defect was exposed by ATTEMPT6.

The isolated heartbeat fixture passed: one-second threshold only in the terminal fault fixture, normal recovery bytes/SHA equal the pre-fault snapshot (`81e792a5ea55716e5ade1f0201e7d02288b60da0d732bd7c8a57e959f8f8708a`), unchanged approval digest, actual START-Recover and technical SUCCESS. Production Watchdog and threshold were unchanged. Full harness preflight, runtime imports, native Qwen input binding, cleanup, UTF-8 and evaluator of the unchanged 28-gate catalog passed and were sealed. This was pre-START certification, not native E2E completion. Git was clean before creating ATTEMPT6.

## Actual new E2E

Run: `run-20261015-005747`; sandbox `sandbox/f24-attempt6-2bfe3e3f/project`. New contract/plan, one approval and new persistent clock; normal limits remained global2700/phase300/restart2/maxcycles5. Qwen alone edited invoice.py and README.md. Launcher, Prepare, admission, llama health, independent Supervisor, actual diagnostic FAIL, official WEB_FETCH, actual session/input-bound WEB_CONTEXT_DELIVERED, Worker correction, 13 immutable tests and approved build passed.

At harness elapsed492.00s, the sole owned Runner parent was deliberately crashed after checkpoint/tests/build. Watchdog confirmed PARENT_PROCESS_LOST at495.10s, and actual START-Recover began at495.12s. A second Supervisor and Worker succeeded, research was delivered again, and all tests/build passed again. The original clock bytes and all approval pins remained unchanged. No local inference overlap or manual target-code correction was introduced. Agent restart counters all remained zero; the single deliberate parent crash was not counted as agent restart credit.

## Failing gate and evidence

F24 consultation ID: `f24-a6-bb8c3e08d0684b80912466bce9011b1f`. Trace:

* 04:09:23.117Z BRIDGE_START.
* 04:09:24.171Z REQUEST_FRESH_CHAT, composer already empty.
* 04:09:24.187Z NEW_CHAT_NAVIGATION_START.
* 04:09:24.867Z NEW_CHAT_NAVIGATION_END.
* 04:09:28.053Z FAILURE FRESH_CHAT_NOT_EMPTY_OR_NOT_READY_NO_CLEAR.

The UI reached `https://chatgpt.com/` with an empty composer, no streaming, but `readConversation()` counted1 user and1 assistant node. Read-only inspection after cleanup proves both old nodes had zero width/height and no client rectangles (`rendered=false`). The extractor counts document-wide role nodes without distinguishing retained nonrendered messages from the current conversation. Those false1/1 counts rejected the required fresh0/0 baseline.

This is a remaining DOM-counting defect, not an ambiguous send. No F24 ledger was reserved, no prompt inserted, no PREPARED or DELIVERY_INTENT, no send method selected and zero mouse-send/Enter actions. Only one New Chat navigation occurred. No logical retry, reconciliation or further physical action followed. The native generic BLOCKED_REQUIRES_HUMAN/no_resend classification was preserved. No bridge/source fix was attempted after START, as required. Reviewer and Completion Gate were not reached; all28 native gates therefore did not pass.

## Metrics, cleanup and integrity

Native finalized duration699.24654s (11m39.25s); total harness708.91890s including setup6.59891s and final observation/cleanup. No phase/global budget extension. RAM minimum6.2265625MiB, pagefile maximum2.30023575GiB, VRAM maximum4507MiB, llama maximum working set20950.582MiB,138 resource samples. The maximum streak below150MiB was one sample; the existing sustained-critical guard did not trigger. The low RAM sample remains in the original metrics and was not replaced.

Native and independent cleanup PASS: zero owned survivors, metadata lock removed, Run/Inference mutex FREE,8080/9119 without listeners. Preexisting Chrome HERMES-CHATGPT remains open. STATE is terminal BLOCKED_REQUIRES_HUMAN and evidence is preserved.

All46 approval hashes,4185 historical files, immutable acceptance/build files, the original clock and six protected hashes (including freshly streamed actual GGUF, llama-server, hook, MCP and both plugins) match. No frozen source changed after START. qwen36/127.0.0.1:8080/ctx65536/parallel1 and Hermes0.21.6 remain unchanged; no dependencies, updates or push. Historical failures and all prior measurements remain intact.

## Requested results

```text
'''+ '\n'.join(k+' = '+str(v) for k,v in result.items())+'''
```

The working tree is committed clean at closure (verify with local Git). Commits for implementation/certification: `ca74d12`, `5b4834d`; heartbeat fixture source was already implemented in `7281c4e`. A separate terminal-evidence commit follows. The native final evaluator was not run after the block; `FROZEN-GATE-STATUS-PARTIAL.json` explicitly records incomplete/failed gates instead of claiming28/28 PASS.

Evidence: `evidence/f24-transaction-cert-20261014/` for certification and `evidence/phase-24-attempt-6-20261014/` for the actual run, byte-identical native exports, Worker diff, resource samples, checkpoint/crash/recovery, failed bridge traces, read-only DOM visibility, cleanup and integrity. `capture-manifest.json` maps exported files to original hashes.
'''
(R/'docs/F24-ATTEMPT-6-STOP-REPORT.md').write_text(text,encoding='utf-8',newline='\n')
note='\n## Estado vigente — F24 ATTEMPT 6 — 2026-10-15\n\nWorking tree parcial retomado. Transaction/legacy recovery/UTF-8/heartbeat/controlled send/preflight PASS (ca74d12,5b4834d); Git limpio antes de START. Nuevo run-20261015-005747: Worker SUCCESS, web fetch/context delivered,13 tests/build, checkpoint/crash/Watchdog/START-Recover/continuación PASS. Fresh-chat FAIL: en root vacío el contador incluyó turnos antiguos no renderizados (1/1); 0 envíos y ledger F24 no reservado. Sin fix/retry/reconciliación tras START. Reviewer/Completion Gate NOT_RUN. F24 FAIL / BLOCKED_REQUIRES_HUMAN; 699.25s, límites2700/300/restart2/cycles5 intactos. Cleanup/integridad PASS;46 pins y4185 archivos históricos intactos. READY_FOR_F25 NO; no ATTEMPT7/F25/F27/F28/push. docs/F24-ATTEMPT-6-STOP-REPORT.md; evidence/phase-24-attempt-6-20261014/.\n'
for name in ['00-README.md','07-ROADMAP.md','MANIFEST.md','docs/IMPLEMENTATION-STATUS.md']:
 p=R/name;t=p.read_text(encoding='utf-8-sig')
 t=t.replace('F24 FAIL, ATTEMPT6 NOT_RUN / Nuevo chat conserva borrador','F24 ATTEMPT6 FAIL / fresh-chat cuenta turnos ocultos')
 t=t.replace('F24 FAIL; ATTEMPT6 NOT_RUN / Nuevo chat conserva borrador','F24 ATTEMPT6 FAIL / fresh-chat cuenta turnos ocultos')
 t=t.replace('validación de Macrofase 8 detenida: F24 FAIL, Nuevo chat conserva borrador; ATTEMPT6 sin iniciar','validación de Macrofase 8 detenida en F24 ATTEMPT6: fresh-chat cuenta turnos ocultos')
 if name=='docs/IMPLEMENTATION-STATUS.md':
  t=re.sub(r'^\| \*\*Fase 24\*\*.*$', '| **Fase 24** | End-to-End corto | **FAIL / BLOCKED_REQUIRES_HUMAN** | ATTEMPT6 run-20261015-005747: Worker/web context/13 tests/build/recovery completo PASS; fresh-chat contó turnos ocultos, 0 envíos, ledger no reservado. Reviewer/gate NOT_RUN. evidence/phase-24-attempt-6-20261014/. |',t,flags=re.M)
  stamp=datetime.datetime.now(datetime.timezone.utc).astimezone(datetime.timezone(datetime.timedelta(hours=-3))).isoformat();t=re.sub(r'\*\*Última actualización:\*\* .*', '**Última actualización:** '+stamp,t,count=1)
 p.write_text(t.rstrip()+'\n'+note,encoding='utf-8',newline='\n')
p=R/'config/INSTALLATION-STATE.json';state=read(p);v=state['validation_8'];assert v['f24_attempt']==5
v['f24_attempt_5_history']={k:value for k,value in v.items() if k.startswith('f24_') and not k.endswith('_history')};v['f24_attempt_5_history']['classification']='HISTORICAL FAIL / BLOCKED_REQUIRES_HUMAN; original ledger untouched'
v.update(status='STOPPED_BLOCKED_REQUIRES_HUMAN',test='F24_ATTEMPT_6_NATIVE_E2E',reason='FRESH_CHAT_NOT_EMPTY_OR_NOT_READY_NO_CLEAR: hidden retained DOM turns counted as current baseline',f24_attempt=6,f24_run_id=s['run_id'],f24_report='docs/F24-ATTEMPT-6-STOP-REPORT.md',f24_evidence='evidence/phase-24-attempt-6-20261014/',f24_consultation_id=s['consultation_id'],f24_delivery='NOT_RESERVED / PRE_SEND_FRESH_CHAT_FAILURE',f24_send_attempts=0,f24_no_resend=True,f24_worker='SUCCESS',f24_worker_restarts_used=0,f24_tests_build='PASS (13 immutable tests/build, both segments)',f24_web_fetch='PASS',f24_web_context_delivered='PASS',f24_watchdog='PASS',f24_recovery_e2e='PASS',f24_reviewer='NOT_RUN',f24_completion_gate='NOT_EVALUATED',f24_duration_seconds=s['duration_seconds'],f24_cleanup='PASS',f24_integrity='PASS',f24_ready_for_f25=False,f24_pending_prompt_sha256=None,f24_attempt6_started=True,f24_attempt7_created=False,f24_transaction_certification='PASS',f24_legacy_draft_recovery='PASS / original ledger unchanged',f24_controlled_real_send='PASS',f24_harness_preflight='PASS / pre-START only',f24_preflight_evidence='evidence/f24-transaction-cert-20261014/',consultation_id=s['consultation_id'],delivery='NOT_RESERVED / PRE_SEND_FRESH_CHAT_FAILURE',no_resend=True,reconciled=False,source='F24_ATTEMPT_6_FRESH_CHAT_HIDDEN_DOM_TURNS')
v['f24_attempt6_admission_history'].append(v['f24_attempt6_admission']);v['f24_attempt6_admission']={'status':'PASS_BEFORE_START','certification':'evidence/f24-transaction-cert-20261014/CERTIFIED.json','attempt6_started':True,'run_id':s['run_id'],'controlled_real_send':'PASS','heartbeat_recovery_fix':'PASS','harness_preflight':'PASS','actual_e2e_result':'FAIL / FRESH_CHAT_GATE','retry_or_reconciliation_after_failure':False}
state['updated_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();save(p,state)
print(json.dumps(result,ensure_ascii=False))
