# F24 ATTEMPT 4 — STOP: consumo web no demostrado

F24 = FAIL / MANDATORY_TEST_FAILED. READY_FOR_F25 = NO. El intento terminó
sin reanudar, sin mensajes ChatGPT, sin Reviewer y sin iniciar F25/F27/F28.

| Campo requerido | Resultado |
|:---|:---|
| CHATGPT_BRIDGE_FIX | PASS determinista; transporte real ATTEMPT4 NOT_RUN |
| SENT_RESPONSE_SEPARATION | PASS determinista; SENT irreversible y RESPONSE_PENDING sin resend |
| TRACEABILITY | PASS determinista; UTC/monotónico/fsync, sin prompt completo; trace real ATTEMPT4 NOT_RUN |
| WEB_HANDOFF | PASS determinista y entrega real; consumo real FAIL / NOT_PROVEN |
| RECOVERY_CONTINUATION | PASS sandbox con crash/Watchdog/START-Recover; ATTEMPT4 NOT_RUN |
| ATTEMPT_4_RUN_ID | run-20261014-201149 |
| DURATION | 729.54s nativos, 12m 9.54s; harness total 741.60s, incluido setup/cleanup |
| WORKER | Diagnóstico PASS; primera corrección TIMEOUT; reinicio normal 1/2, Worker final SUCCESS |
| WEB_FETCH | PASS, documentación oficial Decimal, HTTP 200 |
| WEB_CONSUMED | FAIL / NOT_PROVEN; no marcador ni SHA en salida del modelo |
| RECOVERY | Reinicio normal Worker ejecutado; crash controlado/START-Recover E2E NOT_RUN |
| CHATGPT | NOT_RUN; nuevo ID sin ledger, cero envíos físicos |
| REVIEWER | NOT_RUN |
| COMPLETION_GATE | NOT_EVALUATED |
| RAM_MIN | 72.97 MiB libres; mínimo puntual, sin parada por degradación sostenida |
| PAGEFILE_MAX | 3.3724 GiB utilizados |
| VRAM_MAX | 4640 MiB |
| CLEANUP | PASS; cero supervivientes propios, Run/Inference Lock FREE, 8080/9119 sin listeners |
| F24 | FAIL / MANDATORY_TEST_FAILED |
| READY_FOR_F25 | NO |

## Fronteras certificadas antes de START

- `aabf021`: presupuestos explícitos del bridge y padre, SENT irreversible,
  confirmación por conversación/user +1/SHA, trace y cleanup del hijo.
- `7de9bf9`: entrega explícita inline de investigación sanitizada y acotada,
  referencia absoluta/SHA/nonce y verificación de consumo sin ampliar permisos.
- `c846e2a`: crash/START-Recover sandbox real, continuación obligatoria antes de
  ChatGPT, consulta administrada por Runner y presupuesto conservado entre ticks.

Gate previo PASS: delivery (8), dominio exacto HTTPS (13), reconciliación humana
(41), idempotencia (8), click único (4), UTF-8, timeout/cleanup del hijo,
Runner/Watchdog/STATE/checkpoint, mutex real entre procesos, consumo web
determinista y cleanup. Cero mensajes reales durante esas pruebas.
Los tests deterministas del handoff no certifican que Qwen siga sus instrucciones
durante un E2E real. Esa frontera falló en ATTEMPT4 y no se rebajó el gate.

## Ejecución real y causa de parada

Sandbox nuevo: `sandbox/f24-attempt4-2fbcc7d8/project`. Prepare, preflight,
aprobación única y launcher nativos PASS. Contrato/plan/reloj/ID nuevos.
Límites efectivos: global 2700s, fase 300s, restart_budget 2, max_cycles 5;
Runner utiliza el mínimo del contrato, configuración y plan. Los valores
generales de Prepare (`time_budget_minutes=120`, STATE.max_cycles=20) no
ampliaron los límites más estrictos del plan; se preservan como fueron aprobados.
No se modificó ningún deadline o contador para facilitar el resultado.

