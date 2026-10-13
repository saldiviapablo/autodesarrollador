# Completion Gate

El Runner ejecuta los comandos aprobados y entrega al gate los resultados del
run actual. Un código cero exige también el marcador aprobado. El gate valida
STATE con su schema, backend real, roles, revisión independiente, todos los
tests/builds/linters, correspondencia de criterios, artefactos, hashes de tests,
pendientes, fallos y diff limitado a archivos aprobados. Una simulación del
lifecycle nunca alcanza COMPLETED.

La aprobación se vuelve a comprobar al evaluar el gate. Los falsos positivos
se prueban con datos unitarios explícitamente etiquetados; la integración se
prueba por separado con Supervisor, Qwen Code y Reviewer reales.

Los fallos corregibles producen feedback para otro ciclo dentro del mismo
contrato. Supervisor sólo aconseja; el alcance aprobado siempre prevalece.
El tracker se persiste y cada ciclo guarda checkpoint. Los límites de ciclos,
fallo repetido, falta de progreso, reinicios y tiempo nunca se amplían.

Evidencia: evidence/phase-20/. No se altera RUN-CONTRACT ni sus guardrails.
