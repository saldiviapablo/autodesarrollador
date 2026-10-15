# Revisión explícita del roadmap — F28 eximida por el usuario

F28_ORIGINAL_6_8H = WAIVED_BY_USER
F28_NOT_EXECUTED = TRUE
F28_REPLACED_BY = CERTIFIED_4H_ENDURANCE + F27_REAL_PILOT + FINAL_REGRESSION

La instrucción humana del15-10-2026 sustituye únicamente el gate original de6–8h. No autoriza iniciar F28 ni marcarla PASS. La validación prolongada aceptada es4H PASS,14781.2786871s reales,26 tareas, recovery/Reviewer/Completion/resources/cleanup/integrity PASS (bd822cf). F24/F25/4H/F26 PASS no se repiten.

El F27 que estaba activo continuó sin detenerse/reiniciarse desde fuera del Runner y sin aumentar restart_budget: run-20261015-165354. Final nativo COMPLETED1097.308088s;17 tests/build PASS, consumo web ligado al input real, Reviewer ACCEPTED/read-only y Completion COMPLETED. Sus2 reinicios normales permanecen registrados. Cierre técnico/cleanup/integridad PASS(cc3b9c9). Primer F27 FAIL histórico preservado.

La revisión humana final de F27 continúa requerida por07§30; la exención de F28 no la sustituye. El paquete concreto está en docs/F27-TECHNICAL-REPORT-f27-20261015-165308-d37c78.md. No se fabrica una revisión ni se acredita F27 completo por una aprobación inicial de ejecución.

La regresión/auditoría finales bajo este roadmap requieren F27 completo y la exención explícita ligada por SHA a4H real. Conservan los controles de seguridad, fuentes aprobadas, modelo/contexto/serialización, idempotencia, NativeRunner/Watchdog/Reviewer/Completion, cleanup e integridad. El controlador originalF28 deniega entrada antes de crear cualquier run. Las11 pruebas de la exención,12 de admisión y15 del piloto PASS son certificación aislada; no equivalen a la regresión final todavía pendiente.

Sólo después de todos los demás gates finales PASS puede declararse PROJECT_STATUS=COMPLETE bajo roadmap revisado. No constituye una prueba de6–8h. Arquitectura, guardrails, contratos anteriores, presupuestos y evidencia histórica se preservan. No push.

Evidencia: evidence/revised-roadmap-f28-waiver-20261015-171813/; USER-DIRECTIVE.txt conserva la instrucción y USER-F28-WAIVER.json liga la exención a la4H aceptada.
