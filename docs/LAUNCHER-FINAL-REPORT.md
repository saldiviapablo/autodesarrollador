# Certificación del iniciador único para múltiples proyectos

Fecha: 2026-10-15. **POST_V1_MULTI_PROJECT_LAUNCHER = PASS**.

Un solo iniciador fijo permite elegir proyectos independientes, introducir un objetivo multilínea o cargar un brief UTF-8, revisar el plan de Hermes y aprobarlo una sola vez. La preparación del proyecto y el arranque nativo ocurren después de esa aprobación. El selector no necesita copiar archivos de infraestructura dentro de cada proyecto.

## Resultado real certificado

Se usaron únicamente carpetas descartables. El usuario operó el selector, Objetivo, carga del brief, revisión/aprobación y continuación del proyecto existente. No se utilizó Computer Use, cursor automatizado ni capturas desde su prohibición.

Proyecto manual: `sandbox/launcher-live-A á ñ`. Run: `run-20261015-231741`.

| Gate | Resultado y evidencia |
| --- | --- |
| Objetivo y plan | Brief exacto con tildes, ñ, €, ° y comillas; propuesta real anterior de Hermes reutilizada sin otra inferencia y revalidada contra sus hashes |
| Aprobación | Una HUMAN_PLAN_REVIEW, a las 23:17:39, antes de Prepare y de las escrituras del proyecto |
| Prepare | Canónico, preadmisión y revalidación PASS; Git, QWEN.md y .autopilot propios |
| Continuar | Mismo run, contrato, plan, reloj y contadores; sin otra aprobación ni Prepare |
| Supervisor | Salida 0, 23:37:24; proceso 35172 registrado por Runner |
| Qwen Code | Node real 18868, identidad de nacimiento verificada, descendiente del Worker 33316 |
| Stop | API productiva active_stop; STOP_REQUESTED; ningún proceso matado por el launcher |
| Terminal | STATE y reporte ABORTED / STOP_REQUESTED; checkpoint conservado |
| Cleanup | Kernel job cerrado, procesos propios y Node verificados fuera, LOCK retirado, Inference Lock FREE, RunMutex liberado |
| Aislamiento | Sandbox B manual sin escrituras; dos proyectos preparados independientes y conservación de historial certificados por CLI |

La continuación activa duró **91.542 segundos**. El reloj original registró **1221.729 segundos**, incluida la pausa humana; no se renovó. Los límites siguieron siendo global 2700s, fase 300s, ciclos 5 y reinicios 2; los contadores permanecieron sin cambios.

El objetivo del sandbox **no está COMPLETED**: se detuvo intencionalmente para probar Start/Continue/Stop. Sus tests/build y Completion Gate no llegaron a ejecutarse. La certificación de esta mejora cubre el arranque y la parada reales; la compatibilidad del Completion Gate se conserva mediante sus pruebas dirigidas y código productivo sin cambios. No se presenta este smoke como otro E2E completo.

## Pruebas conservadas y cierre

| Prueba | Resultado | Evidencia |
| --- | --- | --- |
| Datos, seguridad y Prepare | 20/20 PASS; sólo se repitió el caso directamente afectado por el orden de aprobación | evidence/launcher-multi-project-20261015-215119/; evidence/launcher-multi-project-20261015-224049/ |
| Controller y aislamiento de aprobación | 19/19 PASS en la regresión final | evidence/launcher-final-regression-20261015-232045/ |
| Admisión, errores, QWEN existente y parser de streams | 22 controles PASS | evidence/launcher-failure-cert-20261015-224838/ |
| Regresión dirigida | 9 suites PASS: launcher, Prepare, frontera de escritura, Watchdog, Completion Gate, cleanup/recovery, Inference Lock, argumentos y domain lock | evidence/launcher-directed-20261015-224046/ |
| Path Guard y capacidades gobernadas | PASS, incluidas salidas de sandbox y cero efectos laterales | evidence/launcher-directed-pathguard-20261015-2243/ |
| Hermes planificador real de solo lectura | PASS, 163.453s; Worker y aprobación ausentes; proyecto intacto | evidence/launcher-planner-readonly-20261015-2240/ |
| Observador | 13/13 PASS y CIM UTF-8 real PASS; ningún modelo ni GUI en estas pruebas | evidence/launcher-final-certification-20261015-234100/ |
| Smoke manual/nativo | 20 comprobaciones PASS, recuperación de observación documentada | evidence/launcher-final-certification-20261015-234100/MANUAL-NATIVE-SMOKE.json |
| Integridad final | Seis SHA protegidos PASS; 6814 archivos históricos intactos; configuración congelada, puertos y mutex PASS | evidence/launcher-integrity-20261015-234108/ |

