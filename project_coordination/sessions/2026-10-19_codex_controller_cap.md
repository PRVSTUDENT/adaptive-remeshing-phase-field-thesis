# Controller scientific timeout cap

User requested increasing the 600-second cap. No matching live Antigravity/controller process was found. Recovered the stale gemini-antigravity F1596 lock under the explicit user instruction to fix it; original lock preserved below. Scientific task state and all unrelated dirty paths preserved.

Changed installed controller default ScientificTurnSeconds from 600 to 2400 and validation maximum from 1800 to 86400. Requested PrintTimeout remains bounded by this configurable cap. Watchdog retains its 60-second grace. No research run or HPC submission launched.

Installed controller SHA256: f5ff2c979b094ba9690839a408bfe636b56593c712f94217b22c872b9dd3b087

Original session:
```json
{
  "active": true,
  "agent": "gemini-antigravity",
  "task_id": "F1596-INDEPENDENTLY-QUALIFY-PACKAGE72-STATE-TRANSFER",
  "starting_commit": "693b7211cad4ae7d57c76cd7e655696a55b25af2",
  "allowed_write_scope": [
    "project_coordination/ACTIVE_SESSION.json",
    "project_coordination/ACTIVE_TASK.json",
    "project_coordination/TASK_LEDGER.csv",
    "project_coordination/HPC_JOB_LEDGER.csv",
    "project_coordination/ARTIFACT_REGISTRY.csv",
    "project_coordination/sessions/**",
    "scripts/postprocessing/**",
    "scripts/validation/**",
    "models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/**",
    "tests/unit/**"
  ],
  "claimed_at": "2026-10-19T16:38:00+02:00",
  "last_updated": "2026-10-19T17:14:00+02:00",
  "last_released": "2026-10-19T16:31:00+02:00"
}

```

Validation: full installed PowerShell AST parses without errors; default 2400 and range 60..86400 verified; budget cases 2400/2400, 2400/120 and 3600/3600 pass. Initial test incorrectly accessed AST .Value; corrected to .Extent.Text (test issue only).
