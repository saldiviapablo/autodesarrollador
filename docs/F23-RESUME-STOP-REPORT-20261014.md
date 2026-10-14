# F23 reanudada — parada ante nuevo gate obligatorio

Fecha: 2026-10-14. Rama agent/macro8-20261013. NO PUSH.

La reconciliación humana solicitada terminó PASS. F23 se reanudó en el mismo
sandbox y llegó a tests/build PASS y recuperación desde disco PASS. La revisión
independiente no pudo ejecutarse por un fallo de transporte de argumentos del
prompt a Hermes. Se agotó el único reinicio Reviewer aprobado y el Runner
terminó FAILED. No se empezó F24–F28 ni se evitó el Reviewer/Completion Gate.

| Gate | Resultado |
| --- | --- |
| HUMAN_VISUAL_RECONCILIATION | PASS |
| Consulta original, mismo consultation_id | PASS |
| User turn +1 / assistant turn +1 | PASS, 0→1 / 0→1 |
| UTF-8 y composer vacío | PASS |
| Un nuevo intento físico autorizado | PASS, un solo click |
| Retry lógico mismo ID | ALREADY_SENT / 0 envíos adicionales |
| Budget | 1→1, una sola consulta lógica |
| Prepare/Path Guard/MCP/plugin smokes | PASS certificado, sin repetir suites |
| Web y consulta ChatGPT real | PASS certificado / respuesta usada como consejo |
| Hermes Supervisor y Qwen Code Worker | Ejecutados realmente |
| Tests / build del sandbox | PASS / PASS |
| Crash controlado, Watchdog, checkpoint y recovery | PASS |
| Reviewer independiente | FAIL, argparse ExitCode=2 |
| Completion Gate | NOT_REACHED |
| F23 integral | FAIL / MANDATORY_TEST_FAILED |
| F24/F25/2H/4H/F26/regression final | NOT_RUN |
| F27/F28 | NOT_RUN |
| Cleanup e integridad | PASS |
| READY FOR REAL PILOT | NO |

## Reconciliación solicitada

ID único conservado: **f23-ee298529568f4f8b94f4dd16f90a0be4**.
La inspección humana confirmó DELIVERY_NOT_OCCURRED. La comprobación read-only
corroboró cero turnos, hash de composer idéntico al prompt reservado y botón
Enviar disponible. Se registró HUMAN_VISUAL_RECONCILIATION y
NOT_DELIVERED_CONFIRMED / RETRY_SAFE mediante el ledger existente, con una sola
habilitación consumible. El historial ambiguo no se borró ni se reseteó su contador.

Se comprobó el perfil HERMES-CHATGPT real propietario de CDP, HTTPS/hostname
exacto chatgpt.com, contenido, UTF-8, sanitizador, STATE/budget y ledger.
No se insertó ni duplicó texto: se utilizó el composer existente. Un único click
físico confirmó el envío; user 0→1, assistant 0→1, respuesta capturada y composer
vacío. Ledger SENT → COMPLETED. send_attempts=2 conserva la intención antigua y
el intento nuevo autorizado; no significa dos entregas. queries_used sigue 1.

Retry lógico del mismo ID: ALREADY_SENT, send_attempts sin cambio y ningún nuevo
envío. El token humano queda consumido y no permite otro retry. Pruebas
deterministas y domain lock PASS. Commit separado:
**cd44d38689b81e233b4dac43602d4e68eabfc01c**
`fix: reconcile human-confirmed unsent ChatGPT consultation`.

Detalle y evidencia: docs/F23-HUMAN-RECONCILIATION.md y
evidence/f23-human-reconciliation/. Todos los intentos históricos permanecen
ligados por SHA-256 y sin reescritura.

## Reanudación y nuevo fallo

