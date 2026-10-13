# Desarrollador Autónomo

**Versión de documentación:** 2.0  
**Estado:** APROBADO / FROZEN PARA IMPLEMENTACIÓN DE MACROFASE 7A  
**Arquitectura principal:** Hermes Agent + Qwen Code CLI + Qwen local mediante llama.cpp

---

# 1. Qué es este proyecto

**Desarrollador Autónomo** es una infraestructura local para convertir una PC Windows en un trabajador de programación capaz de recibir:

- un proyecto existente;
- un objetivo general;
- criterios de aceptación;

y trabajar durante horas de manera autónoma.

El sistema debe poder:

```text
entender
↓
planificar
↓
investigar
↓
programar
↓
probar
↓
detectar errores
↓
corregirse
↓
recordar
↓
recuperarse
↓
validar
↓
reportar
```

sin depender de supervisión humana constante.

---

# 2. Arquitectura elegida

```text
                   USUARIO
                      │
                      ▼
            HERMES AGENT (Supervisor)
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
  QWEN CODE CLI             HERMES REVIEWER
 (Coding Worker)         (Auditor independiente)
        │                           │
        └─────────────┬─────────────┘
                      │
                      ▼
                  LLAMA.CPP (127.0.0.1:8080)
                      │
                      ▼
        Qwen3.6-35B-A3B Q4_K_M (64K context)
                      │
                      ▼
               PROYECTO + GIT
```

La arquitectura se articula en dos capas bien diferenciadas:

### HERMES CAPABILITY LAYER
- Memoria Persistente (Nivel 2)
- Skills (Memoria Procedimental)
- Servidores MCP
- Plugins / Herramientas Custom
- Browser Automation Nativo
- Bot Mode (Supervisor, Reviewer, Researcher)
- Subagentes Jerárquicos
- Git Worktrees Isolados
- Cron y Jobs sin Agente
- Extracción de Documentos
- Gateway Multiplataforma
- Web Dashboard (Superficie administrativa y observabilidad local)
- Auto-Update Controlado

### DETERMINISTIC CONTROL LAYER (Autoritativa)
- RUN-CONTRACT.yaml
- STATE.json / EVENTS.jsonl
- Checkpoints Inmutables
- Security Guard (Path, Command, Secret)
- Progress Guard (Anti-loop)
- Inference Lock (.NET Mutex, parallel = 1)
- Runner de Ciclo de Vida
- Watchdog de Procesos
- Cleanup Garantizado
- Completion Gate

---

# 3. Roles principales

## Hermes Supervisor
Hermes es el cerebro supervisor y orquestador.
Debe:
- recibir objetivos y ejecutar preflight;
- generar el `RUN-CONTRACT`;
- planificar y dividir trabajo;
- investigar web y consultar ChatGPT;
- supervisar el progreso de los workers;
- validar y emitir aceptación/rechazo (`DECISION: ACCEPTED/REJECTED`).

Hermes NO es el coding worker principal.

---

## Qwen Code CLI (Coding Worker)
Qwen Code es el especialista autónomo en programación.
Debe:
- analizar repositorios y código fuente;
- modificar archivos y crear tests;
- ejecutar comandos, linters y builds;
- gestionar Git local;
- diagnosticar fallos y autocorregirse.

---

## Hermes Reviewer (Auditor Independiente)
Instancia de auditoría separada encargada de:
- auditar diffs y cambios antes de la integración;
- verificar objetivamente criterios de aceptación;
- certificar la ausencia de regresiones.

---

## Runner y Watchdog
Componentes deterministas fuera de los modelos LLM responsables del ciclo de vida, timeouts, health checks, serialización de inferencia y cleanup de procesos.

---

## Qwen local + llama.cpp

Es el modelo local compartido.

Configuración base validada:

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

---

# 4. Regla clave de recursos

El modelo local usa:

```text
--parallel 1
```

Por lo tanto:

> **Sólo puede existir una inferencia Qwen activa a la vez.**

Hermes y Qwen Code pueden realizar otras tareas en paralelo, como:

- web;
- tests;
- builds;
- filesystem;
- Git;

pero el acceso al modelo local debe estar serializado mediante un `Inference Lock` o mecanismo equivalente.

---

# 5. Qwen 64K ya fue validado

Se realizó una prueba real progresiva hasta 60.000 tokens.

Resultados:

