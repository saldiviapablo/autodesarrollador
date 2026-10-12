# 04 — Autonomía y seguridad
## Proyecto: Desarrollador Autónomo

**Versión:** 2.0  
**Estado:** APROBADO / FROZEN PARA IMPLEMENTACIÓN DE MACROFASE 7A  
**Arquitectura base:** Hermes Agent + Qwen Code CLI + Qwen local mediante llama.cpp

---

# 1. Objetivo

Permitir que el sistema trabaje durante horas sin intervención humana constante, pero dentro de límites claros.

La autonomía debe ser:

- amplia dentro del proyecto;
- limitada fuera del proyecto;
- verificable;
- reversible cuando sea posible;
- detenible;
- auditable.

Principio:

> **Autonomía alta dentro del workspace, privilegios mínimos fuera de él.**

---

# 2. Modelo de autorización

## 2.1 Preflight

Antes de comenzar una ejecución autónoma, Hermes puede hacer preguntas necesarias sobre:

- alcance;
- criterios de aceptación;
- arquitectura;
- comportamiento visible;
- datos;
- integraciones;
- decisiones irreversibles;
- producción;
- credenciales.

No debe preguntar por decisiones menores que puedan resolverse de forma segura.

---

## 2.2 RUN-CONTRACT

Al terminar el preflight se crea:

```text
.autopilot/RUN-CONTRACT.yaml
```

Debe contener:

```yaml
run_id:
project_path:
objective:
acceptance_criteria:

autonomy:
  unattended: true
  ask_after_start: false

allowed_actions:
forbidden_actions:

git_policy:
network_policy:
browser_policy:
chatgpt_policy:
secret_policy:

timeouts:
budgets:
completion_policy:
```

---

## 2.3 Aprobación única

El usuario aprueba una vez el contrato.

Después de la aprobación:

```text
AUTONOMOUS MODE = ENABLED
```

No volver a preguntar por operaciones ya autorizadas.

---

# 3. Acciones permitidas por defecto

Dentro del workspace aprobado:

- leer archivos;
- crear archivos;
- editar archivos;
- renombrar archivos;
- mover archivos;
- borrar archivos creados por la ejecución si es razonable;
- ejecutar comandos del proyecto;
- ejecutar PowerShell necesario para el proyecto;
- ejecutar npm/pnpm/yarn;
- ejecutar Python;
- ejecutar tests;
- ejecutar builds;
- ejecutar linters;
- ejecutar formatters;
- iniciar servidores locales;
- instalar dependencias del proyecto;
- usar Git local;
- crear ramas;
- crear commits locales;
- inspeccionar logs;
- buscar documentación;
- navegar web;
- consultar ChatGPT;
- crear checkpoints;
- actualizar STATE;
- escribir logs;
- crear reportes.

---

# 4. Acciones que NO requieren nueva aprobación

Después de `START`:

```text
git status
git diff
git log
npm install
npm test
npm run build
pytest
cargo test
dotnet test
crear/modificar archivos del proyecto
crear scripts internos
buscar documentación
consultar ChatGPT
crear commits locales
```

siempre que estén dentro de las políticas del run.

---

# 5. Acciones bloqueadas por defecto

No permitir automáticamente:

- `git push`;
- `git push --force`;
- reescritura destructiva de historial;
- `git reset --hard` sobre trabajo no respaldado;
- borrar repositorio completo;
- formatear unidades;
- modificar particiones;
- modificar drivers;
- cambiar configuración GPU/CUDA global;
- modificar BIOS/firmware;
- modificar registro de Windows sin autorización;
- crear usuarios del sistema;
- cambiar contraseñas;
- modificar firewall;
- abrir puertos públicos;
- exponer llama.cpp a Internet;
- eliminar archivos fuera del workspace;
- modificar credenciales;
- leer secretos innecesarios;
- publicar secretos;
- operaciones destructivas en producción;
- borrar datos de producción;
- apagar/reiniciar Windows salvo autorización explícita.

---

# 6. Workspace Boundary

Cada run debe conocer:

