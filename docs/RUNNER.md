# Runner determinista — F17–F22

PowerShell 5.1, PROJECT_ROOT canónico distinto de la infraestructura, contrato
estricto existente y RUN-PLAN.json tipado; aprobación una sola vez por digest
de ambos y componentes congelados. Prepare genera run_id y contrato draft;
Approve requiere digest explícito. Sin receipt válido Start es DENY y no inicia
modelo. Fuente de autoridad: contrato/plan/hashes, nunca stdout del agente.

Runner posee mutex global Local\DesarrolladorAutonomo_RunMutex; metadata LOCK
se reconcilia únicamente después de adquirir el mutex kernel. Lifecycle por PID,
birth ticks y Job Object. Llama real qwen36/127.0.0.1:8080/65536/parallel1, health
antes de inferencia y activo entre roles. Listener preexistente incompatible se
rechaza sin terminarlo; compatible se marca EXTERNAL y no pertenece al job.

Hermes Supervisor/Reviewer readonly y Qwen Code principal mediante wrappers
aprobados; cada wrapper conserva su Inference Lock. Heartbeat/STATE/EVENTS y
checkpoint terminal. Timeout global/fase, STOP y observer Watchdog independiente.
Recovery llama protocolo aprobado desde disco, incluso STATE corrupto.

Cron: register-runner-cron.py registra dispatcher nativo no-agent y comprueba
receipt antes de registrar. El scheduler tick dispara Runner, quien vuelve a
validar contrato. Cron no realiza inferencia; las inferencias de los agentes
pertenecen al Runner y quedan serializadas. Job retirado al terminar las pruebas.

F17 pruebas: lifecycle/admisión/timeout/error/cleanup; cadena REAL llama + Hermes
Supervisor + Qwen Code + Reviewer (213s); scheduler tick nativo; recuperación y
listener externo preservado. Evidencia: evidence/phase-17/.
Hasta instalar el Completion Gate completo de F20, resultado técnico SUCCESS
termina STALLED/COMPLETION_GATE_NOT_INSTALLED; jamás COMPLETED por exit0.

Correcciones: File.Replace requiere backup path no nulo en PS5; PSModulePath de
PowerShell7 heredado desde Python se fija a módulos PS5 SOLO en el proceso Runner;
cmdlet Get-FileHash cargado explícitamente; grupo de linters ausente no es comando.
psutil no instalado en Python principal: prueba usa API Win32 stdlib, sin instalar.
No actualización ni dependencia nueva. F18 completa y certifica fault recovery.

Estado actual 7B PASS: Completion Gate instalado; sólo evidencias deterministas permiten COMPLETED. Guardian acotado sobrevive al padre para reportar crash y termina. Reintentos/ciclos/reloj persistidos, reportes terminales sanitizados y cleanup verificado. La limitación del gate no instalado descrita arriba es evidencia histórica de F17. E2E y regression final: evidence/e2e-7b/ y evidence/regression-7b-final/.
