# Plan de validación Macrofase 8

Base inspeccionada: 0ab05aa, Macrofases 1–6, 7A y 7B PASS.
Orden: INSPECT → PLAN → BACKUP → ejecución → VERIFY → DOCUMENT → commit local.
Sin push, actualizaciones, reducción de contexto ni cambios de seguridad.

1. Preflight: Git/estados/evidencias, SHA-256 completo del modelo, ejecutable y
   componentes protegidos, Hermes v0.21.6, mutexes y procesos/puertos. Reconciliar
   metadata genérica obsoleta con backup; no reescribir evidencia histórica.
2. F23: empezar por pruebas adversariales del sistema real en sandbox, incluyendo
   la frontera de escrituras durante Prepare. Sólo si seguridad PASS construir
   y ejecutar un proyecto con bug, feature, tests FAIL, build, documentación,
   investigación web, consulta ChatGPT real y recuperación controlada.
3. F24: launcher y aprobación única, flujo real FAIL → diagnóstico → web →
   corrección → PASS → checkpoint → recovery → ChatGPT → continuación → gate,
   reportes y cleanup. Duración objetivo 15–45 minutos, sin relleno artificial.
4. F25: corrida de unas dos horas, múltiples tareas/ciclos, commits/checkpoints,
   web/ChatGPT y recuperación. Muestreo continuo de RAM, llama WS, VRAM,
   commit/pagefile disponible, procesos, reinicios y timeouts. Mantener el modelo
   intacto; distinguir pico transitorio y crecimiento sostenido antes de concluir.
5. Prueba intermedia 4h, si la sesión lo permite; nunca simular duración ni PASS.
6. F26: auditoría integral de capacidades y controles, casos adversariales y
   regression gate completo con evidencia nueva.

Detenerse inmediatamente ante SECURITY_REGRESSION, fallo obligatorio, cambio
de arquitectura requerido, bloqueo humano o degradación crítica de recursos.
Guardar evidencia, estado y cleanup. Cada fase requiere su gate y commit local.

F27 requiere un proyecto piloto real explícitamente aprobado. No hay selección
automática de repositorios ni autorización implícita para F28.

El dato de RAM mínima 0.38 GiB de 7B se conserva como antecedente, no como
diagnóstico de fuga ni permiso para modificar qwen36/65536/parallel1.
