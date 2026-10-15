# F24 ATTEMPT 5 — STOP en precheck del botón ChatGPT

F24 = FAIL / BLOCKED_REQUIRES_HUMAN. READY_FOR_F25 = NO. No se reenvía ni
reconcilia la consulta. No se inicia ATTEMPT6, F25, F27 ni F28.

| Resultado requerido | Estado |
|:---|:---|
| WEB_GATE_FIX | PASS |
| F24_HARNESS_PREFLIGHT | PASS: 17 grupos, sin inferencias reales ni mensajes ChatGPT |
| TOTAL_GATES_FROZEN | 28, catálogo/condiciones/evidencia/productor/verificador aprobados antes de START |
| HARNESS_ISSUES_FOUND_AND_FIXED | Ver docs/F24-WEB-GATE-FIX.md; correcciones y fallos previos conservados |
| RUN_ID | run-20261014-210131 |
| DURATION | 684.78s nativos (11m 24.78s); harness total 697.73s incluyendo setup/cleanup |
| WORKER | SUCCESS en corrección y continuación; cero reinicios de agentes |
| WEB_FETCH | PASS |
| WEB_CONTEXT_DELIVERED | PASS antes y después del recovery |
| TESTS | PASS, 13 tests inmutables y sus subcasos |
| BUILD | PASS antes y después del recovery |
| RECOVERY_DETECTION | PASS |
| START_RECOVER | PASS, invocación real posterior al Watchdog |
| CONTINUATION | PASS, Supervisor/Worker/checks nuevos después de recuperar STATE/checkpoint |
| CHATGPT_SENT | FAIL: SEND_BUTTON_UNAVAILABLE_OR_AMBIGUOUS; send_attempts=0 |
| CHATGPT_RESPONSE | NOT_RUN |
| REVIEWER | NOT_RUN |
| COMPLETION_GATE | NOT_EVALUATED |
| RAM_MIN | 845.875 MiB libres |
| PAGEFILE_MAX | 2.01074 GiB utilizados |
| VRAM_MAX | 4455 MiB |
| CLEANUP | PASS |
| F24 | FAIL / BLOCKED_REQUIRES_HUMAN |
| READY_FOR_F25 | NO |

## Preflight y correcciones anteriores al START

Commit `8c8bfdf`: sustitución del eco artificial por evidencia determinista de
input despachado y sesión, separación WEB_FETCHED/WEB_CONTEXT_DELIVERED/
TASK_RESULT, 28 gates congelados, aprobación de wrappers/harness y correcciones
del test de cleanup, datos del Reviewer y presupuesto STATE cacheado.
La reserva inicial del presupuesto podía fallar si la copia cacheada no tenía
chatgpt: prueba enfocada reproduce el fallo y verifica max(used)/min(limit) tras
el fix bajo el mismo mutex, sin crédito nuevo.

Commit `c2b1268`: comprobación de imports con el Python Hermes real y uso del
Python canónico para PyYAML. El import inicial falló antes de crear sandbox,
run_id, reloj o consulta y antes de Prepare/START. Se corrigió conforme a la
autorización de autocorregir el harness antes del START; no fue otro E2E iniciado
ni una extensión de presupuesto. No se instalaron dependencias.

Preflight PASS: casos A–J del gate web, argv real/UTF-8 en wrapper, Qwen CLI
instalado y su request real contra endpoint OpenAI simulado, catálogo/evaluador
de 28 gates, presupuesto cacheado, ChatGPT delivery/domain/idempotencia/human/
click único/cleanup de hijo, launcher A–H, transporte nativo Reviewer complejo,
Completion Gate con casos negativos, crash/Watchdog/START-Recover/checkpoint,
cleanup y mutex entre procesos. Snapshot sellado de 34 fuentes. No se confunde
el endpoint simulado con inferencia real ni con un E2E.

ATTEMPT4 conserva su FAIL histórico con las reglas de ese momento; no se cambió
su ledger, sandbox, reloj, aprobación o evidencias. ATTEMPT3 sigue histórico
UNKNOWN_DELIVERY; no se reconcilió ni reenvió. F23 PASS preservada.

## E2E ejecutado y frontera aprobada

Sandbox nuevo `sandbox/f24-attempt5-e6230453/project`. Prepare, preflight y
aprobación única preceden al launcher nativo. Contrato y STATE reflejan 45
minutos y max_cycles=5 antes de aprobar. Límites efectivos normales:
global2700/fase300/restart2/maxcycles5. Un solo reloj, intacto durante recovery.