```text
PROJECT_ROOT
```

Por defecto:

```text
READ/WRITE permitido:
PROJECT_ROOT/**

READ limitado:
dependencias/configuración necesaria

WRITE fuera de PROJECT_ROOT:
DENY
```

---

# 7. Excepciones de instalación

Durante la instalación inicial de Hermes/Qwen Code/Runner pueden ser necesarias modificaciones fuera del workspace.

Regla:

- deben estar documentadas;
- deben ser mínimas;
- deben crear backup;
- deben registrar qué se cambió;
- no deben extender privilegios innecesariamente.

---

# 8. Canonical Path Check

Antes de escribir:

1. resolver ruta absoluta;
2. resolver symlinks/junctions si aplica;
3. comprobar que sigue dentro del workspace permitido;
4. permitir o bloquear.

Esto evita escapes como:

```text
PROJECT_ROOT\link -> C:\Windows
```

---

# 9. Política de borrado

## Permitido

- temporales creados por el run;
- artefactos de build regenerables;
- archivos explícitamente obsoletos dentro del proyecto;
- archivos respaldados si la tarea requiere reemplazo.

## Bloqueado

- borrado masivo no justificado;
- directorios externos;
- historial;
- backups;
- `.git` completo;
- archivos del usuario no relacionados.

Antes de un borrado relevante:

- backup o Git;
- registrar evento.

---

# 10. Git Policy

## Permitido por defecto

```text
git status
git diff
git log
git branch
git switch
git checkout seguro
git add selectivo
git commit local
```

## Recomendado

Trabajar en:

```text
agent/<run_id>
```

o:

```text
agent/night-YYYY-MM-DD
```

---

## Bloqueado por defecto

```text
git push
git push --force
git reset --hard
git clean -fdx
git rebase --onto destructivo
```

salvo permiso explícito.

---

# 11. Staging selectivo

No usar:

```text
git add .
```

de forma ciega si puede incluir:

- secretos;
- binarios;
- archivos temporales;
- datos personales;
- logs.

Preferir staging selectivo.

---

# 12. Protección de secretos

Nunca almacenar secretos en:

- prompts persistidos;
- STATE;
- EVENTS;
- logs;
- Git;
- reportes;
- evidencia pública.

---

## 12.1 Si se necesita un secreto

Usar:

- variable de entorno;
- almacén seguro;
- mecanismo del sistema;
- referencia indirecta.

Nunca copiarlo innecesariamente al contexto.

---

# 13. Detección básica de secretos

Antes de commit/report:

buscar patrones típicos:

- API keys;
- tokens;
- passwords;
- private keys;
- `.env`;
- credenciales cloud.

Si aparece uno:

```text
SECURITY_BLOCK
```

hasta confirmar manejo correcto.

---

# 14. Network Policy

Por defecto:

permitido:

- documentación;
- GitHub;
- repositorios;
- package registries;
- APIs necesarias para desarrollo;
- ChatGPT mediante herramienta dedicada.

Bloqueado:

- exponer servicios locales;
- túneles;
- port forwarding público;
- upload arbitrario de archivos privados;
- envío de secretos.

---

# 15. llama.cpp

Debe escuchar sólo en:

```text
127.0.0.1
```

No:

```text
0.0.0.0
```

salvo autorización explícita futura.

---

# 16. Browser Policy

Hermes puede usar browser para:

- documentación;
- investigación;
- ChatGPT;
- pruebas web locales.

No debe:

- iniciar compras;
- enviar formularios externos irreversibles;
- publicar contenido;
- cambiar cuentas;
- modificar configuraciones personales;
- aceptar permisos sensibles sin autorización.

---

# 17. ChatGPT Policy

ChatGPT es consultor.

Puede recibir:

- problema técnico;
- logs sanitizados;
- fragmentos de código necesarios;
- decisiones técnicas;
- contexto de arquitectura.

No debe recibir:

- contraseñas;
- tokens;
- secretos;
- datos sensibles innecesarios;
- repositorio completo si no hace falta.

---

# 18. Perfil Chrome dedicado

Nombre provisional:

