# Evidencia: Escalera de Escalamiento Determinista (Section 40)

| Nivel | CondiciÃ³n Disparadora | AcciÃ³n Recomendada | Estado |
| :---: | :--- | :--- | :---: |
| 1 | 1er fallo | 
`RETRY`
 | IN_PROGRESS |
| 2 | 2do fallo idÃ©ntico | 
`NEW_APPROACH`
 | IN_PROGRESS |
| 3 | 3 fallos idÃ©nticos | 
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

- **LÃ­mite Absoluto:** Ciclo 20 detiene la ejecuciÃ³n inmediatamente con estado STALLED.