Supervisor real PASS; Worker diagnóstico conserva fuentes y obtiene FAIL real.
Fetch oficial HTTP200 de Decimal guardado con URL/SHA. Qwen corrige únicamente
invoice.py y README.md, devuelve SUCCESS y Runner ejecuta tests/build PASS.
Codex no modificó la implementación objetivo. Tests/build iniciales permanecen
inmutables por SHA. No se añadieron requisitos funcionales después del START.

WEB_CONTEXT_DELIVERED PASS ya no exige nonce/SHA en assistant/result. El wrapper
persiste input exacto, SHA, rango UTF-8 del bloque, SHA del payload/fuente,
sesión y PID/start ticks/timestamp. El verifier enlaza el resultado del proceso
con esa sesión y vuelve a comprobar bytes/fuente. Hay dos recibos de despacho
reales, antes y después del recovery. No se afirma comprensión cognitiva.

Checkpoint inmutable antes de un único crash del parent identificado por PID y
birth. Watchdog detecta PARENT_PROCESS_LOST, limpia y libera. START -Recover
real carga STATE/checkpoint; Supervisor y Worker continúan y se ejecutan nuevos
procesos test/build PASS después de recovery. No se reutilizan los checks
previos como sustituto de esa continuación. Cero reinicios de agentes/modelo
por timeout; el crash del parent es la inyección aprobada, no un reset de
contadores. El Worker final reporta 166.30s, dentro de su ventana de fase.

## Parada ChatGPT y preservación de entrega

ID nuevo: `f24-a5-cfe02556f1f3490eb027139d8e5620ae`.
URL registrada `https://chatgpt.com/`, baseline 0/0. Presupuesto reservado 1/5.
Prompt SHA-256 `449d9d63fff353617d1d5f0f54ce75cf61186f1e8f2251586a8455a119ce056e`.

La comprobación CDP del botón no aprobó disponibilidad/unicidad:
SEND_BUTTON_UNAVAILABLE_OR_AMBIGUOUS. La trace registra BRIDGE_START, FAILURE
y CLEANUP. No registra DELIVERY_INTENT ni mousePressed/mouseReleased, no hay
SENT_CONFIRMED y el contador físico es cero. No se atribuye una causa DOM más
precisa sin evidencia. Este fallo es distinto del antiguo parent timeout:
el hijo devuelve ERROR y termina normalmente, sin vencer el deadline padre.

Ledger persistido UNKNOWN_DELIVERY, send_attempts=0; no_resend=true en el
resultado nativo. No se cambia ese estado, no se descuenta la reserva, no se
reintenta y no se realiza reconciliación humana para convertir el E2E en PASS.
Respuesta, Reviewer y Completion Gate no se alcanzan. La evaluación completa
de los 28 gates no es PASS; se conserva un estado parcial con el bloqueo.
El terminal nativo es BLOCKED_REQUIRES_HUMAN y el siguiente paso exige STOP.

## Cleanup, integridad y evidencia

Cleanup nativo y verificación independiente PASS: cero procesos propios
huérfanos, metadata lock del run ausente, Run mutex e Inference Lock FREE,
8080/9119 sin listeners. Chrome HERMES-CHATGPT preexistente conservado abierto;
sin nueva acción manual en el browser tras el fallo.

42 hashes de aprobación intactos, fuentes de tests/build intactas, reloj sin
cambios y 629 archivos históricos preservados. La copia de stdout del Worker
anterior al crash coincide con el SHA del recibo original. 82 copias verificadas
de .autopilot/artefactos/ledger/trace preservan los bytes originales. El ledger
del nuevo ID se exporta sólo en lectura, sin cambios del auditor.
Modelo/configuración qwen36/127.0.0.1:8080/ctx65536/parallel1 e inferencia
serial preservados. Sin actualizaciones ni dependencias nuevas.

Evidencia: `evidence/phase-24-attempt-5-20261014/`; preflight:
`evidence/f24-harness-preflight-20261014/`. Se guardan logs de ambos segmentos,
recibos/input de despacho, checks, checkpoints, eventos, artefactos/diff,
métricas continuas, ledger y traces, cleanup e integridad. Se conservan los
FAIL anteriores. Commit local separado de cierre, NO PUSH; Git limpio al final.
Macrofase 8 sigue FAIL; regression global posterior y F25 no ejecutadas.
