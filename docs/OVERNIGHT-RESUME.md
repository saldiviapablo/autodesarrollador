# Overnight continuation

```json
{
  "schema_version": "1.0",
  "kind": "MAINTENANCE_ORCHESTRATION_NOT_RUN_STATE",
  "authorization": "2026-10-15 overnight user attachment 6bd9a034-9a1e-4e7e-b13b-7d840198a9f4",
  "last_completed": "F24 ATTEMPT8 FAIL",
  "active_phase": "F24_DIAGNOSIS",
  "last_cause": "Reviewer instruction/data boundary; native transport and role verified correct",
  "last_fix": "Readonly evidence envelope, SHA input binding and strict single decision parser; isolated native Reviewer ACCEPTED",
  "last_commit": "7e0be80ebc31a46e185e406b5f2c5208f5cfe343",
  "next_action": "Preserve and isolate new failure before another clean attempt",
  "run_pointer": "C:\\Users\\Pc\\Documents\\Proyectos Tech\\Desarrollador autonomo\\sandbox\\f24-attempt8-bd7004d5\\project\\.autopilot",
  "updated_at": "2026-10-15T06:07:39.301159+00:00",
  "no_push": true,
  "new_failures": [
    "REVIEWER_INSTRUCTION_DATA_BOUNDARY",
    "NONFINITE_NUMERIC_ACCEPTANCE_COVERAGE"
  ],
  "fixes": [
    "REVIEWER_CONTRACT_CERTIFIED",
    "NONFINITE_ORACLE_EXPANDED_BEFORE_NEW_START"
  ],
  "run_id": "run-20261015-025148",
  "consultation_id": "f24-a8-b948a7b3279b41ef89ccabd327cb79b6",
  "harness_session_id": 20208,
  "auxiliary_tool_sessions": {
    "first_segment_observer": 37499,
    "browser_readonly_observer": 69383
  }
}
```

F25 real2h →4h →F26 →F27 dedicated local pilot →F28 real6–8h →final audit. No push. Native STATE remains authoritative for each run; orchestration metadata does not replace it. All historical attempts remain unchanged.
