---
name: technical-audit-review
description: Project convention SOP for Desarrollador Autonomo to audit git diffs, acceptance criteria, and regressions before approval.
---

# SOP: Auditoría Técnica y Revisión de Cambios (`technical-audit-review`)

## 1. Propósito
Establecer el procedimiento operativo estándar (SOP) obligatorio del proyecto **Desarrollador Autónomo** para auditar cambios generados por un worker o sesión antes de emitir un veredicto de aceptación (`PASS` / `FAIL`).

## 2. Cuándo Activarla
- Al revisar el resultado de una delegación a `Qwen Code CLI` o subagente.
- Antes de pasar por el `Completion Gate` o cerrar una fase/tarea del `RUN-CONTRACT.yaml`.
- Cuando se solicita una auditoría independiente (Hermes Reviewer) sobre un diff o working tree.

## 3. Entradas Esperadas
- Estado del repositorio (`git status --short`, `git diff`).
- Criterios de aceptación definidos en `.autopilot/RUN-CONTRACT.yaml` o en la especificación de la tarea.
- Resultado real de la ejecución de tests y build (Nivel 1).

## 4. Procedimiento Paso a Paso
1. **Inspeccionar `git status` y `git diff` reales**:
   - Enumerar todos los archivos modificados, añadidos o eliminados.
   - Detectar archivos espurios, temporales, logs, backups o artefactos fuera de alcance.
2. **Verificar criterios de aceptación del contrato**:
   - Contrastar cada requisito del `RUN-CONTRACT.yaml` contra la evidencia real en código y artefactos.
3. **Detectar regresiones y violaciones de alcance**:
   - Verificar que no se hayan eliminado funciones, comentarios relevantes, validaciones o guardrails existentes.
   - Confirmar que ningún archivo protegido (`config/security.yaml`, `runner/`, `RUN-CONTRACT.yaml`) haya sido alterado sin autorización.
4. **Verificar sanitización de secretos**:
   - Comprobar que el diff no introduzca claves (`sk-...`, `ghp_...`, `Bearer ...`, `password=...`, `api_key=...`, `token=...`).
5. **Comprobar tests y build reales antes de aceptar**:
   - Confirmar mediante ejecución real o evidencia determinista Nivel 1 que la suite de pruebas pasa (`exit_code == 0`).

## 5. Salida / Evidencia Esperada
Toda auditoría ejecutada bajo esta Skill debe producir un dictamen estructurado con:
- `AUDIT_SKILL_APPLIED: technical-audit-review`
- `FILES_REVIEWED`: lista de archivos auditados en `git status` / `git diff`
- `CONTRACT_COMPLIANCE`: `COMPLIANT` | `NON_COMPLIANT`
- `REGRESSIONS_OR_SPURIOUS_FILES`: hallazgos o `NONE`
- `TESTS_VERIFIED_LEVEL_1`: `PASS` | `FAIL`
- `FINAL_AUDIT_VERDICT`: `APPROVE` | `REJECT`

## 6. Prohibiciones Explícitas
- **PROHIBIDO** aprobar (`APPROVE`) basándose únicamente en que el worker dijo `DONE` o en recuerdos de `MEMORY.md` (Nivel 2).
- **PROHIBIDO** ejecutar `git add .` a ciegas o ejecutar `git push`.
- **PROHIBIDO** relajar o ignorar políticas de `config/security.yaml`.
- **PROHIBIDO** exponer secretos en el reporte de auditoría.