Los 13 tests inmutables existían antes de START, incluidos pesos cero, importe
negativo, pesos negativos, suma cero y un peso positivo. Sólo Qwen Code modificó
invoice.py y README.md; Codex no corrigió la implementación objetivo.

Hermes Supervisor terminó, Qwen diagnosticó sin editar las fuentes y el Runner
confirmó FAIL inicial. Web obtuvo la fuente oficial. WEB_RESULT_PROVIDED quedó
persistido con SHA/nonce y ambos están presentes en el paquete real del Worker.
La primera corrección agotó sus 300s configurados (el wrapper reportó 305.45s
incluyendo terminación), conservó cambios y activó un reinicio permitido.
La salida TIMEOUT anterior se conservó antes de sobrescribir el log corriente.

El Worker final devolvió SUCCESS en 153.02s. Sus resultados de herramientas
capturados muestran 13 tests PASS y build PASS. Sin embargo, omitió el nonce y
SHA de investigación: ambos ausentes de su salida assistant/result. Por eso
WEB-CONSUMED.json registra WEB_RESULT_READ=false. No se infiere lectura a partir
del HTTP 200 ni de que README cite Decimal. No se reclama tests/build como gates
nativos finales: el control de consumo bloqueó esos pasos posteriores.

La causa nativa exacta fue RESEARCH_CONSUMPTION_NOT_PROVEN, conservada en EVENTS
y runner-result.json.previous. El finalizador del harness registró como motivo
secundario NATIVE_WORKER_CRASH_GATE_NOT_REACHED. Ambos se conservan; el segundo
no sustituye el diagnóstico de consumo. No se ejecutaron crash controlado,
START-Recover E2E, ChatGPT, Reviewer ni Completion Gate.
STATE es terminal FAILED; su next_action heredado alude a la tarea pendiente,
sin constituir autorización de continuación. Este informe impone STOP y no
se invocó START-Recover para este intento.

Consulta planificada, nunca ejecutada:
`f24-a4-3120338e4c054c608d367c0b8bc68c77`. No hay ledger ni trace para ese ID;
no hubo click, respuesta, retry físico ni lógico. La consulta histórica de
ATTEMPT3 continúa intacta y no se reconcilió ni reenvió.

## Integridad, recursos y cierre

Monitor continuo de RAM libre, working set llama, pagefile, VRAM y procesos.
Se conserva cada muestra; no se sustituyeron métricas anteriores. Modelo,
qwen36/127.0.0.1:8080/ctx65536/parallel1 e inferencia serial sin cambios.
Hermes productivo v0.21.6, sin actualizaciones ni dependencias nuevas.

Cleanup nativo y comprobación independiente PASS: sin procesos propios
huérfanos, sin metadata lock del run, mutex Run libre, Inference Lock FREE,
8080/9119 libres. Chrome dedicado preexistente conservado abierto.
Los 32 hashes aprobados, tests/build inmutables y reloj nuevo coinciden.
419 archivos históricos intactos, incluidos sandbox/clock/STATE/ledgers de
ATTEMPT2 y ATTEMPT3 y evidencia F23. ATTEMPT3 sigue HISTORICAL FAIL /
BLOCKED_REQUIRES_HUMAN; no se intentó convertirlo en PASS.

Evidencia completa: `evidence/phase-24-attempt-4-20261014/`, con SUMMARY,
STOP-CLASSIFICATION, artefactos, diff, 52 copias verificadas de fuentes nativas,
logs, resultados de herramientas Worker, recursos, integridad y cleanup.
`secret-scan.json` verifica las capturas antes de staging; backups documentales
locales en `backups/f24-attempt4-close-20261014/`.
La certificación A/B/C y smokes está en `evidence/f24-frontiers-20261014/`.
No se modifican evidencias históricas. Commit local de cierre separado;
NO PUSH. Macrofase 8 no certificada; regression global final NOT_RUN.
