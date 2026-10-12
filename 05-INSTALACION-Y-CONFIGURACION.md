# 05 — Instalación y configuración
## Proyecto: Desarrollador Autónomo

**Versión:** 2.0  
**Estado:** BORRADOR PARA APROBACIÓN  
**Arquitectura base:** Hermes Agent + Qwen Code CLI + Qwen local mediante llama.cpp

---

# 1. Objetivo

Definir cómo debe instalarse y configurarse el sistema sin romper el entorno existente.

La instalación debe:

- reutilizar componentes ya funcionales;
- evitar reinstalaciones innecesarias;
- crear backups;
- registrar versiones;
- validar cada fase;
- permitir rollback;
- no modificar drivers ni configuraciones globales sin necesidad.

---

# 2. Entorno actual conocido

Sistema operativo:

```text
Windows 11 Pro
Build 26200
64 bits
```

Hardware conocido:

```text
CPU: Ryzen 5 8400F
RAM: 32 GB DDR5
GPU: RTX 4060 Ti 8 GB
```

---

# 3. Componentes ya existentes

## 3.1 llama.cpp

Ruta conocida:

```text
C:\AI\llama.cpp\llama-server.exe
```

No reinstalar si el binario funciona correctamente.

Antes de cualquier cambio:

- comprobar versión;
- comprobar ejecución;
- registrar salida;
- hacer backup de scripts/configs relacionados si se van a modificar.

---

## 3.2 Modelo Qwen

Modelo:

```text
Qwen3.6-35B-A3B-Q4_K_M.gguf
```

Ruta observada:

```text
C:\Users\Pc\.cache\huggingface\hub\models--ggml-org--Qwen3.6-35B-A3B-GGUF\snapshots\baec3ebee244827cda0f4557eafa8b28f7545fa6\Qwen3.6-35B-A3B-Q4_K_M.gguf
```

Reglas:

- no borrar;
- no mover sin necesidad;
- no descargar nuevamente;
- no sustituir por otro modelo sin aprobación;
- no reducir contexto sin justificarlo.

---

# 4. Configuración Qwen validada

Configuración base oficial inicial:

```text
--ctx-size 65536
--parallel 1
--cpu-moe
--n-gpu-layers 99
--flash-attn on
--cache-type-k q8_0
--cache-type-v q8_0
--jinja
```

Alias:

```text
qwen36
```

Host:

```text
127.0.0.1
```

Puerto:

```text
8080
```

Endpoint:

```text
http://127.0.0.1:8080
```

---

# 5. Comando lógico de referencia

Antigravity debe generar su propia configuración/runner.

Este ejemplo es sólo referencia:

```text
C:\AI\llama.cpp\llama-server.exe
  -m <MODEL_PATH>
  --alias qwen36
  --host 127.0.0.1
  --port 8080
  --ctx-size 65536
  --parallel 1
  --cpu-moe
  --n-gpu-layers 99
  --flash-attn on
  --cache-type-k q8_0
  --cache-type-v q8_0
  --jinja
```

No copiar rutas a múltiples scripts.

Deben salir de configuración central.

---

# 6. Prueba de contexto ya realizada

Se validó Qwen progresivamente hasta 60K tokens.

Resultados:

| Tokens reales | RAM máx. usada | RAM libre mín. | llama WS máx. | VRAM máx. |
|---:|---:|---:|---:|---:|
| 8K | 21.83 GB | 9.84 GB | 12.81 GB | 4186 MB |
| 16K | 22.12 GB | 9.55 GB | 13.10 GB | 4198 MB |
| 32K | 22.37 GB | 9.30 GB | 13.38 GB | 4198 MB |
| 48K | 22.37 GB | 9.30 GB | 13.56 GB | 4198 MB |
| 60K | 22.39 GB | 9.28 GB | 13.69 GB | 4198 MB |

Conclusión:

```text
64K = configuración viable
```

bajo el entorno probado.

---

# 7. Cleanup validado

Después de detener `llama-server`:

- RAM volvió al nivel base;
- VRAM volvió al nivel base;
- no quedó proceso activo.

Esto debe conservarse como requisito del Runner.

---

# 8. Launchers legacy detectados

Configuraciones antiguas relacionadas con Goose:

```text
C:\Users\Pc\Desktop\Iniciar Qwen - Goose 16K.bat
C:\Users\Pc\Desktop\Iniciar Qwen.bat
C:\Users\Pc\Documents\Proyectos Tech\GOOSE-TEST\goose-night.ps1
```

Se observaron perfiles de:

```text
16384
32768
```

Estos archivos:

