---
name: safe-refactoring
description: Project convention SOP for Desarrollador Autonomo to perform behavior-preserving refactoring under strict test and guardrail controls.
---

# SOP: Refactorización Segura Guiada por Tests (`safe-refactoring`)

## 1. Propósito
Definir el procedimiento operativo estándar (SOP) obligatorio del proyecto **Desarrollador Autónomo** para ejecutar refactorizaciones de código preservando el comportamiento observable, la trazabilidad de cambios y el cumplimiento estricto de guardrails.

## 2. Cuándo Activarla
- Cuando se requiere limpiar, modularizar o mejorar la mantenibilidad de código existente sin cambiar su contrato externo.
- Antes de extraer funciones, renombrar símbolos o simplificar estructuras condicionales en el proyecto gestionado.

## 3. Entradas Esperadas
- Archivo(s) objetivo dentro del workspace autorizado.
- Suite de tests existente que cubre el comportamiento actual (línea base Nivel 1).
- Restricciones de alcance del `RUN-CONTRACT.yaml` y `config/security.yaml`.

## 4. Procedimiento Paso a Paso
1. **Verificar tests ANTES de tocar código (Pre-Check Nivel 1)**:
   - Ejecutar los tests existentes y confirmar que pasan (`PASS`) antes de iniciar el refactor. Si fallan previamente, detener el refactor y usar `test-failure-diagnosis`.
2. **Acotar el cambio a pasos pequeños y trazables**:
   - Realizar transformaciones atómicas que preserven firmas públicas y contratos de salida.
   - No mezclar refactorización estructural con cambios funcionales o nuevas features no solicitadas.
3. **Respetar guardrails deterministas de Path, Command y Secret**:
   - Operar exclusivamente dentro del workspace permitido.
   - No tocar archivos protegidos (`config/security.yaml`, `RUN-CONTRACT.yaml`, `runner/`).
4. **Verificar tests DESPUÉS del cambio (Post-Check Nivel 1)**:
   - Re-ejecutar la misma suite de tests y revisar `git diff` para confirmar cero regresiones y cero cambios funcionales accidentales.
5. **Reversión inmediata ante regresión**:
   - Si cualquier test pasa de `PASS` a `FAIL`, revertir o corregir el paso antes de continuar.

## 5. Salida / Evidencia Esperada
Toda refactorización guiada por esta Skill debe reportar:
- `REFACTOR_SKILL_APPLIED: safe-refactoring`
- `PRE_REFACTOR_TESTS`: `PASS`
- `BEHAVIOR_PRESERVED`: `true` | `false`
- `POST_REFACTOR_TESTS`: `PASS`
- `DIFF_SCOPE_CLEAN`: `true` | `false`

## 6. Prohibiciones Explícitas
- **PROHIBIDO** refactorizar sin verificar tests antes y después.
- **PROHIBIDO** mezclar cambios de lógica de negocio no solicitados dentro de un refactor.
- **PROHIBIDO** ejecutar `git push`, `git reset --hard` destructivo o `git clean -fdx`.
- **PROHIBIDO** modificar `config/security.yaml`, `RUN-CONTRACT.yaml` o escribir fuera del workspace autorizado.
- **PROHIBIDO** introducir o registrar secretos en código, logs o `MEMORY.md`.
