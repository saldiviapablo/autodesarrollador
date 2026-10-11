# Inventario del Entorno Real
## Proyecto: Desarrollador Autónomo — Fase 1 (Inventario)

**Fecha y hora de auditoría:** 2026-10-11T18:25:00-03:00  
**Resultado de la fase:** PASS  
**Auditor:** Antigravity (Advanced Agentic Coding)  
**Entorno de ejecución:** Host local Windows sin elevación UAC innecesaria  

---

# 1. Resumen Ejecutivo

Se completó la **FASE 1 — INVENTARIO DEL ENTORNO** de acuerdo con las especificaciones de `AGENTS.md` y `07-ROADMAP.md`. No se instaló ningún componente nuevo, no se modificaron archivos fuera de la infraestructura ni se alteraron configuraciones legacy.

### Conclusiones Principales:
1. **La base de inferencia local ya existe y está intacta:** `llama-server.exe` (build 11368 con soporte CUDA 12.4) y el modelo `Qwen3.6-35B-A3B-Q4_K_M.gguf` (19.02 GB en caché HuggingFace) están presentes y verificados.
2. **El puerto 8080 está libre** y no hay procesos `llama-server` huérfanos.
3. **El entorno base de ejecución es excelente:** Python 3.14.4 (con Python 3.12.12 y `uv` 0.12.0 adicionales), Node.js v24.14.1, npm 11.11.0, Git 2.53.0 y GitHub CLI 2.96.0 autenticado.
4. **Qwen Code CLI y Hermes Agent NO están instalados aún:** Ambos deben ser introducidos en sus fases correspondientes (Fase 5 y Fase 6 respectivamente).
5. **Configuraciones Legacy detectadas:** Existen scripts y lanzadores de pruebas previas con Goose y OpenCode (ej. perfiles de 16K y 32K context) que han sido categorizados formalmente como **LEGACY** para evitar su uso accidental.

---

# 2. Matriz Completa de Componentes Inventariados

### Clasificación de Estados:
- **ACTUAL:** Componente vigente y aprobado para la arquitectura en curso.
- **LEGACY:** Componente o script de pruebas históricas (Goose, OpenCode) que no debe tocarse ni borrarse en esta fase.
- **NO INSTALADO / PENDIENTE:** Componente requerido por el Roadmap pendiente de instalación en su fase asignada.
- **DESCONOCIDO / UNKNOWN:** Componente cuya existencia o estado no pudo ser verificado.

