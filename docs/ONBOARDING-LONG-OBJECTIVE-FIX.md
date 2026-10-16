# Corrección del onboarding para objetivos largos

2026-10-16. **LONG_OBJECTIVE_ONBOARDING = PASS**.

## Causa comprobada

El fallo real fue PREFLIGHT_SUPERVISOR_FAILED / timeout a 180.18s. El objetivo tenía 17,520 bytes UTF-8, 17,296 caracteres y 904 líneas. El mensaje completo al Supervisor tenía 20,568 caracteres. No se autorizó Worker ni se preparó el proyecto; cleanup PASS. Evidencia conservada: `evidence/onboarding-real-timeout-20261016-001320/`.

Los timestamps del modelo muestran aproximadamente 29.86s de procesamiento de entrada y 144.87s de generación antes del corte: 6039 tokens de entrada y unos 5530 generados. No era tiempo de parseo. El wrapper esperaba la terminación para recibir el resultado completo, y la validación no podía comenzar con una salida parcial.

Los 28,051 caracteres eran el stream capturado, no un plan JSON final certificado. Su contenido parcial no quedó persistido y la sesión no guardó una respuesta final: no es posible separar retrospectivamente cuánto era razonamiento y cuánto respuesta o demostrar que ese volumen fuese una repetición literal del brief. El prompt no exigía copiarlo entero, pero sí generar pruebas en código y sólo aconsejaba concisión; no había un límite efectivo de tokens/tamaño ni formato restringido. El objetivo detallado quedó acoplado a una generación abierta y extensa.

## Corrección

El preflight usa ahora la API nativa `AIAgent` de la misma instalación congelada de Hermes para poder aplicar `max_tokens` y `response_format=json_schema` por solicitud. La CLI del Supervisor normal, Reviewer, Qwen Code y el cuerpo Start del Runner permanecen intactos. No se modificó ni actualizó Hermes instalado.

Se mantienen verificación del perfil Supervisor contra su copia aprobada, tools/plugins/MCP desactivados, hooks sin autoaceptación, hashes aprobados de hook y plugin, Job de procesos e Inference Lock productivos. El adaptador exige cero tools antes y después, endpoint/modelo locales exactos y ningún fallback; rechaza respuestas incompletas, tool calls y planes sobredimensionados.

Política central: `config/onboarding-planner.json`:

| Límite | Valor |
| --- | --- |
| Timeout Hermes del planner, antes → ahora | 180s → 180s |
| Salida máxima por solicitud | 4096 tokens |
| Pensamiento del planner transitorio | enable_thinking=false |
| Plan recibido y propuesta JSON compacta normalizada | Hasta 16,384 bytes UTF-8 cada uno |
| Fuentes de verificadores combinadas | Hasta 8192 bytes |
| Resumen / tareas / criterios | 360 caracteres / 8 / 16 |
| Model startup / wrapper GUI | 180s / 390s, sin cambios |
| Data adapter / Prepare apply | 120s / 90s, sin cambios |
| Plan del Worker/Runner | 2700s global, 300s fase, 5 ciclos, 2 reinicios, sin cambios |

El modelo produce resumen, tareas, criterios mapeados, archivos permitidos, pruebas, build, artefactos, requisitos de investigación y restricciones. El host deriva políticas fijas de Git local/no push, ChatGPT desactivado y Completion Gate nativo obligatorio. La política web refleja el campo canónico research; si el modelo sólo describe investigación requerida, se admite traducirla a ese campo cuando hay una única fuente HTTPS pública explícita en el brief. Si la selección es ambigua se bloquea. La URL efectiva se muestra antes de aprobar y los guards web siguen siendo autoritativos; no hay navegación durante el planner.

El objetivo completo se conserva byte a byte en runtime privado antes de inferir y en el binding de revisión. Después de aprobar, Prepare lo conserva también en el contrato y `.autopilot/evidence/ONBOARDING-OBJECTIVE.md`. El modelo no necesita repetirlo. Los resultados nativos quedan auditados en runtime incluso si la validación posterior rechaza la propuesta. El proceso sigue siendo readonly respecto del proyecto antes de la aprobación.

## Transporte canónico de Prepare

El gate largo descubrió otro defecto: request más binding se transportaban como Base64 en argv y superaban el límite de Windows, generando WinError 206 antes del initializer. Ahora viajan por stdin, también en las dos revalidaciones Python del child. Se conserva el formato Base64/UTF-8, se admite el BOM que PowerShell puede emitir y se rechazan cargas inválidas o mayores de 2 MiB. El modo argv anterior sigue disponible para compatibilidad; el camino productivo nuevo no lo usa para el payload.

El cambio de `runner/run.ps1` sólo afecta el transporte de Action Prepare. La auditoría compara exactamente el cuerpo Start con el baseline; compara también los AST de admission/cleanup y de execute salvo su llamada de transporte. Destinos, schemas, hashes, doble revalidación antes de escribir, initializer, cleanup y presupuestos permanecen intactos.