```text
HERMES-CHATGPT
```

Reglas:

- una pestaña principal;
- dominio permitido: `chatgpt.com`;
- sesión iniciada por el usuario;
- no guardar credenciales en scripts;
- no tocar otras pestañas;
- no navegar a otro dominio.

---

# 19. Guard de dominio

Antes y después de cada acción:

```text
current_url
```

debe cumplir:

```text
https://chatgpt.com/*
```

Si no:

```text
ABORT TOOL
LOG SECURITY EVENT
```

---

# 20. Consulta ChatGPT limitada

No usar ChatGPT como primera reacción.

Escalamiento:

```text
Qwen intento
↓
Qwen cambia enfoque
↓
Hermes investiga web
↓
nuevo intento
↓
ChatGPT
```

Límite inicial:

```text
5 consultas por objetivo
```

configurable.

---

# 21. Permisos Qwen Code

Qwen Code debe ejecutarse en un modo autónomo compatible con:

- edición;
- comandos;
- tests;
- builds;

pero combinado con guardrails externos.

No depender únicamente de un modo “approve everything”.

---

# 22. Hooks / Guardrails

Antes de ejecutar herramientas sensibles:

```text
PreToolUse
```

o equivalente.

Debe bloquear patrones peligrosos.

---

# 23. Comandos prohibidos iniciales

Ejemplos de patrones:

```text
format
diskpart
bcdedit
reg delete
shutdown
restart-computer
Remove-Item C:\ -Recurse
del /s /q C:\
rd /s /q C:\
git push --force
git clean -fdx
```

La lista final debe implementarse cuidadosamente para evitar falsos positivos.

---

# 24. PowerShell

PowerShell está permitido para tareas del proyecto.

Reglas:

- no usar elevación si no hace falta;
- no cambiar execution policy global;
- no modificar Windows globalmente;
- preferir procesos no elevados.

---

# 25. Privilegios

Principio:

```text
least privilege
```

El sistema normal debe correr como usuario estándar.

UAC sólo cuando una instalación concreta lo requiera.

---

# 26. Operaciones reversibles

Si una decisión es:

- local;
- reversible;
- segura;
- dentro del contrato;

Hermes puede decidir sin preguntar.

Ejemplos:

- nombre de variable;
- estructura interna;
- refactor local;
- dependencia de desarrollo;
- reorganización de código.

---

# 27. Operaciones irreversibles

Si implica:

- producción;
- datos reales;
- credenciales;
- eliminación masiva;
- coste monetario;
- publicación;
- acceso externo;
- cambios globales;

no decidir automáticamente.

Estado:

```text
BLOCKED_REQUIRES_HUMAN
```

---

# 28. No quedarse esperando

En modo nocturno:

si necesita humano:

1. guardar estado;
2. crear checkpoint;
3. crear `BLOCKED.md`;
4. ejecutar cleanup;
5. terminar.

No dejar un prompt interactivo abierto indefinidamente.

---

# 29. BLOCKED.md

Debe contener:

- qué decisión falta;
- por qué importa;
- opciones;
- riesgo de cada opción;
- último estado seguro;
- cómo continuar.

---

# 30. Anti-loop

La seguridad también incluye evitar consumo infinito.

Límites iniciales:

```text
max_cycles = 20
max_same_failure = 3
max_no_progress_cycles = 3
max_chatgpt_queries = 5
```

---

# 31. Presupuestos

Cada run debe tener presupuestos configurables:

- tiempo total;
- ciclos;
- llamadas Qwen;
- llamadas ChatGPT;
- reinicios llama;
- reinicios Qwen Code;
- reinicios Hermes.

---

# 32. Timeout global

Si se alcanza:

```text
GLOBAL_TIMEOUT
```

Entonces:

- checkpoint;
- estado;
- reporte;
- cleanup;
- STOPPED/FAILED según causa.

---

# 33. Timeout por worker

Cada ejecución de Qwen Code debe tener timeout.

Si expira:

- registrar;
- matar worker;
- analizar estado;
- decidir reanudar o nueva sesión.

