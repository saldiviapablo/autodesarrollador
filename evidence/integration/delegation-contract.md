# Contrato de Delegación Estructurada (Hermes ↔ Qwen Code)

**Macrofase:** 4 — Integración y Serialización  
**Versión:** 1.0  
**Schemas:**
- `schemas/delegation-request.schema.json`
- `schemas/delegation-result.schema.json`

---

## 1. Principio de Diseño

Para garantizar determinismo y evitar la fragilidad de interpretar prosa libre entre agentes de IA:

1. **Hermes Supervisor** emite sus requerimientos exclusivamente en formato JSON estructurado validado contra `DelegationRequest`.
2. **Qwen Code Worker** consume el contrato, opera bajo límites de workspace y emite un resultado estructurado validado contra `DelegationResult`.
3. **Serialización Absoluta:** Ambos agentes adquieren el `InferenceLock` mediante exclusión mutua cross-process. Jamás operan en inferencia al mismo tiempo (`--parallel 1`).

---

## 2. Esquema de Solicitud: `DelegationRequest`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "DelegationRequest",
  "type": "object",
  "required": [
    "schema_version",
    "delegation_id",
    "objective",
    "workspace",
    "task",
    "acceptance_criteria",
    "allowed_actions",
    "forbidden_actions",
    "status"
  ],
  "properties": {
    "schema_version": { "type": "string", "enum": ["1.0"] },
    "delegation_id": { "type": "string", "pattern": "^del-[a-zA-Z0-9_-]+$" },
    "objective": { "type": "string" },
    "workspace": { "type": "string" },
    "task": { "type": "string" },
    "acceptance_criteria": { "type": "array", "items": { "type": "string" } },
    "allowed_actions": { "type": "array", "items": { "type": "string" } },
    "forbidden_actions": { "type": "array", "items": { "type": "string" } },
    "tests": { "type": "array", "items": { "type": "string" } },
    "context": { "type": "object" },
    "status": { "type": "string", "enum": ["READY", "IN_PROGRESS", "COMPLETED", "REJECTED"] }
  }
}
```

---

## 3. Esquema de Resultado: `DelegationResult`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "DelegationResult",
  "type": "object",
  "required": [
    "schema_version",
    "delegation_id",
    "status",
    "summary",
    "files_changed",
    "tests",
    "commands",
    "errors",
    "needs_review"
  ],
  "properties": {
    "schema_version": { "type": "string", "enum": ["1.0"] },
    "delegation_id": { "type": "string", "pattern": "^del-[a-zA-Z0-9_-]+$" },
    "status": { "type": "string", "enum": ["SUCCESS", "FAILED", "BLOCKED", "REJECTED", "TIMEOUT"] },
    "summary": { "type": "string" },
    "files_changed": { "type": "array", "items": { "type": "string" } },
    "tests": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["command", "status", "exit_code"],
        "properties": {
          "command": { "type": "string" },
          "status": { "type": "string", "enum": ["PASS", "FAIL", "SKIPPED"] },
          "exit_code": { "type": "integer" },
          "output": { "type": "string" }
        }
      }
    },
    "commands": { "type": "array", "items": { "type": "string" } },
    "errors": { "type": "array", "items": { "type": "string" } },
    "needs_review": { "type": "boolean" },
    "review_notes": { "type": "string" }
  }
}
```