Se reutilizó sandbox/f23-full-feac8aea/project y RUN-CONTRACT
run-20261013-202418. No hubo nuevo Prepare, consulta ni repetición de A–J.
La respuesta y WEB.json se ligaron como inputs inmutables antes de una aprobación
Runner. Qwen Code corrigió calculator.py y README.md; los tests inmutables
imprimieron F23_UNIT_DOC_PASS y el build F23_BUILD_PASS con exit 0.

Se inyectó un crash del padre cuando apareció el worker real, verificando PID y
birth. El Job Object cerró sus descendientes; Watchdog guardó checkpoint y
PARENT_PROCESS_LOST, soltó lock y dejó owned_survivors=[] / inference_mutex FREE.
El segundo arranque -Recover reutilizó la aprobación y registró
RUN_RECOVERED_FROM_DISK. La recuperación y el cleanup no son simulaciones de
inferencia: Supervisor y Worker realizaron llamadas locales reales serializadas.

El Reviewer falló dos veces antes de producir una revisión. El wrapper devuelve
Hermes ExitCode=2, stderr `unrecognized arguments`, con fragmentos del diff y
del JSON de checks recibidos como argumentos separados. El diff incluye strings
entre comillas como `"missing rounding feature"` y `"0.01"`; la evidencia indica
un fallo de transporte/quoting de prompts complejos en la invocación CLI.
No se atribuye el fallo al criterio del modelo: no hay revisión válida.

Runner hizo el único reinicio Reviewer permitido y terminó con
**AGENT_RESTART_BUDGET_EXHAUSTED:reviewer**. Se aplicó la parada por nuevo gate
obligatorio. No se corrigió otro componente silenciosamente, no se incrementó
el presupuesto y no se declaró COMPLETED sin Reviewer/Completion Gate.
El código del sandbox y sus cambios pendientes se preservan para continuar.

## Recursos reales y cleanup

71 muestras durante aproximadamente 362 s, dos ciclos de vida del modelo
separados por el crash controlado. RAM disponible mínima **68.64 MiB / 0.067 GiB**;
working set llama máximo **19.468 GiB**; VRAM máxima **7028/8188 MiB**.
Pagefile usado inicial **0.816 GiB**, pico **2.923 GiB**, último **2.25 GiB**.

Hubo un mínimo transitorio inferior al antecedente 7B de 0.38 GiB, seguido de
recuperación. El umbral de tres muestras consecutivas bajo 150 MiB no se activó.
Esto no demuestra estabilidad de dos horas ni ausencia de fugas/paging excesivo.
F25/4H siguen NOT_RUN. No se redujeron ctx, modelo ni paralelismo.

Cleanup PASS: llama y todos los procesos propios detenidos, mutex de run e
inferencia liberados, LOCK.json retirado y checkpoint terminal FAILED guardado.
El Chrome que el usuario pidió dejar abierto es preexistente a esta reanudación
y se conserva (PID 26768, CDP 9222). No se clasifica como huérfano ni se mata.
No quedan listeners inesperados de infraestructura; 8080 y 9119 libres.

SHA-256 completos de modelo/llama y hashes de componentes protegidos PASS;
Hermes v0.21.6 / HEAD 818c13be1dc4fd28987e1e881a9408224afd4535 preservados.
qwen36 / 127.0.0.1:8080 / ctx 65536 / parallel 1 intactos. Cero dependencias
nuevas, actualizaciones, cambios de políticas/hashes aprobados o push.

Evidencia nueva en evidence/phase-23-resume-20261014/: integral-result.json,
native-result.json, injection.json, watchdog-failure.json, reviewer.stdout.txt,
reviewer.stderr.txt, resources-live.json, resource-summary.json,
cleanup-final.json y protected-integrity-final.json.

Git de infraestructura limpio tras commit de parada separado; registro final
exacto en runtime/f23-human-resume-final-git.json. El Git del sandbox conserva
dos archivos modificados sin aprobar; no se hicieron pasar por un commit validado.

**RECONCILIACIÓN HUMANA = PASS. F23 = FAIL. READY FOR REAL PILOT = NO.**
