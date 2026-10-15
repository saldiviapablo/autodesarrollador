# Evidencia: Escalera de Escalamiento Determinista (Section 40)

| Nivel | Condición Disparadora | Acción Recomendada | Estado |
| :---: | :--- | :--- | :---: |
| 1 | 1er fallo | 
`RETRY`
 | IN_PROGRESS |
| 2 | 2do fallo idéntico | 
`NEW_APPROACH`
 | IN_PROGRESS |
| 3 | 3 fallos idénticos | 
`WEB_RESEARCH`
 | ESCALATING |
| 4 | Fallo persiste post-web | 
`CHATGPT_CONSULT`
 | ESCALATING |
| 5 | Fallo persiste post-ChatGPT | 
`NEW_SESSION`
 | ESCALATING |
| 6 | Agotamiento de recursos | 
`BLOCKED_REQUIRES_HUMAN`
 | STALLED |

- **Límite Absoluto:** Ciclo 20 detiene la ejecución inmediatamente con estado STALLED.