- NO representan la configuración actual oficial;
- NO limitan globalmente Qwen;
- NO deben reutilizarse como base del nuevo sistema;
- NO deben borrarse automáticamente.

---

# 9. Política legacy

Mover o archivar sólo después de validar el sistema nuevo.

Destino sugerido futuro:

```text
C:\AI\legacy-goose\
```

Pero no ejecutar este cambio sin una fase explícita de limpieza.

---

# 10. Carpeta de infraestructura

Raíz prevista:

```text
Desarrollador autonomo\
```

Antigravity trabajará desde esta carpeta.

Debe poder crear:

```text
config\
runner\
scripts\
tools\
tests\
sandbox\
backups\
docs\
logs\
```

---

# 11. Configuración central

Crear:

```text
config\system.yaml
```

Debe contener todas las rutas y parámetros principales, centralizando tanto la infraestructura base como las secciones para futuras capacidades de Hermes:

```yaml
system:
  name: "Desarrollador Autonomo"

llama:
  executable: "C:\\AI\\llama.cpp\\llama-server.exe"
  model: "C:\\Users\\Pc\\.cache\\huggingface\\hub\\models--ggml-org--Qwen3.6-35B-A3B-GGUF\\snapshots\\baec3ebee244827cda0f4557eafa8b28f7545fa6\\Qwen3.6-35B-A3B-Q4_K_M.gguf"
  alias: "qwen36"
  host: "127.0.0.1"
  port: 8080
  ctx_size: 65536
  parallel: 1
  cpu_moe: true
  n_gpu_layers: 99
  flash_attention: true
  cache_type_k: "q8_0"
  cache_type_v: "q8_0"
  jinja: true

runner:
  health_timeout_seconds: 180
  global_timeout_minutes: 480

security:
  allow_admin: false
  allow_write_outside_workspace: false

chatgpt:
  enabled: true
  allowed_domain: "chatgpt.com"
  chrome_profile_dir: "data\\browser\\HERMES-CHATGPT"
  cdp_port: 9222
  max_queries: 5

# Estructuras de configuración para capacidades nativas de Hermes (Inactivas por defecto)
mcp_servers:
  enabled: false
  servers: []

skills:
  enabled: false
  directory: "~\\.hermes\\skills"

cron:
  enabled: false
  routines: []

gateway:
  enabled: false
  notifications_only: true
  provider: ""

dashboard:
  enabled: false
  host: "127.0.0.1"
  port: 3000

worktrees:
  enabled: false
  base_dir: ".autopilot-worktrees"

document_extraction:
  enabled: false
  allow_optional_dependencies: false

auto_update:
  enabled: false
  require_canary: true
  auto_rollback: true
```

---

# 12. No duplicar configuración

No debe existir:

```text
ctx_size = 65536
```

copiado manualmente en cinco scripts distintos.

Los scripts deben leer:

```text
config\system.yaml
```

o una representación generada a partir de él.

---

# 13. Inventario previo obligatorio

Antes de instalar nada:

Antigravity debe detectar:

```text
llama.cpp
Qwen model
Git
GitHub CLI
Node.js
npm
Python
PowerShell
Chrome
Qwen Code CLI
Hermes
```

y registrar:

- encontrado/no encontrado;
- versión;
- ruta;
- estado.

---

# 14. Resultado del inventario

Guardar en:

```text
docs\INVENTORY.md
```

o:

```text
backups\preinstall\inventory.json
```

Debe incluir comandos utilizados.

---

# 15. No asumir versiones

Antigravity no debe confiar únicamente en la documentación.

Debe comprobar el entorno real.

Ejemplo:

```text
node --version
npm --version
git --version
python --version
```

y equivalentes.

---

# 16. Backups

Antes de modificar configuraciones existentes:

crear:

```text
backups\YYYYMMDD-HHMMSS\
```

Debe contener:

- archivos originales;
- ruta original;
- hash si es práctico;
- manifest.

---

# 17. Manifest de backup

Ejemplo:

```json
{
  "created_at": "...",
  "files": [
    {
      "source": "...",
      "backup": "...",
      "reason": "..."
    }
  ]
}
```

---

# 18. Instalación de Qwen Code CLI

Antigravity debe:

1. comprobar si ya está instalado;
2. comprobar versión;
3. comprobar comando;
4. comprobar documentación compatible con esa versión;
5. instalar sólo si hace falta;
6. configurar endpoint local;
7. validar inferencia;
8. validar ejecución headless;
9. validar resume/continue;
10. registrar configuración.

---

# 19. Qwen Code y modelo local

