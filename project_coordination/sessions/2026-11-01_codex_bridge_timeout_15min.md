# Bridge response timeout

Changed the supervisor default from 2 to 15 minutes and the ordinary controller bridge default to 900 seconds. Deployed both canonical scripts to OpenClawPAD; SHA256 pairs match:

- Antigravity-Autonomous-Loop.ps1: 0A209A80AFF903B510CC119E3E297DCE0E03E7A525B7498B6425B6CCDC559BE4
- Controller-Supervisor.ps1: 4AE293A371289CA6A998EF7E296C9465F0CD7065D0FADB6C729A27AFE63AC494

All 11 existing supervisor regression checks and PowerShell syntax checks pass. This changes future invocations; an already-running poll retains its original timeout. No controller restart, live handoff retry or PBS submission was performed. Existing pending handoffs and checkpoints are preserved. Live acceptance remains unverified.