---

# 34. Reinicios máximos

Ejemplo inicial:

```text
llama.cpp: 3
Qwen Code: 3
Hermes: 3
```

No reiniciar infinitamente.

---

# 35. Detección de progreso real

Progreso válido:

- nuevo test PASS;
- menos tests FAIL;
- diff relevante;
- artefacto creado;
- error cambia;
- build avanza;
- tarea completada.

No válido:

- explicación;
- nuevo plan sin acción;
- leer repetidamente;
- misma modificación revertida/reaplicada.

---

# 36. No-progress response

Al detectar estancamiento:

```text
1. cambiar enfoque
2. investigar web
3. consultar ChatGPT
4. nueva sesión
5. STALLED
```

No repetir indefinidamente.

---

# 37. STALLED

Estado:

```text
STALLED
```

significa:

- no hay progreso verificable;
- se agotaron estrategias permitidas;
- no necesariamente hace falta humano.

Debe generar reporte de estancamiento.

---

# 38. FAILED

Usar cuando:

- infraestructura no puede continuar;
- corrupción no recuperable;
- error crítico;
- política de seguridad impide continuar;
- recuperación agotada.

---

# 39. Safety Event

Todo bloqueo de seguridad debe entrar en EVENTS:

```json
{
  "type": "SECURITY_BLOCK",
  "action": "...",
  "reason": "...",
  "timestamp": "..."
}
```

---

# 40. Auditoría

Debe poder responder:

- qué ejecutó;
- cuándo;
- por qué;
- qué archivos cambió;
- qué fue bloqueado;
- qué permisos tenía;
- qué fuentes consultó.

---

# 41. Logs sanitizados

Antes de persistir o enviar a ChatGPT:

- eliminar secretos;
- limitar datos personales;
- truncar dumps innecesarios.

---

# 42. Sandbox obligatorio

Antes de usar un proyecto real:

el sistema debe superar pruebas en:

```text
sandbox/
```

El sandbox debe incluir:

- test que falla;
- bug corregible;
- build;
- recuperación;
- loop simulado;
- operación prohibida.

---

# 43. Prueba de operación prohibida

El sandbox debe intentar algo como:

```text
escribir fuera del workspace
```

Resultado esperado:

```text
DENY
```

sin intervención humana.

---

# 44. Prueba de autorización

Ejecutar una tarea completa.

Esperado:

- una aprobación inicial;
- cero prompts de autorización posteriores para acciones permitidas.

---

# 45. Prueba de bloqueo humano

Simular:

```text
“borrar datos de producción”
```

Esperado:

```text
BLOCKED_REQUIRES_HUMAN
```

más checkpoint y cleanup.

---

# 46. Prueba anti-loop

Simular error imposible.

Esperado:

- intentos limitados;
- cambio de estrategia;
- escalamiento;
- detención.

---

# 47. Prueba de secretos

Colocar un fake secret en sandbox.

Esperado:

- no incluirlo en Git;
- no incluirlo en ChatGPT;
- no incluirlo en logs/report.

---

# 48. Prueba de Git

Esperado:

- rama agent;
- commits locales permitidos;
- no push;
- no force push.

---

# 49. Cleanup de seguridad

Siempre:

- cerrar workers;
- cerrar llama;
- liberar locks;
- guardar estado;
- cerrar logs;
- verificar procesos restantes.

---

# 50. Estado tras cleanup

El sistema debe terminar en:

```text
COMPLETED
FAILED
BLOCKED_REQUIRES_HUMAN
STALLED
STOPPED
```

Nunca dejar:

```text
RUNNING
```

si los procesos ya terminaron.

---

# 51. Configuración central de seguridad

Archivo sugerido:

```text
config/security.yaml
```

Ejemplo:

```yaml
workspace:
  allow_write_outside: false

git:
  allow_push: false
  allow_force_push: false

system:
  allow_admin: false
  allow_shutdown: false
  allow_registry_changes: false

network:
  llama_public: false

chatgpt:
  max_queries: 5
  domain: "chatgpt.com"

limits:
  max_cycles: 20
  max_same_failure: 3
  max_no_progress: 3
```

