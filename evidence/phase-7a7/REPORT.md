# 7A.7 — Cron + No-Agent Jobs: PASS

El adapter governed-cron.py usa las APIs nativas cronjob y cron.scheduler.run_job.
Cada proyecto sandbox autorizado recibe un HERMES_HOME aislado bajo .autopilot.
El catálogo fijo config/cron-catalog.json acepta únicamente scripts no_agent
verificados por SHA-256. Nunca admite comandos ni prompts libres, jobs ajenos,
cambios de cwd, scripts adulterados ni jobs con inferencia. El profile de soporte
es context-only. Scripts tienen deadline nativo de 5s y cleanup de árbol de procesos.

CRON-001: create/list/pause/resume/remove reales PASS. El job health_snapshot
ejecutó scheduler nativo sin construir AIAgent ni acceder a red; tripwires activos.
CRON-002: catálogo inválido, git push, traversal y hash adulterado DENY; 0 jobs.
CRON-003: script privado no programado sleep30 expiró en 1s; PID detenido PASS.
Inference Lock permaneció intacto: cero inferencias. No se inició daemon/timer.
No habilitar scripts con agente ni scheduler persistente hasta la integración
Cron → Runner → Watchdog → RUN-CONTRACT de 7B. La lista de jobs es nativa; la
admisión y revalidación pertenecen al control determinista. No deps nuevas.
Evidencia: evidence/phase-7a7/. Error corregido: API pública devuelve job_id.
El job parcial de ese intento se retiró por ID exacto y metadata comprobada.
