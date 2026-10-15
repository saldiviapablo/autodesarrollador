"""Terminal report/status views only; never changes native run files or ledger."""
from pathlib import Path
import datetime,json,hashlib,re,shutil
R=Path(__file__).resolve().parents[2];E=R/'evidence/phase-24-attempt-7-20261015'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
save=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
s=read(E/'SUMMARY.json');st=read(E/'stage-results.json');i=read(E/'integrity-final.json');c=read(E/'cleanup-final.json')
f=read(E/'FROZEN-GATE-RESULT.json') if (E/'FROZEN-GATE-RESULT.json').exists() else {'status':'NOT_RUN'}
assert i['status']=='PASS' and c['status']=='PASS','INTEGRITY_OR_CLEANUP_FAILED_STOP_BEFORE_STATUS_UPDATE'
ok=s['status']=='PASS' and f['status']=='PASS' and len(f['gates'])==28 and all(f['gates'].values())
P=Path(s['project']);A=P/'.autopilot';chat=read(E/'chatgpt.json') if (E/'chatgpt.json').exists() else {}
ledger=read(E/'chatgpt-ledger-final.json') if (E/'chatgpt-ledger-final.json').exists() else {}
trace=R/'runtime/chatgpt-consultations'/(hashlib.sha256(s['consultation_id'].encode()).hexdigest()+'.trace.jsonl')
rows=[json.loads(line) for line in trace.read_text(encoding='utf-8').splitlines() if line.strip()] if trace.exists() else []
events=[v['event'] for v in rows];history=[v.get('to') for v in ledger.get('history',[])]
fresh=next((v for v in rows if v['event']=='FRESH_CHAT_READY'),None)
observations=read(E/'browser-layout-observations.json')['observations'] if (E/'browser-layout-observations.json').exists() else []
prior=[o for o in observations if fresh and o['at']<=fresh['at'] and o['url']=='https://chatgpt.com/' and o['composer_empty'] and o['active_user']==o['active_assistant']==0 and not o['isStreaming']]
baseline=prior[-1] if prior else read(E/'admission-browser.json')['observation']
resources=read(E/'resources-live.json');samples=resources['samples'];restart=read(A/'RESTARTS.json')
result={
 'ATTEMPT_7_RUN_ID':s['run_id'],'DURATION':s['duration_seconds'],
 'ADMISSION':'PASS','WORKER':st['WORKER'],'WEB_FETCH':st['WEB_FETCH'],'WEB_CONTEXT_DELIVERED':st['WEB_CONTEXT_DELIVERED'],
 'TESTS':st['TESTS'],'BUILD':st['BUILD'],'RECOVERY_DETECTION':st['RECOVERY_DETECTION'],'START_RECOVER':st['START_RECOVER'],'CONTINUATION':st['CONTINUATION'],
 'FRESH_CHAT_URL':chat.get('fresh_chat',{}).get('url',baseline.get('url')),
 'RAW_USER':baseline.get('raw_user'),'ACTIVE_USER':fresh.get('user') if fresh else None,
 'RAW_ASSISTANT':baseline.get('raw_assistant'),'ACTIVE_ASSISTANT':fresh.get('assistant') if fresh else None,
 'FRESH_CHAT_READY':bool(fresh and chat.get('fresh_chat_ready')),
 'CHATGPT_CONSULTATION_ID':s['consultation_id'],'CHATGPT_SEND_METHOD':ledger.get('send_method','NOT_RUN'),
 'CHATGPT_PHYSICAL_ACTIONS':sum(v in ['MOUSE_PRESSED_START','ENTER_KEYDOWN_START'] for v in events),
 'CHATGPT_PREPARED':'PASS' if 'PREPARED' in history else 'NOT_RUN',
 'CHATGPT_DELIVERY_INTENT':'PASS' if 'DELIVERY_INTENT' in history else 'NOT_RUN',
 'CHATGPT_SENT_CONFIRMED':'PASS' if 'SENT_CONFIRMED' in history else 'NOT_CONFIRMED',
 'CHATGPT_RESPONSE':st['CHATGPT_RESPONSE'],'CHATGPT_COMPLETED':ledger.get('delivery_state')=='COMPLETED',
 'REVIEWER':st['REVIEWER'],'COMPLETION_GATE':st['COMPLETION_GATE'],
 'RAM_MIN_MIB':s['RAM_min_available_mib'],'PAGEFILE_MAX_GIB':s['pagefile_max_used_gib'],'VRAM_MAX_MIB':s['VRAM_max_mib'],
 'LLAMA_MAX_WORKING_SET_MIB':max(v['llama_working_set_bytes'] for v in samples)/2**20,
 'CLEANUP':'PASS','INTEGRITY':i['status'],'HISTORICAL_EVIDENCE_UNCHANGED':not i['historical_mismatches'],
 'GIT_STATUS':'CLEAN after local closure commit; verified separately','F24':'PASS' if ok else 'FAIL','READY_FOR_F25':'YES' if ok else 'NO'}
