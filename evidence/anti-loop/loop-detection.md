# Evidencia: DetecciÃ³n y PrevenciÃ³n de Bucles Repetidos (Section 38)

- **Regla:** MÃ¡ximo 3 fallos idÃ©nticos (max_same_failure = 3).
- **Ciclo 1:** AcciÃ³n = 
`RETRY`
 (Primer fallo detectado)
- **Ciclo 2:** AcciÃ³n = 
`NEW_APPROACH`
 (Fallo repetido, cambia enfoque)
- **Ciclo 3:** AcciÃ³n = 
`WEB_RESEARCH`
 (**ESCALAMIENTO ACTIVADO**: InvestigaciÃ³n Web requerida)
- **Ciclo 4 (Con Avance Real):** AcciÃ³n = 
`CONTINUE`
 (Contador reiniciado a 0)
- **GarantÃ­a:** El sistema nunca ejecuta el mismo fallo indefinidamente.
