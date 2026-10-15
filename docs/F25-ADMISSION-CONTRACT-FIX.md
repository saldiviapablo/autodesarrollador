# F25 — fallo de admisión del primer fixture

Estado histórico FAIL; no prueba de duración aprobada.

La implementación nueva invocó el launcher batch con START/project/digest, pero su contrato real acepta sólo PROJECT_ROOT; recovery pertenece a run.ps1 -Action Start -Recover. F24 ATTEMPT11 ya había certificado la forma correcta. Se alineó el controlador con esa ruta sin cambiar runtime ni policies. Dos tests del contrato de invocación y regresión real A–H del adaptador cubren la corrección. También conserva la razón nativa/outputs y exporta el control tree ante fallo antes de la frontera de crash.

La corrida duró6.264s de trabajo observado, cero inferencias, cero consultas/ledger nuevos, ningún reloj nativo iniciado. El guard productivo rechazó la ruta relativa START. Cleanup de procesos/modelo/mutex/puertos pasó; metadata LOCK de Prepare quedó detectada en el resultado original FAIL, preservado. Cleanup posterior usa helper normal exact run/owner, sin editar STATE/reloj/histórico. El controlador ahora libera esa metadata únicamente cuando no hay RUN_STARTED.

Evidencia: evidence/endurance-f25-20261015-050441-b014d5/; pruebas: evidence/endurance-launcher-contract-fix-20261015/. La siguiente F25 debe empezar desde cero y completar7200s reales. No push ni dependencias nuevas.
