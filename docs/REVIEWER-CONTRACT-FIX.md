# Reviewer independiente — certificación nocturna 2026-10-15

Estado del fix: PASS. F24 ATTEMPT7 conserva FAIL y no fue reanudado.

La comparación obligatoria con F23 verificó el parser nativo, argv, perfil Reviewer, ausencia de resume, system/user y payload de la primera petición al modelo. F23 y F24 usan la misma ruta stdin `chat --query-file -`. El prompt completo llegó al lector nativo; Hermes sólo recorta CRLF exterior al preparar el mensaje. No se encontró pérdida de JSON, truncado de contenido, rol Worker, sesión reutilizada ni tools activadas. El wrapper genérico permanece byte a byte intacto.

El defecto observable es la frontera de instrucciones: F24 agregaba el RUN-PLAN operativo del Worker después de la instrucción inicial de auditoría y sin un contrato final que lo clasificara como datos. Esos imperativos se encontraban completos en el mensaje recibido por el modelo; F23 exitoso no los agregaba. La salida real del intento7 fue `python test_invoice.py` / `python build.py`. El estado mental del modelo no es observable: la evidencia demuestra la mezcla de instrucciones y datos, y descarta las alternativas de transporte/rol comprobables.

El nuevo contrato cita íntegramente diff, tarea, tests/build y criterios como evidencia JSON no ejecutable. Mantiene el rol auditor read-only y coloca al final la decisión exacta ACCEPTED/REJECTED. Un SHA-256 vincula el input al packet antes del dispatch y se comprueba antes de envolverlo. Se conserva la CLI nativa congelada y la serialización del Inference Lock.

El parser requiere exactamente un resultado nativo exitoso, sesión coherente y un solo objeto JSON con decision. Rechaza comandos/prosa, JSON corrupto, claves repetidas, decisiones múltiples, conflicto entre texto streamed y resultado, eventos de tools, timeout y exit no exitoso. REJECTED es una decisión válida y nunca se convierte en ACCEPTED. Completion Gate consume ese mismo parser. Una respuesta mal formada falla antes de nuevos ciclos del Worker; exit0 por sí solo no aprueba al Reviewer.

31 casos deterministas PASS; guards PS reales bloquean tools, MCP y plugins. Core prueba binding UTF-8, wrong role y fail-fast sin retry ciego. Regresiones de Completion, recovery/checkpoint/reanudación, transporte Supervisor/Reviewer, timeout, sintaxis y mutex PASS. La primera invocación de la regresión de recovery heredó un PSModulePath incompatible; se preservó ese FAIL del adaptador y se corrigió por proceso, sin cambiar Windows ni producción.

Certificación real: mismo sandbox ATTEMPT7 y mismos diff/tests/build, un solo Reviewer nativo, resultado {"decision":"ACCEPTED"}, 67.43s, archivos del target idénticos, cero Worker, cero ChatGPT. Perfil aprobado sin tools/MCP/plugins, nuevo contexto sin resume. Se conservan captura nativa de input y traza real. La comprobación adicional de coherencia streamed/result se verificó sobre esa misma traza sin otra inferencia. Cleanup PASS y mutex FREE.

También se reprodujo read-only una falta de cobertura de los criterios monetarios existentes: el resultado histórico aceptaba NaN numérico/Decimal o lanzaba InvalidOperation en vez de ValueError. Se amplió la misma función de tests inmutables, manteniendo los13 métodos y los28 gates, para incluir tipos numéricos/Decimal no finitos y None. Ningún invoice.py histórico fue editado. El Worker del nuevo F24 deberá satisfacerlos desde START; no se cambió el criterio aprobado.

Evidencia: evidence/overnight-reviewer-20261015/; ROOT-CAUSE.json, input-audit/, input-audit-wrapped/, DETERMINISTIC.json, core-regression.json, live/, completion/, recovery/, reviewer-transport/ y CERTIFIED.json. Los intentos fallidos del instrumento de auditoría se preservan y no son inferencias reales ni E2E. Sin dependencias nuevas, sin cambios de arquitectura, configuración de modelo o hashes aprobados de hooks/plugins. No push.

Próxima acción: commit local y F24 ATTEMPT8 completamente nuevo. No reinterpretar ATTEMPT7 como PASS.
