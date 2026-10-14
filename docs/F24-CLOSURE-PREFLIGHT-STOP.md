# F24 — cierre detenido durante preflight

PHASE: F24, continuación desde Reviewer. STATUS: FAIL / MANDATORY_TEST_FAILED.
Se detuvo antes de iniciar el Reviewer al descubrir incumplimientos del plan
aprobado. No se ejecutó Completion Gate, modelo, Worker, recovery, web ni ChatGPT.
F25 y la prueba de dos horas no se iniciaron; F27/F28 tampoco.

RUN-PLAN exige allocate con importe no negativo y pesos numéricos no negativos
cuya suma sea positiva. El código conservado del Worker contradice esos criterios:

| Comprobación de aceptación | Esperado | Resultado real |
|---|---|---|
| allocate("1.00", [0, 1]) | ["0.00", "1.00"] | ValueError: each weight must be positive, got 0 |
| allocate("-1.00", [1]) | ValueError | ["-1.00"] |

invoice.py rechaza pesos cero en la línea 67 y no valida importe negativo en
la línea 52. README exige pesos estrictamente positivos. Los tests históricos
no cubren una mezcla de peso cero/positivo ni un importe negativo de allocate.
Sus PASS y los del build siguen siendo válidos para los casos ejecutados;
no prueban toda la aceptación. Dos probes nuevos read-only corroboraron los
incumplimientos, con hashes de los archivos fuente iguales antes y después.
El proceso diagnóstico terminó normalmente y reportó ambos casos FAIL.

No se corrigió el Worker ni se modificaron tests, README, plan, contrato,
presupuesto o restart counters. STOP conforme a la instrucción ante cualquier
nueva inconsistencia. La auditoría independiente confirmó la contradicción.
El Reviewer nativo sigue NOT_RUN; una revisión auxiliar de preflight no lo sustituye.

ChatGPT permanece COMPLETED, mismo ID f24-7257c739e1fd449aae1f1f93856aef7f;
retry consumido y respuesta ya capturada. No hubo ninguna acción del bridge.
F23 PASS y las evidencias históricas se conservan intactos.

Métricas originales preservadas, verificadas contra los samples reales:

```text
REVIEWER = NOT_RUN / PREFLIGHT_BLOCKED
COMPLETION_GATE = NOT_RUN / PREFLIGHT_BLOCKED
F24 = FAIL
DURATION_TOTAL = 621.1748734 s (10m 21.17s)
RAM_MIN = 579.0703125 MiB
PAGEFILE_MAX = 2.15909958 GiB
VRAM_MAX = 4101 MiB
CLEANUP = PASS
READY_FOR_F25 = NO
```

No comenzó un nuevo segmento de ejecución nativa: continuación Reviewer = 0 s.
La espera humana no se cuenta como ejecución. Duración esperada 15–45 minutos
no alcanzada en el segmento original; no se rellenó artificialmente. Snapshot
global actual de recursos guardado aparte en resources-preflight.json, sin
sustituir ni borrar las mediciones anteriores.

Cleanup: cero procesos propios supervivientes por PID/start-time, Mutex de run
e Inference Lock FREE, sin LOCK.json ni lease del bridge, puertos 8080/9119 libres.
Chrome preexistente conservado. STATE permanece terminal BLOCKED_REQUIRES_HUMAN
mediante State Manager normal, con motivo y próxima acción actualizados a la
inconsistencia de aceptación; se conservan backups del estado y los eventos.

Git de infraestructura: commit separado de esta parada, sin push, árbol limpio
al finalizar. Sandbox: README.md e invoice.py continúan con los mismos cambios
preexistentes del Worker; no se aprueban, descartan ni ocultan mediante commit/stash.

EVIDENCE: evidence/f24-closure-preflight-blocked-20261014/.
BACKUP: backups/f24-closure-preflight-blocked-20261014/.
NEXT PHASE: ninguna. Se requiere nueva instrucción para corregir los resultados
del Worker antes de intentar Reviewer y el cierre de F24.