| Componente | Categoría | Encontrado | Versión / Build | Ruta / Ubicación | Estado Operativo | Comando de Verificación | Observaciones / Posibles Conflictos |
|:---|:---:|:---:|:---|:---|:---:|:---|:---|
| **Sistema Operativo** | ACTUAL | SÍ | Windows 11 Pro (10.0.26200, 64-bit) | `C:\Windows` | ÓPTIMO | `Get-CimInstance Win32_OperatingSystem` | **Discrepancia menor de doc:** En `05-INSTALACION-Y-CONFIGURACION.md` se mencionaba Windows 10 Pro. |
| **Procesador (CPU)** | ACTUAL | SÍ | AMD Ryzen 5 8400F (6 Cores / 12 Threads) | Socket AM5 | ÓPTIMO | `Get-CimInstance Win32_Processor` | Adecuado para offloading CPU MoE (`--cpu-moe`). |
| **Memoria RAM** | ACTUAL | SÍ | 31.67 GB (~32 GB DDR5) | Motherboard | 15.13 GB libres | `Get-CimInstance Win32_ComputerSystem` | Margen suficiente para el working set de 64K validado previamente (~13.7 GB). |
| **Placa de Video (GPU)** | ACTUAL | SÍ | NVIDIA GeForce RTX 4060 Ti | PCIe Slot 1 | ÓPTIMO | `nvidia-smi` | Driver 591.86, CUDA 13.1 nativo. |
| **Memoria VRAM** | ACTUAL | SÍ | 8188 MiB (~8 GB GDDR6) | GPU On-board | ~7.0 GB libres (1200 MiB en uso de escritorio) | `nvidia-smi` | Suficiente para offload parcial GPU (`--n-gpu-layers 99`) y KV Cache quantizado. |
| **llama.cpp (Binario)** | ACTUAL | SÍ | 0.5.0-dev (build 11368, commit 1fb7ef3e3, Clang 20.1.8) | `C:\AI\llama.cpp\llama-server.exe` | LISTO PARA FASE 3 | `& "C:\AI\llama.cpp\llama-server.exe" --version` | Binario de 9,216 bytes con `ggml-cuda.dll` (567 MB) y librerías CUDA 12.4 dinámicas presentes. |
| **Modelo Qwen GGUF** | ACTUAL | SÍ | Qwen3.6-35B-A3B Q4_K_M | `C:\Users\Pc\.cache\huggingface\hub\models--ggml-org--Qwen3.6-35B-A3B-GGUF\snapshots\baec3ebee244827cda0f4557eafa8b28f7545fa6\Qwen3.6-35B-A3B-Q4_K_M.gguf` | LISTO PARA FASE 3 | `Get-Item` (Inspección de enlace simbólico y archivo blob) | El snapshot es un SymbolicLink hacia el blob `671e47e0...` de 20,419,565,568 bytes (19.02 GB). También existe `mmproj` (0.57 GB). |
| **Procesos llama-server** | ACTUAL | NO | N/A | En memoria | NINGUNO ACTIVO | `Get-Process *llama*` | No existen procesos residuales. Estado limpio. |
| **Puerto 8080** | ACTUAL | SÍ (Libre) | N/A | `127.0.0.1:8080` | DISPONIBLE | `Get-NetTCPConnection -LocalPort 8080` | Puerto completamente desocupado. |
| **Git** | ACTUAL | SÍ | 2.53.0.windows.3 | `C:\Program Files\Git\cmd\git.exe` | ÓPTIMO | `git --version` | Configuración global: `Pablo Saldivia <pablosaldiviainfo@gmail.com>`, `init.defaultbranch=master`. |
| **GitHub CLI** | ACTUAL | SÍ | 2.96.0 (2026-07-02) | `C:\Program Files\GitHub CLI\gh.exe` | ÓPTIMO | `gh --version` / `gh auth status` | Sesión activa iniciada para la cuenta `saldiviapablo`. |
| **Node.js** | ACTUAL | SÍ | v24.14.1 | `C:\Program Files\nodejs\node.exe` | ÓPTIMO | `node --version` | Compatible para ejecutar `@qwen-code/qwen-code` (requiere Node >= 22). |
| **npm** | ACTUAL | SÍ | 11.11.0 | `C:\Program Files\nodejs\npm.ps1` | ÓPTIMO | `npm --version` | Paquetes globales detectados: `firebase-tools@15.21.0`, `opencode-ai@1.18.34`, `pnpm@10.33.4`. |
| **Python Principal** | ACTUAL | SÍ | Python 3.14.4 | `C:\Python314\python.exe` y `C:\WINDOWS\py.exe` | ÓPTIMO | `python --version` | Paquetes instalados: `fastapi`, `uvicorn`, `huggingface_hub`, `pydantic`, `PyYAML`, entre otros. |
| **Python Secundario / uv** | ACTUAL | SÍ | Python 3.12.12 / uv 0.12.0 | `C:\Users\Pc\.local\bin\python3.12.exe` / `uv.exe` | DISPONIBLE | `& uv --version` | Excelente herramienta para aislar entornos virtuales rápidos sin tocar Python global. |
| **PowerShell** | ACTUAL | SÍ | 5.1.26100.9444 (Desktop Edition) | `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe` | ÓPTIMO | `$PSVersionTable.PSVersion` | ExecutionPolicy CurrentUser = `RemoteSigned`. PowerShell Core (`pwsh`) no está instalado. |
| **Google Chrome** | ACTUAL | SÍ | 154.0.8037.99 | `C:\Program Files\Google\Chrome\Application\chrome.exe` | INSTALADO | `(Get-Item ...).VersionInfo.ProductVersion` | Perfil dedicado `HERMES-CHATGPT` aún no creado (se creará en Fase 14). |
| **Qwen Code CLI** | PENDIENTE | NO | No instalado en PATH | No aplica | NO INSTALADO | `Get-Command qwen*` | Se verificó disponibilidad en registro npm: `@qwen-code/qwen-code` (v0.25.1) de Alibaba QwenLM. Se instalará en Fase 5. |
| **Hermes Agent** | PENDIENTE | NO | No instalado en PATH/pip | No aplica | NO INSTALADO | `Get-Command hermes*` | Repositorio oficial `NousResearch/hermes-agent`. Se implementará en Fase 6. |
| **Goose CLI** | LEGACY | SÍ | 1.53.0 | `C:\Users\Pc\.local\bin\goose.exe` | LEGACY INTACTO | `& goose.exe --version` | Utilizado en pruebas anteriores con GOOSE-TEST. Preservado sin alteraciones. |
| **OpenCode CLI** | LEGACY | SÍ | 1.18.34 | `C:\Users\Pc\AppData\Roaming\npm\opencode.ps1` | LEGACY INTACTO | `opencode --version` | Utilizado en pruebas anteriores (`C:\AI\PRUEBA-OPENCODE`). Preservado sin alteraciones. |
| **Lanzador Goose 16K (.bat)** | LEGACY | SÍ | N/A | `C:\Users\Pc\Desktop\Iniciar Qwen - Goose 16K.bat` | LEGACY | Inspección de contenido de texto | Configurado para `--ctx-size 16384`. NO usar como configuración del nuevo sistema. |
| **Lanzador Qwen 32K (.bat)** | LEGACY | SÍ | N/A | `C:\Users\Pc\Desktop\Iniciar Qwen.bat` | LEGACY | Inspección de contenido de texto | Configurado para `--ctx-size 32768`. NO usar como configuración del nuevo sistema. |
| **Acceso Directo OpenCode** | LEGACY | SÍ | N/A | `C:\Users\Pc\Desktop\OpenCode.lnk` | LEGACY | Inspección de filesystem | Conservado en el escritorio. |
| **Night Runner Goose (.ps1)** | LEGACY | SÍ | N/A | `C:\Users\Pc\Documents\Proyectos Tech\GOOSE-TEST\goose-night.ps1` | LEGACY | Inspección de contenido de texto | Script antiguo de orquestación nocturna para Goose. |
| **Workspace Actual** | ACTUAL | SÍ | N/A | `C:\Users\Pc\Documents\Proyectos Tech\Desarrollador autonomo` | LISTO | `Get-Item .` | Directorio raíz del nuevo proyecto. Actualmente no es un repositorio Git independiente. |