## Certificación real y regresión

Sólo sandboxes descartables. El brief sintético tiene 17,946 bytes, muchas secciones, UTF-8, UX/UI, stack HTML/CSS/JS, investigación web y criterios de aceptación.

Una llamada nativa real generó JSON válido de **8583 bytes** en **109.549s**; el proceso completo tardó 117.923s. La medición del modelo separa 29.960s de entrada y 73.444s de generación: 6457 tokens de entrada y 2648 de salida. El resumen tiene 116 caracteres, 4 tareas y 12 criterios; los verificadores suman 4644 bytes. La propuesta compacta normalizada mide 8654 bytes. No se usó Landing Page Prueba para certificar.

Después se reutilizó esa misma respuesta real exclusivamente en los fixtures para verificar traducción de research, metadatos y transporte sin gastar otra inferencia. Las trazas conservan cada binding y comparación: no cambiaron criterios, tests, artefactos ni budgets. Cada fixture recibió su propia aprobación simulada de integración, explícitamente marcada como tal; no representa una aprobación humana real ni un Worker iniciado. Producción conserva el binding estricto y la aprobación humana: no revalida automáticamente un plan cambiado para autorizarlo.

| Gate | Resultado |
| --- | --- |
| LONG_OBJECTIVE | PASS |
| PLANNER_WITHIN_BUDGET | PASS |
| STRUCTURED_PLAN | PASS |
| PLAN_SIZE_BOUNDED | PASS |
| ORIGINAL_OBJECTIVE_PRESERVED | PASS |
| NO_WORKER_BEFORE_APPROVAL | PASS |
| PREPARE | PASS |
| CLEANUP | PASS |
| Pruebas nuevas de planner/API/parser | 36 PASS |
| Transporte largo, validación y BOM | 4 PASS |
| Regresión onboarding | 20 PASS |
| Regresión controller | 19 PASS |
| Controles de errores/streams/QWEN previo | 22 PASS |
| Gate adversarial de junction de Prepare original | PASS, assertions intactas y cero escrituras |
| Integridad | PASS, seis componentes protegidos y 6814 evidencias históricas intactos |

Evidencia principal:

- `evidence/onboarding-long-live-final-20261016-004320/`: generación nativa real.
- `evidence/onboarding-long-final-20261016-005653/`: misma respuesta, bindings y lineage.
- `evidence/onboarding-long-final-20261016-005653-prepare/`: todos los gates largos en la versión final de transporte.
- `evidence/onboarding-compact-unit-20261016-004913/`: 36 pruebas nuevas.
- `evidence/onboarding-prepare-stdin-final-20261016-005555/`: transporte/BOM.
- `evidence/launcher-multi-project-20261016-005337/`, `evidence/onboarding-controller-final-20261016-005352/`, `evidence/launcher-failure-cert-20261016-005354/`: regresiones.
- `evidence/onboarding-prepare-boundary-final-20261016-005556/`: gate adversarial.
- `evidence/onboarding-final-integrity-20261016-005843/`: auditoría física y de invariantes.

## Fallos históricos y alcance

Se conservaron todos los intentos intermedios: JSON sin restricción mal escapado; gramática global incompatible con esta ruta de chat; YAML con un scalar sin comillas; políticas de research contradictorias; research sin su campo ejecutable; WinError 206; y rechazo de BOM antes de alcanzar el Path Guard esperado. Este último tuvo cero escrituras y sentinel intacto; se corrigió el formato de transporte y el mismo test adversarial pasó sin relajar sus assertions. No se convirtió ninguno de esos FAIL en PASS ni se borró su evidencia.

No se repitieron F24/F25/4H/F26/F27, no hubo prueba prolongada, GUI, consulta ChatGPT, cambios de ledger, push, actualización de software ni dependencia nueva. No se ejecutó F28. La inferencia mantuvo qwen36, 127.0.0.1:8080, contexto 65536 y parallel 1. Los puertos 8080/9119 y ambos mutex terminaron libres, sin procesos propios huérfanos. Los fixtures preparados quedan INITIALIZED, sin Runner ni Worker iniciados.

El brief original del fallo se recuperó mediante lectura de la sesión nativa, se verificó contra SHA e947cb1429c840ed0f618e3fde665ae23dc47f3f552635574f0e45789d861f6b y se guardó únicamente en runtime privado. Su contenido no se publica en Git; la evidencia sólo registra hash, tamaño y ruta. No se escribió en el proyecto real.

**Se puede reintentar Landing Page Prueba:** cerrar la ventana BLOCKED antigua, abrir de nuevo el mismo iniciador, seleccionar el proyecto, cargar el brief y revisar/aprobar el nuevo plan. Esto certifica el onboarding; no afirma que el proyecto del usuario ya esté implementado o vaya a completar todo su trabajo dentro de cualquier presupuesto. No hace falta otra prueba GUI para este fix.
