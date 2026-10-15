"""Persist the user-required STOP and preserve its evidence; no runtime actions."""
import datetime,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1];E=ROOT/'evidence/f24-admission-repair-20261014'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
save=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
assert not(E/'FINAL.json').exists()
assert read(E/'controlled-send/RESULT.json')['status']=='FAIL'
assert read(E/'integrity-final.json')['status']==read(E/'cleanup-final.json')['status']=='PASS'
result={'FRESH_CHAT_LOGIC':'PASS_DETERMINISTIC / LIVE_FRESHNESS_FAIL','CONTROLLED_REAL_SEND':'FAIL / FRESH_CHAT_NOT_EMPTY_OR_NOT_READY_NO_CLEAR','HEARTBEAT_RECOVERY_FIX':'IMPLEMENTED / NOT_VERIFIED_AFTER_STOP','F24_HARNESS_PREFLIGHT':'NOT_RUN / FRESH_CHAT_STOP','ATTEMPT_6_RUN_ID':'NOT_CREATED',**{k:'NOT_RUN' for k in ['DURATION','WORKER','WEB_FETCH','WEB_CONTEXT_DELIVERED','TESTS','BUILD','RECOVERY_DETECTION','START_RECOVER','CONTINUATION']},'FRESH_CHAT_READY':'FAIL','CHATGPT_SEND_METHOD':'NOT_SELECTED','CHATGPT_PHYSICAL_ACTIONS':0,**{k:'NOT_RUN' for k in ['CHATGPT_SENT','CHATGPT_RESPONSE','REVIEWER','COMPLETION_GATE','RAM_MIN','PAGEFILE_MAX','VRAM_MAX']},'CLEANUP':'PASS','F24':'FAIL / historical ATTEMPT5 preserved; ATTEMPT6 NOT_RUN','READY_FOR_F25':'NO','NEW_CHAT_NAVIGATION_CLICKS':1,'test_consultation_id':read(E/'controlled-send/identity.json')['consultation_id'],'test_ledger_reserved':False,'historical_files_preserved':4146,'protected_hashes_match':6,'new_dependencies':[],'new_local_inferences':0,'attempt7_created':False,'push':False}
save(E/'FINAL.json',result)
save(E/'PREFLIGHT.json',{'status':'NOT_RUN','sealed':False,'reason':'Explicit STOP after actual New Chat retained historical draft','TOTAL_GATES_FROZEN':28,'gates_sha256':read(E/'integrity-final.json')['catalog_sha256'],'attempt6_started':False})
save(E/'deterministic-checks.json',{'status':'PASS','source':'observed command outputs before live fresh-chat STOP; not a full harness preflight','commands':['node tests/test-chatgpt-fresh-chat.js','node tests/test-chatgpt-send-actuator.js','node tests/test-chatgpt-delivery.js','node tests/test-chatgpt-single-physical-click.js','node tests/test-controlled-send-utf8.js'],'fresh_chat_cases':10,'actuator_checks':13,'delivery_checks':8,'single_click_checks':4,'UTF8_SOURCE':'PASS','UTF8_PROMPT_BYTES':'PASS','heartbeat_recovery_probe_executed':False,'full_preflight_executed':False})
report='''# F24 — STOP after real New Chat retained the historical draft

ATTEMPT 6 was not created or started. The explicit condition in the current request requires STOP if New Chat does not produce an empty composer. That happened. No ATTEMPT7, F25 or push.

## What changed and was verified

The bridge requests the actual UI New Chat action for `--new-conversation`; it no longer treats navigation to `/` as proof of freshness. A unique visible editable composer, strict domain, root/new conversation identity, 0/0 turns, no streaming and an empty composer are checked before reserving the consultation ledger. The existing scoped submit/Enter selection, intent-before-one-action and exact turn/hash send proof remain unchanged. It never clears a retained draft.

Deterministic fresh-chat, send actuator A–L, delivery and single-click tests passed before the live check. PowerShell 5 parsed the controlled-send source using its existing UTF-8 BOM and produced the exact expected UTF-8 prompt bytes. No encoding change was needed.

The first preparation failed before navigation because an offscreen `aria-label=Nuevo chat` control masked the visible text-labelled navigation control. Read-only geometry/hit-testing demonstrated this defect. Before START, the selector was fixed to filter by hit-test before choosing a semantic candidate; its regression case passed. This failed preparation and the original identity were preserved. The same test ID was used for the repaired preparation, with no ledger yet reserved and normal budget accounting retained (no credits/reset).

## Live STOP

Test ID: `test-send-actuator-153deadd913e4bdfbbc081196d7f1c63`.

One mouse press/release pair was dispatched to the unique visible hit-tested New Chat navigation control. Post-action inspection still found the historical prompt, 0 user turns, 0 assistant turns, no streaming and URL `https://chatgpt.com/`. Its composer SHA remained `449d9d63fff353617d1d5f0f54ce75cf61186f1e8f2251586a8455a119ce056e`.

The bridge returned `FRESH_CHAT_NOT_EMPTY_OR_NOT_READY_NO_CLEAR`. The trace proves one New Chat navigation action, zero send-action events, zero DELIVERY_INTENT, zero SENT_CONFIRMED and no reserved test ledger. No test prompt was inserted, no draft was cleared or overwritten, no send method was selected and no response was requested. No further UI action or retry occurred after this refusal. Transport acknowledgement of navigation does not prove that ChatGPT created a new conversation.

ATTEMPT5's ledger is unchanged, including send_attempts=0 and UNKNOWN_DELIVERY/no_resend. Its SHA remains `a19538782cfaf89052c6fd4123fc80a1143777d3998c66c13781dbe9baf30521`. No reconciliation occurred.

## Heartbeat fixture correction: implemented, not certified

The proposed probe correction preserves the normal plan bytes before the artificial one-second injection and leaves the fault fixture terminal. A separate recovery fixture must have exactly those normal bytes/hash and retain its normal approval digest across recovery. No production heartbeat policy, Watchdog logic, timeout or budget was changed. This probe was not executed after the explicit fresh-chat STOP, so HEARTBEAT_RECOVERY_FIX is NOT_VERIFIED and the full preflight is NOT_RUN/unsealed. No live recovery success is claimed. The 28-gate catalog remains unchanged; there is no gate29.

## Cleanup and preservation

4,146 historical files retain exact SHA-256, including earlier admission failures and old sandbox/ledger evidence. All six protected component hashes were recomputed with streaming reads and match, including the actual GGUF model, llama-server, hook, MCP and both plugin copies. The 28-gate catalog SHA remains `690949c59fbf278f1863a35f4b27b07f3ab3b99960420c939a628625fc526953`.

Final cleanup verifies no own process survivors, no new metadata locks, Run Mutex FREE, Inference Mutex FREE and no listeners on 8080/9119. The dedicated preexisting Chrome remains open. The controlled test's STATE is ABORTED; its logical query reservations were preserved. No local inference, installations or updates were performed; qwen36/127.0.0.1:8080/ctx65536/parallel1 remain unchanged. All F24 E2E stages and metrics for ATTEMPT6 are NOT_RUN; prior measurements remain untouched.

## Requested results

```text
'''+ '\n'.join(k+' = '+str(v) for k,v in list(result.items())[:27])+'''
```

Evidence: `evidence/f24-admission-repair-20261014/`: FINAL.json, controlled-send/ (including failed preparation, native state and both traces), live-before.json, live-after-new-chat.json, new-chat-controls.json, controlled-source-utf8.json, deterministic-checks.json, cleanup-final.json, integrity-final.json and history-before.json. Backups: `backups/f24-admission-repair-20261014/manifest.json`. Infrastructure commit: 7281c4e. A separate local closure commit records this report and evidence. No push.
'''
(ROOT/'docs/F24-FRESH-CHAT-STOP-REPORT.md').write_text(report,encoding='utf-8',newline='\n')
note='\n## Estado vigente — Nuevo chat conserva borrador; STOP — 2026-10-14\n\nFix de aislamiento UI implementado y deterministas PASS. Un click de navegación Nuevo chat no produjo composer vacío: FRESH_CHAT_READY FAIL, hash histórico intacto. 0 envíos, 0 DELIVERY_INTENT, ledger de prueba no reservado; ATTEMPT5 sin cambios/reconciliación. STOP explícito; heartbeat fixture corregido pero NOT_VERIFIED, preflight completo NOT_RUN, ATTEMPT6 NOT_CREATED/NOT_RUN. Cleanup e integridad PASS (4146 archivos y 6 componentes protegidos). F24 conserva FAIL; READY_FOR_F25 NO; no ATTEMPT7/F25/F27/F28/push. docs/F24-FRESH-CHAT-STOP-REPORT.md; evidence/f24-admission-repair-20261014/.\n'
for name in ['00-README.md','07-ROADMAP.md','MANIFEST.md','docs/IMPLEMENTATION-STATUS.md']:
 p=ROOT/name;s=p.read_text(encoding='utf-8-sig')
 s=s.replace('F24 FAIL, ATTEMPT6 NOT_RUN / admisión fallida','F24 FAIL, ATTEMPT6 NOT_RUN / Nuevo chat conserva borrador')
 s=s.replace('F24 FAIL; ATTEMPT6 NOT_RUN / admisión fallida','F24 FAIL; ATTEMPT6 NOT_RUN / Nuevo chat conserva borrador')
 s=s.replace('validación de Macrofase 8 detenida: F24 FAIL, admisión ATTEMPT6 fallida antes de START','validación de Macrofase 8 detenida: F24 FAIL, Nuevo chat conserva borrador; ATTEMPT6 sin iniciar')
 if name=='docs/IMPLEMENTATION-STATUS.md':s=s.replace('Admisión ATTEMPT6 FAIL antes de START (prueba ChatGPT y probe cleanup); sin nuevo run. evidence/f24-attempt6-preflight-20261014/. |','Admisión ATTEMPT6 detenida: Nuevo chat conserva borrador; 0 envíos y sin nuevo run. Heartbeat fix NOT_VERIFIED; preflight NOT_RUN. evidence/f24-admission-repair-20261014/. |')
 p.write_text(s.rstrip()+'\n'+note,encoding='utf-8',newline='\n')
p=ROOT/'config/INSTALLATION-STATE.json';s=read(p);v=s['validation_8'];assert v['f24_attempt']==5
v['f24_attempt6_admission_history']=[v['f24_attempt6_admission']]
v['f24_attempt6_admission']={'status':'STOP_FRESH_CHAT_NOT_EMPTY','run_id':None,'fresh_chat_logic':'PASS_DETERMINISTIC_LIVE_FRESHNESS_FAIL','fresh_chat_ready':'FAIL','controlled_real_send':'FAIL_BEFORE_PREPARATION','test_consultation_id':result['test_consultation_id'],'physical_send_actions':0,'new_chat_navigation_clicks':1,'ledger_reserved':False,'historical_draft_unchanged':True,'heartbeat_recovery_fix':'IMPLEMENTED_NOT_VERIFIED','harness_preflight':'NOT_RUN','attempt6_started':False,'attempt7_created':False,'cleanup':'PASS','integrity':'PASS','report':'docs/F24-FRESH-CHAT-STOP-REPORT.md','evidence':'evidence/f24-admission-repair-20261014/'}
s['updated_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();save(p,s)
print(json.dumps(result))
