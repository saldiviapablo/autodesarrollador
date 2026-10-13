# Informe final de Macrofase 7B

MACROFASE 7B = PASS. READY FOR MACROFASE 8 = YES.
Macrofase 8 permanece PENDING; no se inició la prueba nocturna ni F23–F28.
Base comprobada: 8ec42f4, Macrofases 1–6 y 7A PASS.
Rama: agent/run-20261013-7b. Sin push ni actualizaciones de componentes.

| Fase | Estado | Commit local |
|---|---|---|
| F17 Runner + Cron | PASS | 7ae2b2d |
| F18 Watchdog | PASS | f316643 |
| F19 Launchers | PASS | a973c73 |
| F20 Completion Gate | PASS | 08e0983 |
| F21 Reportes | PASS | 97fa3eb |
| F22 Cleanup | PASS | c1f8496 |

Preflight/plan: e611e12. Corrección posterior de metadata prestart y UTF-8: 411102e.
El commit final de cierre contiene este informe y el estado canónico; su hash y
Git status real después del commit se guardan en runtime/7b-final-git.json.

## Pruebas y evidencia

- F17: T-RUN-001–009 PASS; aprobación/digest, rutas, exclusión de runs,
  lifecycle real, recovery desde disco y Cron nativo → Runner → Watchdog → contrato.
- F18: T-WATCH-001–005 PASS. Se mataron procesos reales llama, Hermes y
  Qwen Code; recuperación acotada y presupuestos persistidos. Stale heartbeat
  probado suspendiendo el padre; no restart infinito.
- F19: BAT reales en rutas con espacios, STOP controlado y bloqueo desatendido
  sin aprobación. Guardado de estado/checkpoint y salida sin esperar input.
- F20: T-COMP-001–009 PASS, doce falsos positivos rechazados. Tests, build/linter
  cuando corresponden, marcadores, criterios, artefactos, hashes, diff,
  pending, roles y STATE verificables. Un probe jamás alcanza COMPLETED.
- F21: reportes humanos y JSON con todos los campos; cinco terminales,
  sanitización, timeout, STALLED, gate rechazado y BLOCKED real.
- F22: T-CLEAN-001–004 PASS. Diez casos de lifecycle/recuperación y obstrucciones
  de checkpoint/reporte. Guardian independiente finaliza un padre muerto y sale;
  el finally libera mutex incluso si falla la persistencia. Reloj aprobado
  conservado durante recovery. Adopción real compatible con modelo preservado.

Evidencia por fase: evidence/phase-17/ a evidence/phase-22/.
E2E final y anterior conservado: evidence/e2e-7b/.
Regression e integridad: evidence/regression-7b-final/.

## E2E final y Completion Gate

Run real: run-20261013-170634; duración 207.92 s.
Fallo controlado: Hermes Supervisor PID 29740, con identidad de creación registrada. Un solo restart; supervisor → Qwen Code → tests reales → Reviewer independiente → gate → reportes → cleanup.
Todos los 19 checks del gate PASS; resultado COMPLETED. RAM disponible mínima observada 0.38 GiB; working set llama máximo 19.79 GiB. VRAM y muestras completas en native.json. Sin OOM ni crash no controlado.

## Regression, integridad y cleanup

134 comprobaciones finales PASS, con auditoría de los 38 tests obligatorios de 7A. Smokes nuevos de estado, seguridad, checkpoints, mutex cross-process, hook/sanitización, MCP health/allowlist, plugin, domain lock y Cron PASS. No se repitieron las suites completas de 7A.1/7A.2; bridge real/UTF-8/idempotencia se conserva mediante binding SHA-256 sin cambios.

Modelo completo SHA-256 671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7.
Ejecutable llama c741d245d827a0a3d3896f5f9b0039b3bb282dc9fc9840aa7cd7d072ddd86a39.
Hermes productivo v0.21.6; checkout/commit y módulos nativos protegidos intactos.
qwen36, 127.0.0.1:8080, ctx 65536, parallel 1 e Inference Lock sin cambios.
RUN-CONTRACT, security.yaml, hooks, guardrails y hashes aprobados conservados.

Resultado global: cero procesos propios/auxiliares huérfanos, cero locks propios,
mutexes físicos libres, cero listeners 8080/9119/9222, heartbeat terminal coherente.
Ningún proceso desconocido fue matado. Modelos compatibles EXTERNAL se preservan.
Metadata antigua de fixtures reconciliada sólo bajo mutex físico, con backups;
primer diagnóstico conservado en cleanup-initial-stale-reconciliation.json.

## Problemas encontrados y corregidos

- PS5 File.Replace exigía backup no nulo; módulos PS7 heredados por el hijo
  causaban Get-FileHash ausente. Corrección local al proceso, sin tocar Windows.
- Linters ausentes se interpretaban como comando vacío; se omiten correctamente.
- Harness inicial de F18 sufrió sharing violation al leer metadata atómica:
  lectura con retry limitado, ledger previo al kill y retest real PASS.
- Quoting cmd/BAT ajustado para rutas con espacios; NameError del test F20 corregido.
- Finally reforzado contra fallos de STATE/checkpoint/reporte; fallback de reportes
  dentro de infraestructura y cleanup físico siempre ejecutado.
- Metadata del inicializador quedaba al bloquear antes de START: retiro validado
  bajo mutex y prueba específica sin workers PASS.
- Acentos de IMPLEMENTATION-STATUS alterados por encoding Windows: restauración
  desde Git y escritura UTF-8 explícita. La auditoría final verifica UTF-8.

Intentos fallidos y snapshots históricos se conservan. No se ocultaron ni
reescribieron las evidencias aprobadas. Los backups permanecen en backups/.

## Archivos y dependencias

Runner/contrato/plan/gate/reportes/guardian/cleanup nuevos, BAT simples,
registro Cron controlado, tests, documentación y evidencia. VERSIONS.lock y
config/system.yaml intactos. Sin dependencias nuevas: se reutilizaron los
runtimes y PyYAML/jsonschema, ruamel.yaml y psutil existentes.
La lista completa de archivos está en regression-7b-final/SUMMARY.json.

Git: commits locales separados; staging selectivo y diff check antes del cierre.
Verificación final CLEAN y hash del cierre en runtime/7b-final-git.json.

Los tests acreditan el funcionamiento corto y la contención de fallos. La
estabilidad durante 2 y 6–8 horas se verifica en Macrofase 8 tras nueva autorización.