---

# 3. Análisis de Discrepancias y Contradicciones

Siguiendo el mandato de `AGENTS.md` (no ocultar contradicciones, documentarlas y proponer solución), se detallan los hallazgos:

### 1. Sistema Operativo Documentado vs Real
- **Documento:** `05-INSTALACION-Y-CONFIGURACION.md` (Sección 2) indica: `Windows 10 Pro`.
- **Realidad:** `Microsoft Windows 11 Pro` (Build 26200).
- **Impacto:** Ninguno negativo. Windows 11 maneja perfectamente la virtualización, aceleración CUDA y llamadas de proceso.
- **Propuesta:** Actualizar la documentación en el siguiente paso de revisión para reflejar `Windows 11 Pro`.

### 2. Archivo `MANIFEST.md`
- **Requerimiento:** La instrucción del usuario solicitaba leer `MANIFEST.md` como parte del set inicial.
- **Realidad:** El archivo `MANIFEST.md` no existe en la carpeta raíz del proyecto.
- **Impacto:** Ninguno funcional; la documentación de arquitectura está 100% cubierta por `00-README.md` a `07-ROADMAP.md` y `AGENTS.md`.
- **Propuesta:** Se creará un manifiesto formal de artefactos cuando se generen las estructuras en fases posteriores.

### 3. Numeración de Fases en Documentación
- **Documentos en conflicto:** `07-ROADMAP.md` (Fases 0 a 28) vs `05-INSTALACION-Y-CONFIGURACION.md` (Fases A a J).
- **Resolución:** `AGENTS.md` (Regla 6) establece la jerarquía donde `07-ROADMAP.md` rige el orden y numeración canónica de implementación. Se adopta la nomenclatura numérica de `07-ROADMAP.md` (Fase 0 a Fase 28) en todo el seguimiento del sistema.

### 4. Tamaño Reportado del Archivo GGUF en Windows
- **Observación:** El archivo `Qwen3.6-35B-A3B-Q4_K_M.gguf` en la carpeta `snapshots` tiene `Length = 0` en comandos básicos de PowerShell porque es un **SymbolicLink** de Windows.
- **Verificación real:** El symlink apunta al blob `671e47e0...` dentro del directorio `blobs` de HuggingFace, el cual posee exactamente `20,419,565,568 bytes` (~19.02 GB).
- **Regla para scripts:** Los scripts futuros deben ser conscientes de enlaces simbólicos o resolver la ruta final con `Resolve-Path` / apuntar directamente al alias o flag `-hf`.

---

# 4. Evaluación de Riesgos y Seguridad

1. **Riesgo de Inferencia Concurrente (`--parallel 1`):**
   - Actualmente ningún proceso ocupa el modelo ni el puerto 8080.
   - Es mandatorio implementar el `Inference Lock` (Fase 7) antes de conectar Hermes y Qwen Code para evitar cuelgues o degradación del servidor local.
2. **Coexistencia con Componentes Legacy:**
   - Goose CLI y OpenCode CLI están presentes en el sistema pero no interfieren salvo que un script los invoque. No deben borrarse ni modificarse.
3. **Privilegios:**
   - Todo el inventario se ejecutó en modo usuario estándar, validando que el entorno no requiere privilegios de Administrador para operar normalmente.
4. **Protección de Credenciales:**
   - No se almacenaron tokens, claves ni cadenas sensibles en logs ni documentación. GitHub CLI mantiene su token en el keyring de Windows.

---

# 5. Dictamen de la Fase 1

**ESTADO FINAL DE FASE 1:** **PASS**

El entorno real está completamente identificado, verificado con evidencia determinista y listo para avanzar de forma segura a la **FASE 2 — BACKUP Y BASELINE**.
