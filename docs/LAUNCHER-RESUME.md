# Continuación de la mejora del iniciador

NO empezar de cero ni revertir. NO Computer Use, cursor, teclado gráfico ni capturas. NO F24/F25/4H/F26/F27/F28 ni push.

La lógica CLI está certificada. Leer el CHECKPOINT y la guía; no repetir los 20 tests originales. Sólo queda la certificación manual final y el smoke real del nuevo flujo. El usuario revisa y aprueba; jamás generar una aprobación para el run real desde un fixture.

Sandbox A: C:\Users\Pc\Documents\Proyectos Tech\Desarrollador autonomo\sandbox\launcher-live-A á ñ
Brief: C:\Users\Pc\Documents\Proyectos Tech\Desarrollador autonomo\runtime\project-launcher\manual-briefs\objetivo-A.md

El draft cacheado es exactamente la propuesta real de Hermes, revalidada contra los hashes actuales y sin ninguna aprobación. Usar Abrir .md o .txt conserva el objetivo exacto y evita repetir inferencia. El modelo sigue qwen36/127.0.0.1:8080/65536/parallel1.

Cuando se abra un diálogo, pedir acción humana clara y esperar. La prueba puede observarse por CLI con tests/observe-launcher-manual-smoke.py: no controla la GUI, no aprueba y sólo solicita STOP mediante el mecanismo productivo cuando existan Supervisor exitoso y Node Qwen CLI realmente iniciado. Guardar sus resultados de runtime como evidence al concluir. No declarar la mejora PASS hasta ese gate y la inspección manual.

Proyecto existente, .md/.txt, cancelación, aislamiento e historial ya tienen pruebas de controller/Prepare; sólo un chequeo visual manual por flujo que lo necesite. Mantener cada FAIL previo. Tras completar: consolidar informe, actualizar estado y guía, commit local y Git limpio.

Checkpoint: evidence\launcher-usability-checkpoint-20261015-225852