| Tokens reales | RAM máx. usada | RAM libre mín. | llama WS máx. | VRAM máx. |
|---:|---:|---:|---:|---:|
| 8K | 21.83 GB | 9.84 GB | 12.81 GB | 4186 MB |
| 16K | 22.12 GB | 9.55 GB | 13.10 GB | 4198 MB |
| 32K | 22.37 GB | 9.30 GB | 13.38 GB | 4198 MB |
| 48K | 22.37 GB | 9.30 GB | 13.56 GB | 4198 MB |
| 60K | 22.39 GB | 9.28 GB | 13.69 GB | 4198 MB |

Conclusión inicial:

```text
64K es viable en el hardware probado.
```

También se validó que al cerrar `llama-server` se libera correctamente la memoria utilizada.

---

# 6. Filosofía del proyecto

## 6.1 El chat no es memoria suficiente

La conversación activa puede compactarse o reiniciarse.

Por eso la continuidad depende de:

```text
filesystem
Git
tests/build
STATE.json
STATE.md
EVENTS.jsonl
QWEN.md
checkpoints
sesiones persistentes
```

---

## 6.2 Un agente diciendo “terminé” no alcanza

Debe existir evidencia.

Ejemplos:

```text
test PASS
build PASS
artefacto existe
endpoint responde
Git diff correcto
criterios cumplidos
```

---

## 6.3 Autonomía no significa acceso ilimitado

Dentro del workspace:

```text
alta autonomía
```

Fuera del workspace:

```text
mínimo privilegio
```

---

## 6.4 Recuperarse es obligatorio

Si falla:

- Qwen Code;
- Hermes;
- llama.cpp;
- una sesión;
- Windows;

el sistema debe poder reconstruir el estado.

---

# 7. Flujo de una ejecución

```text
Usuario selecciona proyecto
        ↓
Objetivo
        ↓
Hermes hace preflight
        ↓
RUN-CONTRACT
        ↓
Usuario aprueba una vez
        ↓
Runner inicia llama.cpp
        ↓
Hermes planifica
        ↓
Qwen Code implementa
        ↓
Tests / build
        ↓
¿falló?
 ├─ sí → diagnosticar / corregir / investigar
 └─ no
        ↓
Checkpoint
        ↓
Siguiente tarea
        ↓
Completion Gate
        ↓
Informe final
        ↓
Cleanup
        ↓
Cerrar llama.cpp
```

---

# 8. ChatGPT dentro del sistema

ChatGPT actúa únicamente como:

```text
CONSULTOR EXTERNO
```

Flujo:

```text
Hermes
  ↓
consultar_chatgpt
  ↓
Chrome dedicado
  ↓
chatgpt.com
  ↓
respuesta
  ↓
Hermes evalúa
  ↓
Qwen Code implementa
```

ChatGPT no debe modificar directamente el proyecto.

---

# 9. Documentos del proyecto

## `00-README.md`

Visión general y punto de entrada.

---

## `01-OBJETIVOS-Y-REQUISITOS.md`

Especificación funcional.

Define:

- qué debe hacer;
- requisitos;
- prioridades;
- criterios de aceptación;
- definición de terminado.

---

## `02-ARQUITECTURA.md`

Define:

- componentes;
- responsabilidades;
- Runner;
- Watchdog;
- Inference Lock;
- flujo;
- ChatGPT;
- locks;
- recovery;
- Completion Gate.

---

## `03-MEMORIA-Y-CONTINUIDAD.md`

Define:

- STATE;
- EVENTS;
- checkpoints;
- sesiones;
- recuperación;
- compactación;
- reconciliación;
- integridad.

---

## `04-AUTONOMIA-Y-SEGURIDAD.md`

Define:

- autorización única;
- acciones permitidas;
- acciones prohibidas;
- límites de workspace;
- Git;
- secretos;
- navegador;
- anti-loop;
- bloqueo humano.

---

## `05-INSTALACION-Y-CONFIGURACION.md`

Define:

- entorno conocido;
- llama.cpp;
- modelo Qwen;
- 64K;
- componentes legacy;
- inventario;
- backups;
- instalación;
- configuración central;
- rollback.

---

## `06-PRUEBAS-Y-CRITERIOS-DE-EXITO.md`

Define cómo demostrar que cada componente funciona.

Nada debe marcarse `PASS` sin evidencia.

---

## `07-ROADMAP.md`

Define el orden de implementación por macrofases (Macrofases 1 a 6 aprobadas, Macrofases 7A, 7B y 8 pendientes).

---

## `08-CAPACIDADES-NATIVAS-HERMES.md`

Especificación canónica, matriz de preparación y gobernanza de las 14 capacidades nativas de Hermes Agent y del subsistema de idempotencia.

---

## `AGENTS.md`

Reglas operativas obligatorias para Antigravity, Codex y otros agentes.