El objetivo es que Qwen Code use el servidor local.

Configuración exacta dependerá de la versión instalada.

Antigravity debe verificar la forma oficial soportada por esa versión.

No inventar flags.

---

# 20. Prueba Qwen Code mínima

Sandbox:

```text
sandbox\qwen-code-basic\
```

Debe:

1. leer archivo;
2. modificarlo;
3. ejecutar test;
4. corregir error;
5. volver a ejecutar;
6. devolver resultado.

---

# 21. Prueba headless

El Runner necesita invocar Qwen Code sin interacción manual.

Debe verificarse:

- comando no interactivo;
- entrada reproducible;
- salida capturable;
- timeout controlable;
- exit state interpretable;
- logs disponibles.

---

# 22. Resume Qwen Code

Debe probarse:

```text
continue/resume
```

según la CLI real instalada.

Guardar:

- session id;
- método;
- ubicación del historial;
- limitaciones observadas.

---

# 23. Instalación de Hermes Agent

Antigravity debe:

1. comprobar si existe;
2. comprobar versión;
3. instalar si hace falta;
4. verificar proveedor/modelo local;
5. configurar Qwen;
6. validar tools;
7. validar memoria;
8. validar sesiones;
9. validar ejecución no interactiva cuando corresponda.

---

# 24. Hermes + Qwen local

Hermes debe usar el mismo `llama-server`.

No crear un segundo modelo local salvo que más adelante exista una necesidad validada.

---

# 25. Contexto Hermes

Configuración inicial:

```text
64K
```

si la integración/provider lo soporta de acuerdo con la versión real instalada.

Si una limitación real impide 64K:

- documentarla;
- mostrar evidencia;
- no reducir silenciosamente;
- proponer alternativa.

---

# 26. Hermes tools

Validar al menos:

- shell/control permitido;
- filesystem;
- web;
- sesión/memoria;
- herramienta delegación Qwen Code;
- herramienta ChatGPT.

---

# 27. Integración Hermes → Qwen Code

No debe ser manual.

Crear wrapper/tool estructurado.

Nombre provisional:

```text
qwen_code_worker
```

o equivalente.

Entrada:

```json
{
  "project": "...",
  "task_id": "...",
  "objective": "...",
  "acceptance_criteria": [],
  "constraints": [],
  "timeout": 0
}
```

Salida:

```json
{
  "status": "...",
  "summary": "...",
  "files_changed": [],
  "tests": [],
  "build": "...",
  "errors": [],
  "evidence": []
}
```

---

# 28. Model Gateway / Lock

Debe implementarse antes de pruebas integrales.

Objetivo:

```text
parallel 1
```

Garantizar que Hermes y Qwen Code no hagan inferencia simultánea.

---

# 29. Opción de implementación

Antigravity puede elegir:

- mutex Windows;
- lockfile robusto;
- broker local;
- proxy local;
- cola.

Requisito:

- recuperación después de crash;
- timeout;
- logging.

---

# 30. llama health check

Usar:

```text
http://127.0.0.1:8080/health
```

o endpoint real soportado por la build instalada.

No considerar listo el modelo sólo porque el proceso existe.

---

# 31. Secuencia de inicio llama

```text
Start process
↓
esperar puerto
↓
health check
↓
validar modelo cargado
↓
READY
```

---

# 32. Timeout de carga

Valor inicial sugerido:

```text
180 segundos
```

configurable.

---

# 33. Detección de servidor existente

Antes de iniciar:

- comprobar puerto;
- comprobar proceso;
- identificar si pertenece al sistema;
- no matar procesos desconocidos ciegamente.

---

# 34. Ownership de procesos

El Runner debe registrar:

- PID;
- start time;
- run_id;
- command line si es posible.

Sólo debe cerrar procesos propios o explícitamente adoptados.

---

# 35. Chrome

Comprobar instalación y ruta real.

No asumir ubicación fija si puede detectarse.

---

# 36. Perfil Chrome ChatGPT

Crear perfil dedicado:

```text
HERMES-CHATGPT
```

El usuario inicia sesión manualmente una vez.

No almacenar:

- contraseña;
- cookies exportadas;
- credenciales en texto.

---

# 37. Browser automation

Antigravity debe escoger una técnica compatible y estable con Chrome instalado.

Debe permitir:

- adoptar perfil/pestaña;
- inspeccionar URL;
- escribir prompt;
- leer respuesta;
- mantener domain lock.

---

# 38. No usar navegador personal

La automatización no debe adoptar pestañas personales existentes.

---

# 39. Web research normal

