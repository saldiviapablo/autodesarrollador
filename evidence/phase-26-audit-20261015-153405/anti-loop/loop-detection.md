# Evidencia: Detección y Prevención de Bucles Repetidos (Section 38)

- **Regla:** Máximo 3 fallos idénticos (max_same_failure = 3).
- **Ciclo 1:** Acción = 
`RETRY`
 (Primer fallo detectado)
- **Ciclo 2:** Acción = 
`NEW_APPROACH`
 (Fallo repetido, cambia enfoque)
- **Ciclo 3:** Acción = 
`WEB_RESEARCH`
 (**ESCALAMIENTO ACTIVADO**: Investigación Web requerida)
- **Ciclo 4 (Con Avance Real):** Acción = 
`CONTINUE`
 (Contador reiniciado a 0)
- **Garantía:** El sistema nunca ejecuta el mismo fallo indefinidamente.
