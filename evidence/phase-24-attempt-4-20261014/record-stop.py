"""Record current documentation after STOP; preserve previous attempt fields."""
import datetime, json, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
updates={
 '00-README.md':[
 ('validación de Macrofase 8 detenida en F24 ATTEMPT 3 por ChatGPT UNKNOWN_DELIVERY','validación de Macrofase 8 detenida en F24 ATTEMPT 4 por consumo web no demostrado'),
 ('FAIL / BLOCKED_REQUIRES_HUMAN (F23 PASS; F24 ATTEMPT 3 UNKNOWN_DELIVERY)','FAIL / MANDATORY_TEST_FAILED (F23 PASS; F24 ATTEMPT 4 WEB_CONSUMED NOT_PROVEN)')],
 '07-ROADMAP.md':[
 ('| **Macrofase 8** | Validación Final | F23 PASS; F24 ATTEMPT 3 UNKNOWN_DELIVERY | **FAIL / BLOCKED_REQUIRES_HUMAN** |','| **Macrofase 8** | Validación Final | F23 PASS; F24 ATTEMPT 4 consumo web no demostrado | **FAIL / MANDATORY_TEST_FAILED** |')],
 'MANIFEST.md':[
 ('FAIL / BLOCKED_REQUIRES_HUMAN (F23 PASS; F24 ATTEMPT 3 ChatGPT UNKNOWN_DELIVERY)','FAIL / MANDATORY_TEST_FAILED (F23 PASS; F24 ATTEMPT 4 consumo web no demostrado)')],
 'docs/IMPLEMENTATION-STATUS.md':[
 ('| **Fase 24** | End-to-End corto | **FAIL / BLOCKED_REQUIRES_HUMAN** | ATTEMPT 3: Worker SUCCESS, 13 tests/build y Watchdog PASS; ChatGPT UNKNOWN_DELIVERY, sin reenvío. Reviewer/gate final NOT_RUN. evidence/phase-24-attempt-3-20261014/. |','| **Fase 24** | End-to-End corto | **FAIL / MANDATORY_TEST_FAILED** | ATTEMPT 4: entrega web explícita PASS, consumo por Qwen NOT_PROVEN. Worker SUCCESS tras 1 reinicio; ChatGPT/Reviewer/gate NOT_RUN. evidence/phase-24-attempt-4-20261014/. |')]
}
note='\n## Estado vigente — F24 ATTEMPT 4 — 2026-10-14\n\nFronteras A/B/C y smokes previos PASS (aabf021, 7de9bf9, c846e2a). Nuevo run-20261014-201149: Prepare/preflight/aprobación/launcher/Supervisor/diagnóstico FAIL inicial/fetch/entrega explícita PASS. Worker TIMEOUT y un reinicio normal 1/2; Worker final SUCCESS con 13 tests/build PASS en sus herramientas, pero consumo web NOT_PROVEN (marcador/SHA ausentes). Runner STOP RESEARCH_CONSUMPTION_NOT_PROVEN; F24 FAIL / MANDATORY_TEST_FAILED. Crash/START-Recover E2E/ChatGPT/Reviewer/Completion Gate NOT_RUN. Consulta nueva no ejecutada, cero envíos. Duración 729.54s; límites 2700/fase300/restart2/maxcycles5 sin ampliar. Cleanup/integridad PASS, 419 archivos históricos intactos. ATTEMPT3 permanece HISTORICAL FAIL / BLOCKED_REQUIRES_HUMAN y su ledger no se tocó. F23 PASS; READY_FOR_F25 NO; F25/F27/F28 no iniciadas. docs/F24-ATTEMPT-4-STOP-REPORT.md; evidence/phase-24-attempt-4-20261014/.\n'
for name,pairs in updates.items():
 p=ROOT/name;text=p.read_text(encoding='utf-8-sig')
 for before,after in pairs:
  assert text.count(before)==1,(name,before,text.count(before));text=text.replace(before,after)
 p.write_text(text.rstrip()+'\n'+note,encoding='utf-8',newline='\n')
p=ROOT/'docs/F24-FRONTIER-HARDENING.md'
p.write_text(p.read_text(encoding='utf-8-sig').rstrip()+'\n\nResultado posterior: ATTEMPT4 FAIL / MANDATORY_TEST_FAILED en consumo web real; el modelo recibió el envelope pero no produjo marcador/SHA. Los PASS deterministas previos se conservan con su alcance. ChatGPT y START-Recover E2E ATTEMPT4 NOT_RUN. Informe: docs/F24-ATTEMPT-4-STOP-REPORT.md. STOP, F25 no iniciada.\n',encoding='utf-8',newline='\n')
p=ROOT/'config/INSTALLATION-STATE.json';s=json.loads(p.read_text(encoding='utf-8-sig'));v=s['validation_8']
assert v['f24_attempt']==3
v['f24_attempt_3_history']={k:value for k,value in v.items() if (k.startswith('f24_') and k!='f24_attempt_2_history') or k in ('consultation_id','delivery','no_resend','reconciled','source','attempt_3_report')}
v['f24_attempt_3_history']['classification']='HISTORICAL FAIL / BLOCKED_REQUIRES_HUMAN'
v.update(status='STOPPED_MANDATORY_TEST_FAILED',test='F24_ATTEMPT_4_NATIVE_E2E',reason='RESEARCH_CONSUMPTION_NOT_PROVEN; harness NATIVE_WORKER_CRASH_GATE_NOT_REACHED',f24_run_id='run-20261014-201149',f24_attempt=4,f24_report='docs/F24-ATTEMPT-4-STOP-REPORT.md',f24_evidence='evidence/phase-24-attempt-4-20261014/',f24_consultation_id='f24-a4-3120338e4c054c608d367c0b8bc68c77',f24_delivery='NOT_RUN',f24_no_resend=True,f24_send_attempts=0,f24_worker='SUCCESS',f24_worker_restarts_used=1,f24_tests_build='Worker tools PASS 13 tests/build; native final checks NOT_RUN / WEB_GATE_FAILED',f24_web_fetch='PASS',f24_web_handoff='PROVIDED / SHA and marker present in actual packet',f24_worker_web_read='FAIL / NOT_PROVEN',f24_watchdog='Worker restart PASS; controlled parent crash NOT_RUN',f24_recovery_e2e='NOT_RUN / WEB_GATE_FAILED',f24_reviewer='NOT_RUN / WEB_GATE_FAILED',f24_completion_gate='NOT_EVALUATED',f24_duration_seconds=729.5409989356995,f24_global_timeout_seconds=2700,f24_budgets_changed=False,f24_cleanup='PASS',f24_integrity='PASS',f24_ready_for_f25=False,f24_pending_prompt_sha256=None,consultation_id='f24-a4-3120338e4c054c608d367c0b8bc68c77',delivery='NOT_RUN',no_resend=True,reconciled=False,source='F24_ATTEMPT_4_STOP_BEFORE_CHATGPT')
s['updated_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
p.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Current README/ROADMAP/MANIFEST/IMPLEMENTATION/INSTALLATION reconciled to ATTEMPT4 FAIL; historical evidence unchanged.')