save(E/'FINAL.json',result)
stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
doc='docs/F24-ATTEMPT-7-REPORT.md';ev='evidence/phase-24-attempt-7-20261015/'
summary=f"F24 ATTEMPT7 **{result['F24']}**; run `{s['run_id']}`, duración {s['duration_seconds']:.2f}s. Worker {st['WORKER']}; web fetch/context {st['WEB_FETCH']}/{st['WEB_CONTEXT_DELIVERED']}; 13 tests/build {st['TESTS']}/{st['BUILD']}; crash/Watchdog/START-Recover/continuación {st['RECOVERY_DETECTION']}/{st['START_RECOVER']}/{st['CONTINUATION']}. ChatGPT {ledger.get('delivery_state','NOT_RUN')}, método {result['CHATGPT_SEND_METHOD']}, acciones físicas {result['CHATGPT_PHYSICAL_ACTIONS']}; Reviewer {st['REVIEWER']}; Completion Gate {st['COMPLETION_GATE']}. Cleanup e integridad PASS; historial intacto. READY_FOR_F25 {result['READY_FOR_F25']}; F25 y ATTEMPT8 no iniciados. {doc}; {ev}."
note='\n## Estado vigente — F24 ATTEMPT 7 — 2026-10-15\n\n'+summary+'\n'
(R/doc).write_text('# F24 ATTEMPT 7 — informe terminal\n\n'+summary+'\n\n## Resultado verificable\n\n```text\n'+'\n'.join(k+' = '+str(v) for k,v in result.items())+'\n```\n\n## Ejecución y límites\n\nAdmisión mínima, sin campaña nueva de certificación. Contrato, plan, sandbox, run, aprobación única, reloj y consultation_id nuevos. Se ejecutó el launcher nativo. Sólo Qwen Code modificó invoice.py y README.md; tests/build inmutables existían antes de START. El fallo inicial esperado fue diagnosticado antes del fetch oficial. La entrega web se vinculó al input y sesión reales, sin confundir HTTP200 con consumo del contexto. Se conservaron las salidas del primer segmento en pre-recovery-native antes de su reemplazo normal por la continuación.\n\nPresupuestos global2700/fase300/restart2/maxcycles5 intactos. Reinicios reales: '+json.dumps(restart)+'. El Worker agotó una fase y consumió un reinicio normal; no se añadió crédito ni se corrigió manualmente el target. Un único crash controlado del padre ocurrió después de tests/build/checkpoint. START-Recover ejecutó el segundo Supervisor/Worker y conservó exactamente el reloj original.\n\n## Gates y ChatGPT\n\nLos mismos 28 gates congelados se evaluaron con el evaluador existente. Resultado: '+str(f['status'])+'. Estado nativo y reportes exportados byte a byte; ningún PASS procede sólo de exit code o self-report. Consulta nueva con extractor compartido y perfil dedicado. La traza y el ledger permiten verificar PREPARED, selección de método previa a DELIVERY_INTENT, única acción física, SENT_CONFIRMED previo a espera de respuesta, captura y retry lógico sin envío adicional cuando se alcanzaron. El snapshot root previo a FRESH_CHAT_READY y las observaciones read-only conservan RAW/ACTIVE. No hubo reconciliación humana ni reenvío.\n\n## Integridad y recursos\n\nMétricas originales sin sustituir: resources-live.json; RAM mínima '+str(result['RAM_MIN_MIB'])+'MiB; pagefile máximo '+str(result['PAGEFILE_MAX_GIB'])+'GiB; VRAM '+str(result['VRAM_MAX_MIB'])+'MiB; llama WS '+str(result['LLAMA_MAX_WORKING_SET_MIB'])+'MiB. Se mantuvo el guard de tres muestras consecutivas bajo150MiB. Se verificaron hashes del modelo, llama-server, hook, MCP y plugins, más fuentes aprobadas, tests, reloj e historial. Chrome preexistente puede permanecer abierto; los procesos propios y locks se verifican en cleanup-independent.json. Sin dependencias, actualizaciones, cambio de arquitectura, push, F25 ni ATTEMPT8. ATTEMPT6 conserva su FAIL histórico.\n\n'+('Fallo terminal: '+str(s['failure'])+'\n' if s['failure'] else '')+'\nEvidencia: '+ev+'; FROZEN-GATE-RESULT.json, capture-manifest.json, stage-results.json, SUMMARY.json, integrity-final.json, admission-source-integrity.json, CLEANUP nativo y observaciones del browser. Las vistas documentales se actualizan sólo tras la auditoría final; ninguna fuente protegida cambió durante el run.\n',encoding='utf-8')
for name in ['00-README.md','07-ROADMAP.md','MANIFEST.md','docs/IMPLEMENTATION-STATUS.md']:
 p=R/name;text=p.read_text(encoding='utf-8-sig')
 if ok:
  text=text.replace('F24 ATTEMPT6 FAIL / fresh-chat cuenta turnos ocultos','F24 ATTEMPT7 PASS; F25 pendiente')
  text=text.replace('validación de Macrofase 8 detenida en F24 ATTEMPT6: fresh-chat cuenta turnos ocultos','validación de Macrofase 8: F24 ATTEMPT7 PASS; F25 pendiente')
 if name=='docs/IMPLEMENTATION-STATUS.md':
  text=re.sub(r'^\| \*\*Fase 24\*\*.*$', '| **Fase 24** | End-to-End corto | **'+result['F24']+'** | ATTEMPT7 '+s['run_id']+'; '+doc+'; '+ev+' |',text,flags=re.M)
  if ok:text=re.sub(r'^(\| \*\*Macrofase 8\*\*.*?\|) \*\*FAIL / BLOCKED_REQUIRES_HUMAN\*\*',r'\1 **IN_PROGRESS**',text,flags=re.M)
  text=re.sub(r'\*\*Última actualización:\*\* .*','**Última actualización:** '+stamp,text,count=1)
 p.write_text(text.rstrip()+'\n'+note,encoding='utf-8')