No se repitieron las fases F24, F25, 4H, F26 o F27. F28 sigue WAIVED_BY_USER / NOT_EXECUTED. No hubo otra consulta ChatGPT, cambios de ledger, nuevos paquetes, actualizaciones de Hermes, cambios de guardrails, credenciales, push ni despliegues.

## Problemas preservados y corregidos

1. El primer observador cortaba a los 240s antes del límite aprobado de una fase de 300s. Se conservó el FAIL y se corrigió exclusivamente la ventana de observación, limitada siempre por el reloj real restante. Al continuar se descartan eventos de arranques anteriores. Evidencia: evidence/launcher-manual-smoke-fail-20261015-232458/; certificación aislada de 8 controles en evidence/launcher-observer-cert-20261015-232545/.
2. El observador asumía UTF-8 mientras Windows PowerShell emitía OEM al redirigir stdout. El Supervisor ya había pasado y Qwen estaba iniciado. Se conservó ese FAIL, se obtuvo la prueba del proceso por CLI y se pidió Stop al mismo run, sin repetir la GUI o la inferencia. El observador fuerza UTF-8 y solicita Stop seguro si falla mientras observa su propio run; no detiene runs ajenos. Evidencia: evidence/launcher-observer-utf8-fail-20261015-233908/.
3. El primer chequeo del pequeño proceso auxiliar CIM confundió un handle de proceso terminado aún abierto con un superviviente. Se conservó el falso negativo; el fixture aislado se verificó con el handle del kernel señalado y exit code 0. Los 13 tests y el roundtrip ya habían pasado. Detalle: OBSERVER-CERTIFICATION.json y CIM-ROUNDTRIP.json en la evidencia final.

Todos los FAIL anteriores de implementación se conservan; no se reescribió evidencia histórica para convertirlos en PASS. El informe final reúne las verificaciones posteriores que resuelven cada gate.

## Cambios y límites

Se añadieron la interfaz Python/tkinter, el bootstrap PowerShell, los adaptadores de onboarding y aprobación, un planificador previo de solo lectura en Runner, pruebas y documentación. Se actualizaron los dos .bat fijos y los estados documentales. La arquitectura y los componentes deterministas existentes permanecen intactos. Los manifiestos de evidencia final enumeran las rutas y hashes exactos.

Dependencias nuevas: **ninguna**. Se reutilizan PowerShell, Python/tkinter, Hermes y Qwen Code instalados. El auditor reutiliza psutil ya presente en el entorno de Hermes; no se instaló ningún paquete.

La inspección inicial está acotada a 3000 archivos y 2 MB por archivo; el brief admite hasta 200 KB. Repositorios mayores pueden ser rechazados de forma visible. Los errores permanecen hasta Cerrar. La cancelación, rechazo, .txt, argumentos y otros casos de frontera se certificaron mediante pruebas deterministas; las interacciones gráficas reales fueron las descritas arriba. No se probaron proyectos reales del usuario ni una nueva prueba prolongada.

No quedan gates pendientes dentro del alcance de esta mejora. La ventana Resultado del sandbox puede permanecer abierta; cerrarla es opcional y no implica una ejecución activa. Los sandboxes, backups y evidencias se conservan.

Guía: [Cómo usar Desarrollador Autónomo](COMO-USAR-DESARROLLADOR-AUTONOMO.md). Commits de implementación y checkpoint: 48fdd61 y af76253; el commit de cierre conserva la certificación final sin push.
