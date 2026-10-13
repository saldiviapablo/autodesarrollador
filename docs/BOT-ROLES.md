# 7A.5 — PASS

PHASE: Bot Mode + Subagentes. STATUS: PASS.
Supervisor nativo sin herramientas produce contrato estructurado; Qwen Code corrige
el sandbox; Reviewer independiente sin herramientas acepta diff con tests reales.
BOT-001, BOT-002 (0 ms solapamiento), BOT-003 timeout, SUBAGENT-001: PASS.
Hijo instanciado mediante SubagentLifecycleService; hereda tools vacías y el hook
aprobado rechaza git push y write_file security.yaml antes de ejecutar.
El padre espera al hijo bajo una única lease del Inference Lock. CLI finita usa
HERMES_SINGLE_QUERY_SESSION=1 para evitar wake/background que competiría con Qwen.
Profiles supervisor/reviewer/researcher restringidos al contexto proporcionado;
Researcher no certifica navegación independiente. Invocación valida hash del perfil.
Cleanup de roles y timeout: Job Object del wrapper; mutex RELEASED; cero procesos
auxiliares observados. llama-server propio sigue activo para la macrofase.
Smoke de 7A.1/2, extracción y browser: PASS. Dependencias nuevas: ninguna.
Fallos autocorregidos: Supervisor con tools delegaba cambios (reemplazado por
perfil sin tools); timestamp de evidencia reutilizada; API nativa lifecycle;
smoke apuntaba a fixture histórica eliminada (ahora fixture propia con finally).
Se conservan intentos fallidos. Capability token del handle redactado.
Backups: backups/phase-7a5-20261013-033216/. Tres perfiles nuevos fuera del
workspace necesarios para roles nativos; configuración original respaldada,
hook hash validado, copias repo iguales a configuración instalada.
RIESGO/LÍMITE: solo ejecución finita síncrona certificada. No bots persistentes
ni fan-out local concurrente. NEXT PHASE: 7A.6 tras commit y Git limpio.
