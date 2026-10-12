# Auditoría de Seguridad e Integridad del Instalador Oficial de Hermes Agent
## Proyecto: Desarrollador Autónomo — Fase 6

**Fecha de inspección:** 2026-10-12  
**Origen oficial:** `https://hermes-agent.nousresearch.com/install.ps1`  
**Repositorio oficial:** `NousResearch/hermes-agent` (GitHub)  
**Ruta local temporal:** `C:\Users\Pc\AppData\Local\Temp\hermes-install.ps1`  
**Tamaño:** 75,835 bytes  
**Algoritmo de hash:** SHA-256  
**Hash verificado:** `61824D6B47BE29AB793D0E72872CF56CD7A3E99CBE40ABEB177A6C9EEF52F485`

---

## 1. Análisis Técnico y Comportamiento del Instalador

El script `install.ps1` es un instalador de tipo bootstrap diseñado específicamente para entornos Windows nativos. Se compone de las siguientes etapas (`stages`):

1. **Normalización de Rutas (8.3 Short Names):**
   - Corrige alias cortos de Windows (`FIRST~1`) para prevenir errores de resolución en el proveedor de archivos de PowerShell 5.1.
2. **Descarga de Herramientas Aisladas (Store de PM):**
   - Descarga `uv` (versión fijada `0.12.3`, hash SHA-256 `b23350c79e8ad0192b8124af13a0f17e8d4e4549524785e1aef389ae5a06990e`).
   - Descarga PortableGit (`2.53.0.windows.3`, hash SHA-256 `b365da794b1d2225eb24d5f5e09ef7792cfd5fa26c3a3586210280c80dff3a2a`).
   - Ambas herramientas se ubican en el store aislado del usuario (`%LOCALAPPDATA%\hermes\store\`), sin alterar el Git ni el Python global del sistema.
3. **Clonación del Repositorio:**
   - Clona `https://github.com/NousResearch/hermes-agent.git` en `%LOCALAPPDATA%\hermes\hermes-agent` utilizando un clon filtrado por blobs (`--filter=blob:none`).
4. **Entorno Python Aislado:**
   - Utiliza `uv` para aprovisionar un intérprete CPython gestionado (sin tocar `C:\Python314`).
   - Construye el entorno virtual (`venv`) e instala dependencias bloqueadas y verificadas contra `pm/lock.json` y `uv.lock`.
5. **Publicación del Comando CLI:**
   - Genera el lanzador `hermes` en `%LOCALAPPDATA%\hermes\bin\`.
   - Agrega `%LOCALAPPDATA%\hermes\bin\` al `PATH` del usuario actual en el registro (`HKCU\Environment`).
   - No requiere privilegios de Administrador ni elevación UAC.
6. **Opciones Headless/No-Interactivas:**
   - El flag `-NonInteractive` omite las etapas interactivas `setup` (claves Nous Portal) y `gateway` (servicios de mensajería).
   - Los flags `-SkipBrowser` y `-SkipComputerUse` omiten la instalación de navegadores y controladores de interfaz gráfica.

---

## 2. Dictamen de Seguridad
- **Permisos requeridos:** Usuario estándar (sin UAC).
- **Impacto global:** Cero cambios a registro de máquina (`HKLM`), drivers de Windows o dependencias globales.
- **Veredicto:** SEGURO PARA EJECUCIÓN LOCAL.
