# F24 — evidencia determinista de entrega web

ATTEMPT4 permanece HISTORICAL FAIL / MANDATORY_TEST_FAILED bajo el gate vigente
durante su ejecución. No se reescriben sus evidencias ni se recertifica ese run.
ATTEMPT3 conserva UNKNOWN_DELIVERY; no se envía ni reconcilia su consulta.

La definición operativa nueva separa tres resultados:

1. WEB_FETCHED: respuesta HTTP 200 real, URL y contenido persistidos, SHA-256 del
   registro fuente verificado. WEB-FETCHED.json registra productor y timestamp.
2. WEB_CONTEXT_DELIVERED: el wrapper guarda el input exacto despachado a Qwen,
   su SHA-256, rango UTF-8 del bloque inline, SHA de fuente y payload, run/project,
   dispatch_id, session_id, PID/start ticks y dispatch timestamp. PREPARED no
   basta: el proceso debe haberse iniciado y terminado correctamente y su sesión
   init debe coincidir. El verifier revalida bytes, bloque, fuente y sesión.
3. TASK_RESULT: tests/build/aceptación completa, diff, artefactos, pendientes,
   Reviewer independiente read-only y Completion Gate siguen obligatorios.

El wrapper utiliza el mismo Prompt para el archivo de prueba y para argv de
ProcessStartInfo. Un proceso Node determinista prueba el transporte real de
argv, incluyendo comillas, saltos y UTF-8, sin inferencia. Se comprueba
además el transporte con el Qwen CLI instalado contra un endpoint OpenAI
simulado propio: el bloque/SHA/rango aparece en el request real del modelo y
la sesión coincide; cero inferencias locales y cero mensajes ChatGPT. Se
conserva el primer fallo del fixture por conversión CRLF y su corrección a
bytes UTF-8 exactos, sin normalizar silenciosamente el payload de producción.
El contrato aprueba
ahora también los hashes de wrappers de Qwen/delegación/Hermes y del catálogo,
harness y fixture. La raíz/ruta se valida antes de crear archivos; secretos
detectados impiden persistir el input. El resultado web sigue siendo dato
pasivo sanitizado/acotado; no amplía permisos.

No se exige nonce, SHA ni marcador en assistant/result. El mode inline no exige
read_file. File-mode se rechaza sin una prueba separada de acceso real de
herramienta; no se introduce implícitamente ese modo. No se afirma lectura o
comprensión cognitiva del modelo. Los recibos certifican el input despachado y
la ejecución del Worker con esa sesión; la corrección la deciden los gates
funcionales posteriores.

Pruebas A–J: fetch+input real PASS; ausencia, SHA erróneo, fuente modificada,
truncamiento, Worker no iniciado, sesión distinta y file-mode sin acceso DENY;
inline y ausencia de eco PASS. Test del evaluador de 28 gates con metadata
sintética explícita: shape completo PASS; Completion fallido y prueba de
idempotencia ausente DENY. Nunca se presenta esa metadata como un E2E real.

## Auditoría previa de harness

Catálogo cerrado: docs/F24-GATES.json, 28 gates con condición exacta, evidencia,
productor y verificador. Se congela por SHA antes de START y se liga a la
aprobación. El harness exige todos esos gates al terminar. El nuevo contrato
pre-approval refleja 45 minutos y STATE.max_cycles=5; no se extiende ningún
presupuesto después del START. Plan: 2700s/fase300/restart2/maxcycles5.
Los 13 tests y criterios monetarios aprobados permanecen intactos.

Defectos encontrados y corregidos antes de START:

- Gate web basado en eco del modelo: sustituido por binding de despacho.
- Wrappers/harness de frontera fuera del conjunto de aprobación: hashes nuevos
  incluidos sin modificar recibos/aprobaciones históricos.
- Reviewer recibía objetivo/diff/checks pero no la tarea y fuentes de aceptación
  completas: ahora recibe también task, criteria y tests/build inmutables.
- Metadatos generales de Prepare divergían de límites efectivos: se alinean en
  el nuevo sandbox antes de la única aprobación.
- El motivo genérico del harness ocultaba la causa nativa: se conserva como
  principal la causa del Runner; next_action terminal del finalizador dice STOP.
- Test cleanup observaba al guardian antes de su salida posterior al reporte:
  ahora espera su terminación física con PID/birth hasta 10s y falla si sobrevive.
- STATE cacheado sin chatgpt fallaba al fusionar la primera reserva nueva:
  reproducción determinista y fix bajo el mutex existente. Se copia primero el
  presupuesto persistido ausente y se aplica max(used)/min(limit), sin crédito
  adicional. La prueba anterior de recovery no cubría esa forma exacta del cache.
- Tests legacy tenían destinos históricos: se parametrizan con directorio nuevo.
  El primer idempotency test regeneró su salida histórica y se restauró sólo ese
  archivo propio desde HEAD; no hay cambio neto. La prueba humana conservaba un
  baseline del bridge anterior al hardening ya aprobado: el nuevo snapshot se
  compara primero contra Git HEAD, sin tocar el histórico ni el bridge.

Los primeros fallos de preflight se conservan en la carpeta nueva. No hubo
inferencia ni mensajes ChatGPT en esos tests. No se cambian security.yaml,
Inference Lock, hooks ni configuración qwen36/127.0.0.1:8080/ctx65536/parallel1.
Hermes v0.21.6 permanece sin actualizar. Sin dependencias nuevas. NO PUSH.

Evidencia: evidence/f24-harness-preflight-20261014/. El archivo PREFLIGHT.json
es la autorización técnica: ATTEMPT5 sólo puede iniciarse cuando exista PASS.
F24 sigue FAIL hasta que un E2E nuevo apruebe todos los gates. F25 no autorizada.