Para investigación web general, priorizar herramientas de búsqueda/extracción de Hermes.

Chrome/ChatGPT queda reservado a la consulta de ChatGPT y casos donde navegador real sea necesario.

---

# 40. Git

Verificar:

```text
git --version
```

Opcional:

```text
gh --version
```

GitHub CLI puede ser útil, pero no es obligatorio para la primera fase si no se necesita.

---

# 41. Git identity

No cambiar globalmente:

```text
user.name
user.email
```

sin autorización.

Si hacen falta commits y Git no tiene identidad:

usar configuración local al repo o bloquear para decisión.

---

# 42. Node

Qwen Code/Hermes pueden requerir Node dependiendo de versión/distribución.

Antigravity debe comprobar la documentación real de la versión elegida.

No instalar múltiples Node sin necesidad.

---

# 43. Python

Si Hermes o tooling requiere Python:

- detectar versión;
- preferir entorno virtual;
- no contaminar paquetes globales.

---

# 44. Virtual environments

Preferencias:

```text
.venv\
```

o entorno específico dentro de infraestructura.

No instalar indiscriminadamente con pip global.

---

# 45. Dependencias del sistema

Cada dependencia nueva debe documentarse:

```text
nombre
versión
motivo
cómo verificar
cómo desinstalar
```

---

# 46. PowerShell

No modificar:

```text
ExecutionPolicy
```

globalmente.

Si un script necesita bypass temporal:

hacerlo sólo para el proceso específico.

---

# 47. Administrador / UAC

No ejecutar todo el sistema como administrador.

Usar elevación sólo para instalación que realmente la necesite.

Runtime normal:

```text
usuario estándar
```

---

# 48. Variables de entorno

Si se usan:

- documentarlas;
- evitar secretos persistidos en texto;
- preferir ámbito de proceso cuando sea posible.

---

# 49. Paths con espacios

Todo script debe soportar correctamente rutas como:

```text
C:\Users\Pc\Documents\Proyectos Tech\Desarrollador autonomo
```

No asumir paths sin espacios.

---

# 50. Unicode

Archivos de configuración, logs y docs:

```text
UTF-8
```

Evitar problemas con:

- tildes;
- ñ;
- nombres en español.

---

# 51. Logs de instalación

Guardar:

```text
logs\installation\
```

Debe registrar:

- comandos;
- versión;
- resultado;
- errores;
- cambios.

Sanitizar secretos.

---

# 52. Fases de instalación

## Fase A — Inventario

No modificar.

Resultado:

```text
INVENTORY PASS
```

---

## Fase B — Backup

Crear respaldo de configuraciones afectables.

Resultado:

```text
BACKUP PASS
```

---

## Fase C — Qwen local

Validar lo existente.

Resultado:

```text
LLAMA PASS
```

---

## Fase D — Qwen Code

Instalar/configurar/probar.

Resultado:

```text
QWEN_CODE PASS
```

---

## Fase E — Hermes

Instalar/configurar/probar.

Resultado:

```text
HERMES PASS
```

---

## Fase F — Integración

Hermes → Qwen Code.

Resultado:

```text
DELEGATION PASS
```

---

## Fase G — Web

Resultado:

```text
WEB PASS
```

---

## Fase H — ChatGPT

Resultado:

```text
CHATGPT PASS
```

---

## Fase I — Runner/Watchdog

Resultado:

```text
RUNNER PASS
```

---

## Fase J — End-to-End

Resultado:

```text
SYSTEM PASS
```

---

# 53. No avanzar a ciegas

Cada fase debe:

1. ejecutar prueba;
2. guardar evidencia;
3. marcar PASS/FAIL;
4. sólo después continuar.

---

# 54. Rollback

Cada fase que modifica el entorno debe tener instrucciones de rollback.

Ejemplo:

```text
rollback:
- restaurar archivo X
- borrar archivo Y creado
- restaurar PATH anterior
```

---

# 55. Version lock

Después de una instalación funcional:

registrar versiones en:

```text
config\VERSIONS.lock
```

Ejemplo:

```text
llama.cpp = ...
Hermes = ...
Qwen Code = ...
Node = ...
Python = ...
Chrome = ...
```

No es un lockfile de paquetes necesariamente.

Es un manifiesto de entorno conocido.

---

# 56. Actualizaciones

No actualizar automáticamente durante una ejecución autónoma.

Las actualizaciones del stack deben ser una tarea de mantenimiento separada.

---

# 57. Actualización de llama.cpp

Sólo si:

- existe motivo;
- backup;
- prueba de compatibilidad;
- benchmark básico;
- rollback.

