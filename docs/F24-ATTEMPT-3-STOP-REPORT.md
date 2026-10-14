# F24 ATTEMPT 3 — STOP por entrega ambigua

F24 = FAIL / BLOCKED_REQUIRES_HUMAN. No se reenvió la consulta ni se inició F25.

ATTEMPT 2, run-20261014-020920, queda clasificado externamente como FAIL /
GLOBAL_TIMEOUT. Los 216 archivos preservados mantienen sus bytes: sandbox,
STATE, Git interno, evidencias, contrato, plan, aprobación, deadline y contadores.
Su STATE histórico no fue reescrito para cambiar esa clasificación.

El nuevo run es run-20261014-143502, en sandbox/f24-attempt3-f79dd822/project.
Prepare, preflight y aprobación única nativos precedieron al START real mediante
INICIAR-DESARROLLADOR-AUTONOMO.bat. Contrato y plan nuevos; mismo objetivo,
task y criterios aprobados. global_timeout_seconds=2700, fase=300s,
restart_budget=2 y max_cycles=5. El reloj nativo permanece intacto.

Antes de START existían 13 tests inmutables, incluidos estos casos:

| Caso | Resultado exigido | Test final nativo |
|:---|:---|:---|
| allocate("1.00", [0,1]) | ["0.00", "1.00"] | PASS |
| allocate("-1.00", [1]) | ValueError | PASS |
| allocate("1.00", [-1,2]) | ValueError | PASS |
| allocate("1.00", [0,0]) | ValueError | PASS |
| allocate("1.00", [1]) | ["1.00"] | PASS |

La suite conserva redondeo, total sin redondear precios antes de multiplicar,
largest remainder y desempate por índice, conservación de centavos en 100 casos,
validación de valores y README. Los hashes de tests/build aprobados no cambiaron.
Codex creó el fixture deliberadamente incompleto; únicamente Qwen Code modificó
la implementación objetivo y README después de START.

Qwen ejecutó el FAIL inicial, diagnosticó y corrigió varias veces. Las dos primeras
invocaciones alcanzaron su timeout normal. Runner conservó sus resultados,
reconcilió el diff y consumió exactamente dos reinicios permitidos. El segundo
Worker ya obtuvo 13/13 PASS antes de expirar; el tercero devolvió SUCCESS.
Runner verificó unit/build PASS, creó checkpoint y recibió un único crash
controlado de su parent propio. Watchdog registró PARENT_CRASH_RECOVERED.
No se ejecutó el START-Recover posterior al bloqueo ChatGPT.

Web obtuvo realmente HTTP 200 de https://docs.python.org/3/library/decimal.html.
Se conservan el fetch inicial y otro posterior al diagnóstico. La lectura de
WEB.json por Worker NO está demostrada: su glob ignoró .autopilot y su respuesta
afirmó erróneamente que el archivo no existía. Las tres sesiones persistidas no
contienen una lectura efectiva de WEB.json. Fetch PASS no certifica consumo de
la investigación ni cumplimiento completo del task.

Antes de START se respaldó el bridge y se sustituyó su primer click sintético
por el mismo par físico único mousePressed/mouseReleased que la ruta humana.
Se exige un botón único visible/habilitado y SHA del composer; intent se guarda
antes del click. No hay fallback ni segundo envío. Pruebas deterministas de
transporte (4), domain lock (13), idempotencia (8) y reconciliación humana (41)
PASS. Ledger y reconciliación automática conservaron su código. Esta prueba
real no certifica entrega exitosa del transporte.

Consulta nueva: f24-a3-run-20261014-143502-bfca6e98.
Baseline 2/2 persistido antes de DELIVERY_INTENT; conversación registrada:
https://chatgpt.com/c/6acefadc-36b8-83e8-9172-7e3e9421dc21.
Prompt normalizado SHA-256:
a559513c2d75b9e090bd58af11569a70c9c6f15627ab4a6cc500b949cf788032.
El prompt exacto reconstruido desde la fuente coincide con ese hash.

El deadline del transporte padre expiró. El estado persistido conserva
DELIVERY_INTENT, send_attempts=1; el mecanismo normal devuelve UNKNOWN_DELIVERY,
no_resend=true. No se confirmó user +1 / assistant +1, respuesta ni composer
vacío. No se infiere que hubo entrega a partir del intento. El ledger quedó
intacto después del STOP. No se ejecutaron reconcile, retry físico, nueva
consulta ni retry lógico COMPLETED. Los IDs anteriores F23/F24 siguen intactos.

Reviewer independiente final y Completion Gate NOT_RUN. No existe COMPLETED ni
se certifica F24 E2E. El reporte nativo terminal es BLOCKED_REQUIRES_HUMAN.

| Medición | Valor |
|:---|---:|
| Duración nativa hasta cierre | 920.52 s (15 min 20.52 s) |
| Setup anterior al reloj | 9.12 s |
| Harness total, incluyendo cleanup | 932.75 s |
| RAM libre mínima | 13.7422 MiB |
| Pagefile usado máximo | 2.5709 GiB |
| VRAM usada máxima, GPU total | 4254 MiB |
| Muestras de recursos | 182 |

Hubo una sola muestra bajo 150 MiB. El umbral de degradación sostenida de tres
muestras consecutivas no se alcanzó; la caída transitoria queda preservada.
No se reemplazaron las métricas anteriores. Llama working set, procesos,
reinicios y todos los samples están en resources-live.json.

Cleanup e integridad PASS: 126 identidades PID/inicio, cero supervivientes;
locks ausentes; mutex Runner e Inference Lock FREE; 8080/9119 libres. Chrome
preexistente PID16576 permanece abierto en su perfil dedicado. Los 24 bindings
de la aprobación, reloj, hashes protegidos, modelo y llama.exe coinciden.
Hermes productivo sigue v0.21.6 / 818c13be1dc4fd28987e1e881a9408224afd4535.
qwen36 / 127.0.0.1:8080 / ctx65536 / parallel1 intactos. F23 conserva PASS,
sus 11 componentes protegidos y 40 evidencias históricas.

Chrome instalado 155.0.8059.41 difiere del snapshot de VERSIONS.lock; esta deriva
ya estaba documentada antes del intento. No se actualizó Chrome, el lock,
Hermes ni ninguna dependencia. No hay dependencias nuevas.

Evidencia: evidence/phase-24-attempt-3-20261014/. Incluye manifiestos de
preservación, preparación/aprobación, tests inmutables, fallos y trazas Qwen,
artefactos producidos, checks nativos, checkpoint/Watchdog, consulta pendiente,
clock, STATE/report terminal, recursos y cleanup. Copias exactas de 60 archivos
están identificadas en artifact-manifest.json. Backups locales en
backups/f24-attempt3-preflight-20261014/.

Git: cambios y evidencia en commit local separado; NO PUSH. Ninguna fase
posterior ejecutada. READY_FOR_F25 = NO.
