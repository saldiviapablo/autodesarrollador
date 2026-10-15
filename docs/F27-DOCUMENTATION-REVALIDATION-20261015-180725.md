# F27: corrección documental y nueva revisión humana pendiente

F27 NO se declara PASS. El usuario solicitó cambios sobre tres ejemplos del README después de revisar el resultado real. La revisión anterior, el README original, las decisiones técnicas y todo el run nativo se preservan.

Sólo README.md cambió dentro del piloto. No se modificó module.py, ninguno de los17 tests originales, build.py, sample-records.json ni los dos artefactos finales. No se reabrió el Runner terminado, ni se alteró Started/deadline/presupuestos/restart_budget/STATE nativo/contratos/contadores. Esta validación documental autorizada es independiente del reloj del E2E original, que duró1097.308088s y consumió2 reinicios normales.

Correcciones exactas: round_seconds(1.005) devuelve1.01; Decimal(str(1.005)) produce Decimal('1.005'); se suman valores NORMALIZADOS0.11+2.68+0.00+1.01=3.80.

| Comprobación nueva | Resultado |
|---|---|
| 17 tests de aceptación originales | PASS |
| Build original | PASS |
| Artefactos y sus bytes | PASS, sin cambios |
| Tres ejemplos contra el código real | PASS |
| Hermes Reviewer independiente | ACCEPTED |
| Reviewer read-only, archivos y Git HEAD | PASS |
| Contrato original aprobado | PASS, sin cambios |
| Completion Gate productivo reejecutado read-only | COMPLETED |
| Gate de revalidación con tests/build/Reviewer nuevos vinculados al resultado actual | COMPLETED |
| Cleanup e integridad | PASS |
| Revisión humana final NUEVA | PENDING |

El evaluador productivo se ejecutó sin cambiar su código ni sobrescribir los receipts históricos del run. Por ello conserva la lectura de roles/checks históricos. COMPLETION-REVALIDATION.json exige ADEMÁS los17 tests/build originales recién ejecutados, artefactos exactos y Reviewer nuevo ACCEPTED sobre el conjunto actual de archivos; ningún resultado anterior sustituye esas comprobaciones nuevas. El resultado es una revalidación documental, no un nuevo E2E ni una extensión del run original.

El Reviewer fue invocado por scripts/invoke-hermes-role.ps1 con perfil read-only y contrato SHA; inferencia serializada mediante el mutex productivo. Se mantuvieron qwen36/127.0.0.1:8080/ctx65536/parallel1, sin actualizaciones ni dependencias nuevas. Se cerró únicamente el modelo propio de esta validación; puertos8080/9119 libres, tres mutex libres, Chrome preexistente preservado.

No se repitieron F24/F25/4H/F26, no hubo consulta ChatGPT, no se ejecutó auditoría/regresión final, no se ejecutó F28 y no hubo push. F28_ORIGINAL_6_8H=WAIVED_BY_USER; F28_NOT_EXECUTED=TRUE. Falta exclusivamente la nueva aprobación humana para cerrar F27; la regresión/auditoría final sigue pendiente de esa aprobación.

Reviewer session: 20261015_180841_072af5. Revalidación completa: 187.05s. Evidence: evidence/f27-documentation-revalidation-20261015-180725/.

## Diff documental exacto

```diff
--- a/README.md
+++ b/README.md
@@ -19,8 +19,8 @@
 >>> from module import round_seconds
 >>> round_seconds('1.005')   # string → Decimal preserves exactness
 '1.01'
->>> round_seconds(1.005)     # float loses precision before Decimal sees it → floor
-'1.00'
+>>> round_seconds(1.005)     # Decimal(str(value)) preserves this value
+'1.01'
 ```

 The canonical approach is to pass the **string** directly to `Decimal(str(value))` so `1.005` is rounded up to `1.01` as expected.
@@ -91,7 +91,7 @@
 >>> s = summarize(recs)
 >>> s['counts']
 {'PASS': 1, 'FAIL': 1, 'BLOCKED': 1, 'TIMEOUT': 1}
->>> s['total_seconds']   # 0.105 + 2.675 + 0 + 1.005 = 3.785 → 3.79
+>>> s['total_seconds']   # Sum normalized values: 0.11 + 2.68 + 0.00 + 1.01 = 3.80
 '3.80'
 >>> s['max_seconds']     # 2.675 → 2.68
 '2.68'
@@ -178,8 +178,8 @@
 Always pass **strings** to `Decimal()` to avoid float precision loss:

 ```python
->>> Decimal(str(1.005))   # float loses precision first → '1.00499...'
-Decimal('1.00499999999999989341858963598497211933135986328125')
+>>> Decimal(str(1.005))   # str(1.005) is '1.005'
+Decimal('1.005')
 >>> Decimal('1.005')      # string preserves exact value
 Decimal('1.005')
 ```
```

- [README corregido](<C:/Users/Pc/Documents/Proyectos Tech/Desarrollador autonomo/sandbox/endurance-f27-20261015-165308-d37c78/pilot-002/README.md>)
- [Código intacto](<C:/Users/Pc/Documents/Proyectos Tech/Desarrollador autonomo/sandbox/endurance-f27-20261015-165308-d37c78/pilot-002/module.py>)
- [17 tests originales](<C:/Users/Pc/Documents/Proyectos Tech/Desarrollador autonomo/evidence/f27-documentation-revalidation-20261015-180725/tests.stderr.txt>)
- [Resultado Reviewer](<C:/Users/Pc/Documents/Proyectos Tech/Desarrollador autonomo/evidence/f27-documentation-revalidation-20261015-180725/REVIEWER-VALIDATION.json>)
- [Completion revalidation](<C:/Users/Pc/Documents/Proyectos Tech/Desarrollador autonomo/evidence/f27-documentation-revalidation-20261015-180725/COMPLETION-REVALIDATION.json>)
- [Cleanup](<C:/Users/Pc/Documents/Proyectos Tech/Desarrollador autonomo/evidence/f27-documentation-revalidation-20261015-180725/CLEANUP.json>)
- [Integridad](<C:/Users/Pc/Documents/Proyectos Tech/Desarrollador autonomo/evidence/f27-documentation-revalidation-20261015-180725/INTEGRITY.json>)
- [Nuevo paquete de revisión humana pendiente](<C:/Users/Pc/Documents/Proyectos Tech/Desarrollador autonomo/evidence/f27-documentation-revalidation-20261015-180725/HUMAN-REVIEW-PACKAGE.json>)
