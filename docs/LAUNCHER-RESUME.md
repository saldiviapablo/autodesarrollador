# Continuación de la mejora del iniciador

NO empezar de cero ni revertir. NO Computer Use, cursor, teclado gráfico ni capturas. NO F24/F25/4H/F26/F27/F28 ni push.

La lógica CLI está certificada. Leer el CHECKPOINT y la guía; no repetir los 20 tests originales. Sólo queda la certificación manual final y el smoke real del nuevo flujo. El usuario revisa y aprueba; jamás generar una aprobación para el run real desde un fixture.

Sandbox A: C:\Users\Pc\Documents\Proyectos Tech\Desarrollador autonomo\sandbox\launcher-live-A á ñ
Brief: C:\Users\Pc\Documents\Proyectos Tech\Desarrollador autonomo\runtime\project-launcher\manual-briefs\objetivo-A.md

El draft cacheado es exactamente la propuesta real de Hermes, revalidada contra los hashes actuales y sin ninguna aprobación. Usar Abrir .md o .txt conserva el objetivo exacto y evita repetir inferencia. El modelo sigue qwen36/127.0.0.1:8080/65536/parallel1.

Cuando se abra un diálogo, pedir acción humana clara y esperar. La prueba puede observarse por CLI con tests/observe-launcher-manual-smoke.py: no controla la GUI, no aprueba y sólo solicita STOP mediante el mecanismo productivo cuando existan Supervisor exitoso y Node Qwen CLI realmente iniciado. Guardar sus resultados de runtime como evidence al concluir. No declarar la mejora PASS hasta ese gate y la inspección manual.

Proyecto existente, .md/.txt, cancelación, aislamiento e historial ya tienen pruebas de controller/Prepare; sólo un chequeo visual manual por flujo que lo necesite. Mantener cada FAIL previo. Tras completar: consolidar informe, actualizar estado y guía, commit local y Git limpio.

Checkpoint: evidence\launcher-usability-checkpoint-20261015-225852

## Continuación manual pendiente — 2026-10-15 23:26

El usuario seleccionó sandbox A, cargó el brief y la GUI registró HUMAN_PLAN_REVIEW a las 23:17:39. Prepare PASS; run `run-20261015-231741` empezó a las 23:17:45 con llama health PASS. El observador solicitó STOP a los 240 segundos antes de que terminara Supervisor; Qwen no llegó a iniciarse. Run ABORTED/STOP_REQUESTED, checkpoint y cleanup PASS. No certificar todavía el smoke Supervisor/Worker.

FAIL preservado: `evidence/launcher-manual-smoke-fail-20261015-232458/`. La prueba tenía un corte de 240s incompatible con una fase aprobada de 300s más el arranque del modelo. Sólo se corrigió el observador: ventana finita derivada de fase y arranque, limitada al tiempo restante real; al continuar exige un RUN_STARTED nuevo y descarta eventos anteriores. Ocho controles aislados PASS: `evidence/launcher-observer-cert-20261015-232545/`. Regresión final de controller 19/19 PASS: `evidence/launcher-final-regression-20261015-232045/`.

No se modificaron contrato, plan, reloj, contadores, Runner ni código objetivo. La falta de respuesta del Supervisor antes de la parada no demuestra que hubiese completado dentro de sus 300s. Eso sigue pendiente de prueba real.

Leer `runtime/project-launcher/MANUAL-RESUME.json` para la identidad exacta del nuevo observador CLI. Espera el siguiente RUN_STARTED; no controla GUI ni aprueba. Acción humana: cerrar Resultado: ABORTED, abrir el iniciador fijo, seleccionar la MISMA carpeta A y pulsar Continuar proyecto. No Nuevo objetivo. Antes de continuar comprobar que queda tiempo en el reloj original; si venció, detenerse sin renovarlo. No repetir la planificación ni pedir otra aprobación del mismo contrato.

## Estado final — 2026-10-15 23:45

La mejora está certificada PASS. Los párrafos anteriores conservan la secuencia histórica y sus pendientes ya resueltos; no reanudar el sandbox. Informe vigente: `docs/LAUNCHER-FINAL-REPORT.md`. Evidencia final: `evidence/launcher-final-certification-20261015-234100/` e `evidence/launcher-integrity-20261015-234108/`.

El usuario continuó realmente el proyecto preparado. Supervisor terminó exit 0 y se verificó el Node Qwen CLI real (PID 18868, descendiente del Worker 33316). El observador falló al decodificar la salida OEM de PowerShell; se preservó ese FAIL. Se recuperó la prueba por CLI con salida UTF-8 explícita y se solicitó STOP productivo al mismo run, sin reiniciar nada. Cleanup PASS, run ABORTED/STOP_REQUESTED, objetivo no completado. El lector corregido y el stop de emergencia del observador pasan 13 tests más CIM UTF-8 real. No repetir la GUI ni la inferencia.

Reloj, contrato, plan y contadores originales conservados; una sola aprobación humana. Integridad final PASS; locks y puertos libres. La ventana Resultado puede permanecer abierta para que el usuario la cierre. No hay ninguna acción humana bloqueante pendiente para esta mejora. F24/F25/4H/F26/F27 no se repitieron, F28 no se ejecutó, no push.