Debe leerse antes de modificar el proyecto.

---

# 10. Carpeta esperada

Estructura canónica:

```text
Desarrollador autonomo/
│
├── 00-README.md
├── 01-OBJETIVOS-Y-REQUISITOS.md
├── 02-ARQUITECTURA.md
├── 03-MEMORIA-Y-CONTINUIDAD.md
├── 04-AUTONOMIA-Y-SEGURIDAD.md
├── 05-INSTALACION-Y-CONFIGURACION.md
├── 06-PRUEBAS-Y-CRITERIOS-DE-EXITO.md
├── 07-ROADMAP.md
├── 08-CAPACIDADES-NATIVAS-HERMES.md
├── AGENTS.md
├── MANIFEST.md
│
├── config/
├── runner/
├── scripts/
├── tools/
├── tests/
├── sandbox/
├── backups/
├── docs/
├── logs/
└── evidence/
```

Las subcarpetas son gestionadas de forma controlada según el avance de cada fase.

---

# 11. Estado actual

Fases Aprobadas y Certificadas (PASS):

```text
Macrofase 1: Baseline e Inventario (Fases 0 a 4) — PASS
Macrofase 2: Qwen Code CLI (Fase 5) — PASS
Macrofase 3: Hermes Agent (Fase 6) — PASS
Macrofase 4: Integración Hermes ↔ Qwen Code (Fases 7 a 9) — PASS
Macrofase 5: Memoria y Continuidad (Fases 10 a 12) — PASS
Macrofase 6: Web, ChatGPT, Seguridad y Anti-Loop (Fases 13 a 16) — PASS
```

Estado de las macrofases restantes:

```text
Macrofase 7A: Hermes Native Capabilities (7A.1 a 7A.10) — IN_PROGRESS
  7A.1 — PASS
  7A.2 — PASS
  7A.3 — PASS
  7A.4 — PASS
  7A.5 — PASS
  7A.6 — PASS
  7A.7 — PASS
  7A.8 — PASS
  7A.9 — PASS
  7A.10–7A.10 — PENDING
Macrofase 7B: Runner Autónomo Nocturno (Fases 17 a 22) — PENDING
Macrofase 8:  Validación Final (Fases 23 a 28) — PENDING
```

---

# 12. Qué debe hacer Antigravity primero

No instalar inmediatamente.

Orden inicial:

```text
1. leer AGENTS.md
2. leer toda la documentación
3. inspeccionar el entorno
4. generar INVENTORY
5. comparar realidad con documentación
6. hacer backups
7. recién entonces comenzar implementación
```

---

# 13. Qué NO debe hacer Antigravity

No debe:

- reinstalar todo;
- descargar otro Qwen;
- cambiar drivers;
- alterar Windows innecesariamente;
- reutilizar launchers legacy como sistema nuevo;
- reducir 64K silenciosamente;
- cambiar Hermes por otro supervisor;
- cambiar Qwen Code por otro coding worker;
- eliminar STATE/checkpoints;
- desactivar seguridad para “hacerlo funcionar”;
- marcar éxito sin pruebas.

---

# 14. Launchers legacy

Existen configuraciones antiguas de Goose.

Deben considerarse:

```text
LEGACY
```

No son la arquitectura actual.

No deben borrarse hasta tener sistema nuevo validado.

---

# 15. Cómo se considera listo

No alcanza con instalar programas.

La versión 1.0 requiere demostrar:

```text
llama
Qwen Code
Hermes
delegación
Inference Lock
STATE
Recovery
continuidad
web
ChatGPT
seguridad
anti-loop
Runner
Watchdog
Completion Gate
reporting
cleanup
E2E
prueba prolongada
```

---

# 16. Resultado esperado final

La experiencia del usuario debe ser aproximadamente:

```text
abrir Desarrollador Autónomo
        ↓
seleccionar proyecto
        ↓
decir qué quiere lograr
        ↓
responder pocas preguntas iniciales
        ↓
INICIAR
```

Después:

```text
el usuario se va
```

y el sistema:

```text
investiga
programa
prueba
corrige
recuerda
recupera
continúa
```

hasta:

```text
COMPLETED
```

o:

```text
BLOCKED_REQUIRES_HUMAN
STALLED
FAILED
```

con un informe que explique exactamente qué ocurrió.

---

# 17. Regla final

El objetivo no es crear un chatbot de programación.

El objetivo es construir:

> **un trabajador de programación autónomo, persistente, verificable y recuperable que pueda trabajar durante horas sobre proyectos reales con límites de seguridad claros.**
