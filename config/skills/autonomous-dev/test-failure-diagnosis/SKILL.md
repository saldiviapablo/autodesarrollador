---
name: test-failure-diagnosis
description: Project convention SOP for Desarrollador Autonomo to diagnose failing tests and produce structured root-cause verdicts.
---

# SOP: Diagnóstico Estructurado de Tests Fallidos (`test-failure-diagnosis`)

## 1. Propósito
Establecer el procedimiento operativo estándar (SOP) obligatorio del proyecto **Desarrollador Autónomo** para diagnosticar fallos de tests o builds de manera determinista, aislando la causa raíz real sin adivinar ni ocultar errores.

## 2. Cuándo Activarla
- Cuando un test unitario, de integración o suite de verificación devuelve `FAIL` o código de salida distinto de `0`.
- Cuando existe discrepancia entre el estado esperado y la salida real de un script de prueba.
- Antes de delegar una corrección de bug o fallo de test al worker (`Qwen Code CLI`).

## 3. Entradas Esperadas
- Nombre o ruta del test/script fallido.
- Salida real de ejecución (`stdout`, `stderr`, `exit_code`) o archivo de log/stacktrace.
- Archivos de código fuente y test involucrados en el alcance del `RUN-CONTRACT.yaml`.

## 4. Procedimiento Paso a Paso
1. **Identificar el test fallido exacto**:
   - Registrar el identificador del test, archivo, línea exacta y código de salida (`exit_code`).
2. **Leer el stacktrace y log real (Nivel 1)**:
   - Inspeccionar el mensaje de error literal y la traza de ejecución real en disco/consola. No confiar en resúmenes previos ni en entradas antiguas de `MEMORY.md` (Nivel 2).
3. **Clasificar la categoría del fallo (`FAILURE_CATEGORY`)**:
   - `CODE_DEFECT`: el código de producción incumple la especificación o introduce una regresión.
   - `TEST_DEFECT`: el test contiene una aserción desactualizada, mock inválido o supuesto falso.
   - `ENVIRONMENT_FAILURE`: dependencia ausente, puerto ocupado, lock activo o recurso externo caído.
4. **Proponer cambio mínimo verificable (`MINIMAL_FIX`)**:
   - Definir la modificación más pequeña y localizada que resuelve la causa raíz sin alterar contratos ajenos.
5. **Exigir re-ejecución determinista (`DETERMINISTIC_RETEST`)**:
   - Especificar el comando exacto de re-ejecución y el criterio objetivo (`exit_code == 0` y output esperado) que confirma la resolución.

## 5. Salida / Evidencia Esperada
Todo diagnóstico ejecutado bajo esta Skill debe incluir explícitamente el bloque estructurado:
- `DIAGNOSIS_SKILL_APPLIED: test-failure-diagnosis`
- `FAILED_TEST`: nombre/archivo del test
- `FAILURE_CATEGORY`: `CODE_DEFECT` | `TEST_DEFECT` | `ENVIRONMENT_FAILURE`
- `ROOT_CAUSE`: causa técnica verificada en Nivel 1
- `MINIMAL_FIX`: cambio mínimo propuesto
- `DETERMINISTIC_RETEST`: comando de verificación obligatoria

## 6. Prohibiciones Explícitas
- **PROHIBIDO** declarar `PASS` sin re-ejecutar determinísticamente el test fallido.
- **PROHIBIDO** desactivar, comentar o borrar tests para ocultar un fallo.
- **PROHIBIDO** ejecutar `git push`, `git reset --hard`, `git clean -fdx` o comandos destructivos.
- **PROHIBIDO** modificar `config/security.yaml`, `RUN-CONTRACT.yaml` o escribir fuera del workspace autorizado.
- **PROHIBIDO** incluir secretos, tokens o credenciales en texto plano dentro de diagnósticos, reportes o `MEMORY.md`.
