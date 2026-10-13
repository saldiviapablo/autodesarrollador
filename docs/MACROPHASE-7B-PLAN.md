# Plan de implementación 7B

Base inspeccionada: 8ec42f4; 1–6 y 7A PASS. PREFLIGHT: evidence/preflight-7b/.
Orden: INSPECT → PLAN → BACKUP → IMPLEMENT → VERIFY → DOCUMENT → commit local.

1. F17 Runner: PowerShell 5.1, mutex exclusivo global, contrato y plan ligados a
   digest aprobado una sola vez; ruta canónica, procesos por PID/start time,
   Job Object, llama owned/adopted, health, heartbeat, wrappers existentes,
   STATE/EVENTS/checkpoints, timeouts y finally. Observer Watchdog mínimo de ciclo
   de vida para T-RUN-009; F18 completa recuperación y pruebas de fallos.
2. F18 Watchdog: observación independiente, heartbeat y roles/llama, reinicios
   acotados, recuperación desde disco. Pruebas con procesos reales registrados.
3. F19 BAT simples y STOP persistido, sin lógica de lifecycle en los BAT.
4. F20 Completion Gate: predicados ejecutables ligados a cada criterio aprobado,
   tests/build/linters/artifacts/diff/pending/state; falsos DONE y exit0 rechazados.
5. F21 informes humanos + JSON sanitizados, todos los terminales.
6. F22 teardown/finally/Job Object, STOP/Ctrl+C/crash; preservar externos.
7. E2E corto real completo y fallo controlado; regression smoke 1–7A; cierre Git.

RUN-CONTRACT y sus restricciones no cambian. RUN-PLAN.json expresa únicamente
argv de comprobaciones, marcadores, archivos permitidos/inmutables y artefactos
esperados; también forma parte del digest de aprobación. La autoridad nunca
deriva de una declaración del LLM. Se conserva Inference Lock de cada wrapper;
Runner no adquiere una lease alrededor de un wrapper que ya la adquiere.

Managed project distinto de infraestructura. Un modelo preexistente compatible
puede adoptarse, conserva ownership EXTERNAL y no se detiene/reinicia como propio.
Un Job Object del Runner contiene auxiliares y modelo creado por este run; su
cierre kernel elimina descendientes aunque el padre termine abruptamente.
Hasta instalar/certificar el gate completo de F20 no se declara un run COMPLETED.

Sandbox primero; pruebas livianas aisladas y smoke real de roles/modelo. Ninguna
actualización de Hermes/Qwen/llama/Node/Python. Sin cambios Windows globales ni
drivers. Commits separados, NO PUSH. No iniciar Macrofase8.