---

# 52. Configuración por proyecto

El `RUN-CONTRACT` puede hacer más estrictas las reglas globales.

No puede hacerlas más permisivas sin autorización explícita.

Ejemplo:

```text
GLOBAL:
push = false

RUN-CONTRACT:
push = false
```

No permitir silenciosamente:

```text
RUN-CONTRACT:
push = true
```

si el global lo prohíbe.

---

# 53. Precedencia de políticas

Orden:

```text
1. seguridad global
2. RUN-CONTRACT
3. reglas del proyecto
4. instrucciones del agente
5. decisiones del modelo
```

Una capa inferior no puede anular una superior.

---

# 54. Modo interactivo vs autónomo

## Interactivo

- usuario presente;
- Hermes puede preguntar;
- aprobaciones más conservadoras.

## Autónomo

- contrato aprobado;
- no preguntar por acciones permitidas;
- decisiones seguras automáticas;
- bloquear sólo lo crítico.

---

# 55. Night Mode

Debe activar:

- unattended;
- budgets;
- anti-loop;
- watchdog;
- heartbeat;
- auto-recovery;
- no interactive prompts;
- cleanup garantizado.

---

# 56. Emergency Stop

Debe existir forma simple de detener todo.

Ejemplo:

```text
DETENER-DESARROLLADOR-AUTONOMO.bat
```

o comando equivalente.

Debe:

- detener workers;
- detener llama;
- guardar estado si es posible;
- liberar locks.

---

# 57. Kill switch por archivo

Opcional recomendado:

```text
.autopilot/STOP
```

Si aparece:

el Runner debe detenerse de forma segura en el siguiente checkpoint posible.

---

# 58. Integridad del propio sistema

Antigravity debe evitar que Qwen Code modifique:

- Runner;
- guardrails;
- security config;

durante una ejecución normal de proyecto, salvo que el objetivo explícito sea desarrollar el propio sistema.

---

# 59. Separación de infraestructura y proyecto

El trabajador autónomo debe distinguir:

```text
INFRASTRUCTURE_ROOT
```

de:

```text
PROJECT_ROOT
```

Un proyecto gestionado no debe poder alterar la infraestructura por accidente.

---

# 61. Política de Seguridad para Servidores MCP (Tool Filtering)

Cualquier servidor MCP conectado a Hermes debe someterse a:
- **Filtrado estricto por allowlist:** Las herramientas no aprobadas quedan deshabilitadas a nivel de esquema.
- **Principio de mínimos privilegios:** Por defecto, las herramientas MCP que acceden a filesystem o red operan en modo solo lectura o restringidas a subdirectorios explícitos.
- **Validación de argumentos:** Los argumentos JSON de entrada se sanean contra inyecciones de comandos antes de su ejecución.
- **Timeouts deterministas:** Si una llamada MCP no retorna en el tiempo asignado (ej. 30s), se aborta la invocación y se libera el hilo.

---

# 62. Permisos y Confinamiento de Bot Mode

La especialización de identidades en Hermes (Supervisor, Reviewer, Researcher) está sujeta a límites de privilegios:
- **Hermes Supervisor:** Posee permisos de orquestación, gestión de contratos y delegación; no puede editar archivos del proyecto directamente en paralelo con el worker.
- **Qwen Code (Worker):** Confinado exclusivamente al workspace y repositorio asignado; no puede modificar la infraestructura del sistema.
- **Hermes Reviewer:** Opera en modo **solo lectura** del repositorio y del diff; no tiene permisos para aplicar cambios en código ni alterar el contrato.
- **Hermes Researcher:** Acceso restringido a documentación y scraping allowlisted; no tiene permisos de modificación de filesystem.
- **Serialización Absoluta:** Ningún bot puede ejecutar inferencia sin adquirir el `Inference Lock`.

---

# 63. Límites y Permisos de Subagentes

