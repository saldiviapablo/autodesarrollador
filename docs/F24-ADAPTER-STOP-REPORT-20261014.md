# Parada después del cierre F23 — 2026-10-14

F23 PASS. Fix del transporte Reviewer PASS, commit `d7ee4779bde80ad1d3ede43294c4d5855bea1fac`. Macrofase 8 FAIL / MANDATORY_TEST_FAILED por intento F24 no ejecutado correctamente. F25, 4H, F26 y regression gate final NOT_RUN / PREVIOUS_GATE_FAILED. F27/F28 no iniciadas. READY FOR REAL PILOT NO.

F24 preparó un sandbox nuevo, registró un test inicialmente fallido y aprobó una sola vez su contrato. El adaptador Python pasó una expresión `/c` ya entrecomillada como elemento de una lista para `cmd.exe`. `subprocess.list2cmdline` volvió a escapar las comillas con la gramática CRT, incompatible con la gramática de cmd.exe. El launcher no llegó a ejecutarse: stderr «No se ha encontrado la ruta de acceso de la red», exit 1. No hubo Runner, Hermes, Worker, consultas web ni ChatGPT de F24. No se atribuye este fallo del adaptador a una regresión demostrada del producto.

Diagnóstico determinista PASS: un launcher ficticio en una ruta con espacios reproduce exit 1 con la lista y exit 0 usando la expresión `/c` nativa sin el segundo escape. El argumento con espacios llega íntegro. Sólo se ejecutó ese diagnóstico; F24 real no se repitió después del nuevo gate fallido. El candidato corregido se conserva como evidencia experimental, sin certificación E2E ni instalación productiva.

Duración del intento inválido: 5,53 segundos; no satisface la prueba de 15–45 minutos. Lectura ambiental única: RAM libre 15543,82 MiB, pagefile usado 2,116 GiB, VRAM global 7195 MiB. No son mediciones de una corrida local de inferencia. La continuación real F23 sí registró mínimo de RAM 279,45 MiB, pagefile máximo 2,398 GiB y VRAM global máxima 7092 MiB; el mínimo histórico anterior de 68,64 MiB permanece intacto. No se cambió modelo, contexto ni paralelismo.

Cleanup final PASS: el metadata lock del inicializador ya terminado se retiró únicamente tras comprobar run_id/proyecto/ownership y adquirir el mutex físico. Cero procesos propios supervivientes, ningún listener 8080/9119, mutex del run liberado e Inference Lock FREE. STATE FAILED, checkpoint y reporte guardados mediante APIs existentes. Chrome dedicado preexistente permanece abierto. F23 y su consulta completada permanecen intactas: cero nuevos envíos.

Evidencia: `evidence/phase-24-20261014/`. La suite F24 integral no está certificada. No se ejecutaron fases posteriores después de este gate. Dependencias nuevas: ninguna. No se alteraron Hermes v0.21.6, hooks, security.yaml, RUN-CONTRACT, hashes aprobados ni guardrails. NO PUSH.