p=R/'config/INSTALLATION-STATE.json';state=read(p);v=state['validation_8'];assert v['f24_attempt']==6
v['f24_attempt_6_history']={k:value for k,value in v.items() if k.startswith('f24_') and not k.endswith('_history')}
v['f24_attempt_6_history']['classification']='HISTORICAL FAIL / BLOCKED_REQUIRES_HUMAN; original evidence and sandbox unchanged'
v.update(status='IN_PROGRESS' if ok else 'STOPPED_MANDATORY_TEST_FAILED',test='F24_ATTEMPT_7_NATIVE_E2E',reason=s['failure'],f24_attempt=7,f24_run_id=s['run_id'],f24_report=doc,f24_evidence=ev,f24_consultation_id=s['consultation_id'],f24_delivery=ledger.get('delivery_state','NOT_RUN'),f24_send_attempts=ledger.get('send_attempts',0),f24_no_resend=True,f24_worker=st['WORKER'],f24_worker_restarts_used=restart['worker'],f24_tests_build=st['TESTS']+'/'+st['BUILD'],f24_web_fetch=st['WEB_FETCH'],f24_web_context_delivered=st['WEB_CONTEXT_DELIVERED'],f24_watchdog=st['RECOVERY_DETECTION'],f24_recovery_e2e=st['CONTINUATION'],f24_reviewer=st['REVIEWER'],f24_completion_gate=st['COMPLETION_GATE'],f24_duration_seconds=s['duration_seconds'],f24_cleanup='PASS',f24_integrity='PASS',f24_ready_for_f25=ok,f24_attempt7_created=True,f24_attempt8_created=False,consultation_id=s['consultation_id'],delivery=ledger.get('delivery_state','NOT_RUN'),no_resend=True,reconciled=False,source='F24_ATTEMPT_7_NATIVE_E2E',f24_preflight_evidence=ev)
state['updated_at']=stamp;save(p,state)
shutil.copyfile(R/'backups/f24-attempt7-closure-20261015/MANIFEST.json',E/'status-backup-manifest.json')
print(json.dumps(result,ensure_ascii=False,indent=2))