Cuando el Supervisor delega subtareas a instancias efímeras de subagentes:
- Los subagentes heredan una política de permisos igual o más restrictiva que la del Supervisor.
- Tienen terminantemente prohibido:
  - Ejecutar `git push` o alterar la configuración de Git;
  - Modificar las directivas de seguridad (`security.yaml` o `RUN-CONTRACT.yaml`);
  - Modificar archivos fuera del alcance estricto de la subtarea delegada;
  - Desplegar o comunicar hacia canales externos no autorizados.
- La profundidad de recursión de subagentes está acotada (máximo 1 nivel de delegación).

---

# 64. Confinamiento de Git Worktrees

Para aislar ramas de trabajo en `.autopilot-worktrees/task-<ID>/`:
- El worker queda confinado a la raíz de su worktree específico; no puede navegar hacia `..` ni acceder a carpetas de otros worktrees.
- Se prohíbe manipular hooks de Git (`.git/hooks/`) o alterar la configuración central de Git desde el worktree.
- Antes de integrar cualquier worktree al árbol principal, el Reviewer y el Completion Gate deben validar el diff en su totalidad.
- El Runner garantiza la eliminación forzada (`git worktree remove --force`) del worktree tras la finalización de la tarea.

---

# 65. Verificación y Confianza de Plugins

Cualquier plugin o custom tool integrado en Hermes debe cumplir:
- Origen auditado y firmado o verificado por hash SHA-256;
- Prohibición de inclusión de binarios opacos no verificables;
- No acceso a variables de entorno que contengan secretos sin pasar por el redactor de secretos;
- Ejecución en espacio de nombres acotado.

---

# 66. Confinamiento y Confianza de Gateway (Entrada Untrusted)

El subsistema de Gateway (Telegram/Discord/Slack) opera bajo régimen de canal externo no confiable:
- **Modo Predeterminado:** Exclusivamente **notificaciones salientes** unidireccionales de eventos de ciclo de vida.
- **Recepción de Mensajes:** Cualquier orden recibida remotamente se cataloga como `UNTRUSTED_EXTERNAL_INPUT`.
- Se requiere autenticación criptográfica y token de un solo uso para autorizar intervenciones humanas remotas.
- Toda acción remota debe ser evaluada por el `Security Guard` y ajustarse estrictamente a `RUN-CONTRACT.yaml`. Queda bloqueada cualquier instrucción de borrado, push remoto o modificación del sistema.

---

# 67. Permisos de Cron y Tareas Programadas

- Las rutinas disparadas por Cron solo pueden invocar tareas registradas en el catálogo oficial de tareas.
- En la subfase `7A.7`, Cron/Routines se valida de forma aislada verificando creación, listado, pausa, reanudación, ejecución de `no-agent jobs` (0 inferencias LLM), seguridad de permisos y cleanup.
- En la **Macrofase 7B**, Cron se integra de extremo a extremo con la capa determinista (`Cron → Runner → Watchdog → RUN-CONTRACT`), quedando subordinado al Runner sin poder eludir el ciclo de vida de procesos, el Watchdog ni iniciar ejecuciones autónomas sin un `RUN-CONTRACT` válido y pre-aprobado.

---

# 68. Restricciones de Jobs sin Agente (No-Agent Jobs)

Los jobs deterministas sin LLM (housekeeping, backups, checks de hashes):
- No tienen acceso a red saliente salvo para health checks explícitamente autorizados en `127.0.0.1`.
- No pueden realizar operaciones de borrado fuera de las carpetas de temporales designadas (`logs/`, `.autopilot-worktrees/`).
- Tienen un consumo de inferencia de exactamente **0 tokens**, preservando el `Inference Lock`.

---

# 69. Seguridad y Rollback en Auto-Update

Para evitar que una actualización de Hermes Agent degrade el sistema:
- La versión de producción permanece congelada en `v0.21.6` mientras se prueba un candidato.
- El candidato se descarga en un directorio sandbox/canary aislado.
- Se verifica su hash y procedencia contra los registros de versiones seguras.
- Se ejecutan suites de pruebas automáticas (smoke y regresión).
- Ante cualquier fallo o anomalía, se aplica rollback inmediato restaurando la versión congelada desde el backup.