---

# 58. Actualización de Qwen Code / Hermes

Antes:

- release notes;
- cambios de CLI;
- compatibilidad;
- backup configs;
- sandbox.

---

# 59. Prueba de instalación limpia

El proyecto debe documentar cómo reconstruir la infraestructura en otra PC compatible.

No es requisito automatizar toda la migración en v1, pero sí dejar dependencias claras.

---

# 60. Scripts principales previstos

```text
scripts\
  start-llama.*
  stop-llama.*
  health-llama.*
  inventory.*
  backup-config.*
  verify-install.*
```

La extensión final puede ser:

- PowerShell;
- Python;
- otra opción justificada.

---

# 61. Runner previsto

```text
runner\
  supervisor.*
  watchdog.*
  model-lock.*
  state-manager.*
  cleanup.*
```

La tecnología final debe elegirse por robustez, no por comodidad momentánea.

---

# 62. Launcher visible

Crear:

```text
INICIAR-DESARROLLADOR-AUTONOMO.bat
```

Debe ser simple.

Ejemplo conceptual:

```text
llamar Runner
```

No meter toda la lógica dentro del `.bat`.

---

# 63. Stop launcher

Crear:

```text
DETENER-DESARROLLADOR-AUTONOMO.bat
```

Debe activar un stop seguro.

No matar arbitrariamente procesos ajenos.

---

# 64. Comprobación de RAM

El Runner puede registrar:

- RAM disponible;
- VRAM disponible;
- proceso llama.

No necesita bloquear por umbral todavía salvo riesgo claro.

---

# 65. Seguridad de puerto

Antes de iniciar `8080`:

- comprobar uso;
- si ocupado por otro proceso, no matar automáticamente;
- registrar conflicto;
- elegir acción segura.

---

# 66. Firewall

No abrir reglas de firewall para llama.cpp.

No es necesario con:

```text
127.0.0.1
```

---

# 67. Estado de instalación

Crear:

```text
config\INSTALLATION-STATE.json
```

Ejemplo:

```json
{
  "inventory": "PASS",
  "llama": "PASS",
  "qwen_code": "PASS",
  "hermes": "PASS",
  "delegation": "PENDING",
  "chatgpt": "PENDING",
  "runner": "PENDING",
  "e2e": "PENDING"
}
```

---

# 68. Evidencia de instalación

Guardar:

```text
evidence\installation\
```

Ejemplos:

```text
llama-health.txt
qwen-code-version.txt
hermes-version.txt
delegation-test.json
chatgpt-test.md
```

---

# 69. Criterio de instalación terminada

No se considera instalado sólo porque los ejecutables existan.

Debe cumplir:

```text
INVENTORY PASS
BACKUP PASS
LLAMA PASS
QWEN_CODE PASS
HERMES PASS
DELEGATION PASS
WEB PASS
CHATGPT PASS
SECURITY PASS
ANTI_LOOP PASS
RUNNER PASS
SYSTEM PASS
```

---

# 70. Dependencias para Extracción Documental

Para el procesamiento de especificaciones en formatos no planos:
- **Formatos Nativos:** Texto plano, Markdown, JSON, YAML y formatos convertibles mediante utilidades estándar del sistema.
- **Dependencias Opcionales:** Librerías especializadas de Python como `openpyxl` (XLSX), `mammoth` / `python-docx` (DOCX), `pypdf` / `pdfminer` (PDF).
- **Directiva de Instalación:** **NO instalar dependencias opcionales en esta fase.** Su evaluación, auditoría de vulnerabilidades y necesidad operativa se evaluarán durante la Macrofase 7A (subfase 7A.3).

---

# 71. Directorio Canary y Staging para Auto-Update

Cualquier prueba de actualización de Hermes Agent debe realizarse en un staging desacoplado:
- Directorio de staging: `sandbox\canary-update\`
- No se ejecutan comandos `hermes update` sobre el entorno productivo.
- El procedimiento requiere snapshot previo de `~/.hermes/` y del virtualenv en `backups/updates/<timestamp>/`.

---

# 72. Regla para Antigravity

Antigravity debe actuar primero como auditor del entorno y después como instalador.

Orden obligatorio:

```text
INSPECT
→ BACKUP
→ INSTALL/CONFIGURE
→ VERIFY
→ DOCUMENT
```

No:

```text
INSTALL FIRST
→ SEE WHAT BREAKS
```

Si encuentra componentes previamente configurados:

- no sobrescribirlos sin necesidad;
- comparar;
- reutilizar;
- hacer backup antes de tocar.

