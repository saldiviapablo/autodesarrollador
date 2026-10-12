# Perfil Dedicado de Hermes Agent

**Perfil:** `desarrollador-autonomo`  
**Ruta en disco:** `C:\Users\Pc\AppData\Local\hermes\profiles\desarrollador-autonomo\`  
**Fecha de creación:** 2026-10-12  
**Hermes Version:** `v0.21.6`  

---

## 1. Justificación y Propósito

Conforme a las reglas del proyecto (`AGENTS.md`, `02-ARQUITECTURA.md`, `04-AUTONOMIA-Y-SEGURIDAD.md`), el Supervisor / Orquestador debe operar en un entorno completamente aislado:

- Sin afectar otras instalaciones o perfiles globales de Hermes en la máquina.
- Con almacenamiento local dedicado para base de datos SQLite (`state.db`), sesiones, planes, memorias y logs.
- Con variables de entorno (`.env`) y configuración (`config.yaml`) restringidas exclusivamente al backend local `llama-server`.

---

## 2. Creación del Perfil

El perfil fue creado de forma determinista mediante el comando oficial de Hermes CLI:

```powershell
hermes profile create desarrollador-autonomo `
  --no-alias `
  --description "Supervisor y orquestador autonomo para el proyecto Desarrollador Autonomo"
```

---

## 3. Estructura de Directorios y Archivos

```text
C:\Users\Pc\AppData\Local\hermes\profiles\desarrollador-autonomo\
├── .env                  # Variables de entorno y sentinels locales
├── .env.lock             # Lock de permisos de archivo de secretos
├── config.yaml           # Configuración del modelo local y herramientas
├── profile.yaml          # Metadatos del perfil
├── SOUL.md               # Definición de personalidad/instrucciones del perfil
├── audio_cache/          # Cache de audio (inactivo)
├── backups/              # Backups de estado de sesiones
├── cron/                 # Tareas programadas locales
├── home/                 # Directorio home virtual del agente
├── hooks/                # Hooks de ciclo de vida
├── image_cache/          # Cache de imágenes (inactivo)
├── logs/                 # Logs de ejecución del perfil
├── memories/             # Base de conocimiento persistente
├── pairing/              # Dispositivos emparejados (inactivo)
├── plans/                # Planes de trabajo estructurados
├── sessions/             # Historial y estados de sesiones (SQLite / JSON)
├── skills/               # Habilidades locales instaladas
├── skins/                # Temas de interfaz
└── workspace/            # Espacio de trabajo temporal del perfil
```

---

## 4. Configuración Aplicada

### `config.yaml`

```yaml
model:
  default: qwen36
  provider: custom
  base_url: http://127.0.0.1:8080/v1
custom_providers:
  - name: local-qwen
    base_url: http://127.0.0.1:8080/v1
    api_key: local-not-required
    api_mode: chat_completions
    context_length: 65536
    models:
      qwen36:
        context_length: 65536
_config_version: 50
```

### `.env`

```env
# Per-profile secrets for this Hermes profile.
OPENAI_API_KEY=local-not-required
```

---

## 5. Invocación y Parámetros Operativos

Para invocar Hermes bajo este perfil, se utiliza la bandera `-p` / `--profile`:

```powershell
hermes.exe -p desarrollador-autonomo -z "<prompt>"
```

- `-p desarrollador-autonomo`: Dirige todas las lecturas y escrituras al directorio de este perfil.
- `-z`: Ejecuta en modo headless / quiet (one-shot batch), sin banners interactivos ni spinners TUI.