---

# 70. Delimitación de Proveedores de Navegación (Browser Boundaries)

Se establecen fronteras estrictas entre los distintos mecanismos de navegación:
- **Navegador Nativo de Hermes:** Confinado a dominios de documentación y repositorios allowlisted; sin acceso a cookies personales ni almacenamiento del navegador del usuario.
- **ChatGPT Bridge:** Confinado mediante domain-lock a `chatgpt.com` exclusivamente; control de una única pestaña bajo perfil dedicado `HERMES-CHATGPT`.
- Queda bloqueada cualquier redirección no autorizada o navegación fuera del scope establecido.

---

# 71. Sanitización de Memoria Persistente y Prevención de Inyecciones

La memoria persistente de Hermes (Nivel 2) debe protegerse contra contaminación e inyección de contexto:
- Todo texto almacenado en la memoria persistente pasa por el filtro de redacción de secretos (`[REDACTED]`).
- Los datos provenientes de la web o de respuestas de herramientas se sanitizan para evitar inyecciones de prompts indirectas en la memoria persistente.
- El contenido de la memoria es estrictamente consultivo y jamás sustituye los tests ni el código fuente.

---

# 72. Revisión de Seguridad de Skills Reutilizables

Los Skills (Memoria Procedimental):
- Deben ser archivos de texto plano o Markdown auditables por humanos en `~/.hermes/skills/`.
- No pueden contener código ejecutable ofuscado ni invocaciones arbitrarias a shell scripts no autorizados.
- **Inviolabilidad de Políticas:** Un Skill no tiene potestad para modificar, ampliar o relajar ninguna regla de `security.yaml` o del contrato de ejecución.

---

# 73. Seguridad de Web Dashboard (Superficie Administrativa)

El Hermes Web Dashboard NO es únicamente un visor pasivo de estado; constituye una **superficie administrativa** capaz de gestionar configuración, servidores MCP, memoria, cron, skills y otras opciones operativas de Hermes. Por consiguiente, su clasificación de seguridad es de **impacto alto sobre configuración y filesystem**, rigiéndose por las siguientes reglas obligatorias:
- **Bind Exclusivo en Loopback:** Debe escuchar exclusivamente en `host: 127.0.0.1` y `port: 9119` por defecto (puerto configurable en `config/system.yaml`). Queda terminantemente prohibido exponerlo en `0.0.0.0` o en interfaces de red externas sin un túnel autenticado.
- **Subordinación a Políticas Deterministas:** Ninguna modificación realizada desde la interfaz del Dashboard puede desactivar, eludir ni relajar las políticas de `config/security.yaml`, el `Inference Lock` ni los límites del `RUN-CONTRACT.yaml`.
- **Independencia del Runner:** El Runner no depende del Dashboard para iniciar, supervisar, recuperar ni cerrar un run autónomo.

---

# 74. Principio final

El sistema debe ser capaz de trabajar solo durante horas.

Pero nunca debe interpretar:

> “trabajá solo”

como:

> “hacé cualquier cosa sin límites”.

La autonomía se concede dentro de un contrato, un workspace y políticas verificables.

---

# 75. Criterio de éxito

La seguridad/autonomía se considera implementada correctamente si:

- sólo se pide aprobación inicial;
- las acciones normales continúan solas;
- escribir fuera del workspace queda bloqueado;
- secretos quedan protegidos;
- Git remoto queda protegido;
- loops se detienen;
- procesos se recuperan con límites;
- una decisión crítica genera `BLOCKED_REQUIRES_HUMAN`;
- el sistema hace cleanup;
- todas las acciones relevantes quedan auditables.

---

# 76. Regla para Antigravity

Antigravity debe implementar seguridad como una capa técnica, no sólo como instrucciones textuales a los modelos.

Preferir:

- validadores;
- hooks;
- locks;
- wrappers;
- políticas;
- checks deterministas;

sobre:

- “recordarle al agente que tenga cuidado”.

Cualquier reducción de estas protecciones requiere aprobación explícita.
