# F27 — piloto local descartable autorizado

Sólo se ejecuta después del cierre F26 PASS, Git limpio y ausencia de otro controlador. El usuario autorizó explícitamente un proyecto sintético dentro de workspace/sandbox: esta autorización sustituye únicamente la ubicación fuera del sandbox del objetivo original07§30. No se selecciona ningún proyecto personal ni productivo.

El piloto entrega un CLI stdlib de reportes JSON/Markdown de ejecuciones sintéticas. La especificación completa y17 tests inmutables existen antes de START: validación exacta de entradas/estados/IDs únicos Unicode, segundos finitos/no negativos/límite superior, Decimal ROUND_HALF_UP, copia sin mutar, orden, sumas/conteos/máximo, formato Markdown y escape de pipes, CLI y errores fail-closed, documentación y ejemplos. build.py y sample-records.json también quedan fijados por SHA antes de la aprobación única. El seed tiene un bug de redondeo y funciones faltantes; sólo Qwen Code puede resolverlo tras START.

Se conserva backup de archivos y Git HEAD/branch/estado/hashes iniciales. El repositorio Git original permanece en el sandbox; sus internals no se incluyen como repositorio anidado en evidence. Rama local independiente, sin push.

Recorrido real: launcher/Prepare/preflight/aprobación/Runner/modelo/Hermes Supervisor/Qwen diagnóstico FAIL/web oficial con handoff al modelo/corrección/tests/build/checkpoint/Reviewer independiente read-only/Completion Gate/reporte/cleanup. F27 no añade una consulta ChatGPT o crash artificial; estos ya se ejercitaron realmente en F24/F25/4H. El primer workload de F28 sí los exige nuevamente.

Cada contrato tiene global1800s/fase300s/restart2/maxcycles5. El guard del controlador no extiende el reloj nativo. El modelo inicia una vez y se cierra al terminar. Inference Lock físico serializa roles con qwen36/127.0.0.1:8080/ctx65536/parallel1. Monitor real de recursos/health; no actualizaciones ni dependencias nuevas.

Se exige la aceptación completa, tests/build, diff permitido, pendientes vacíos, STATE terminal, artefactos, Reviewer ACCEPTED y Completion COMPLETED. El observador verifica todo el target y Git HEAD durante el Reviewer final aceptado; conserva baselines de revisiones anteriores, sin confundir cambios legítimos del Worker entre ciclos con escrituras del Reviewer. Un test negativo conserva el rechazo de una edición durante el Reviewer final; la corrección legítima entre dos revisiones pasa. El Reviewer productivo y su política read-only no cambian.

El cierre técnico verifica copias nativas, reloj, aprobaciones, SHA de tests/fuentes/componentes protegidos/histórico, recursos, cero procesos propios/locks/puertos8080/9119 e Inference Lock FREE. Chrome HERMES-CHATGPT preexistente puede permanecer.

La condición de salida de07§30 incluye «revisión humana final». TECHNICAL_PASS_AWAITING_HUMAN_REVIEW no equivale a F27 PASS. Sólo después del resultado real se entrega el paquete de7 archivos con hashes, código/diff/README/reportes, y se solicita la revisión humana del resultado. No se fabrica un receipt ni se inicia F28 sin esa confirmación real.

F28 preparado reutiliza copias byte exactas del piloto realmente revisado y de su reporte anterior, con memoria inmutable/hash chain y23 tests previos. Es preparación, no ejecución ni certificación de6–8h.
