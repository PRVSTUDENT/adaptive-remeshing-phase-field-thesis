# Smart account switching restored

User requested configuration repair only and will start the loop manually. Set EnableSmartAgyProfileSelection default to true in C:/Users/pruth/OpenClawPAD/Antigravity-Autonomous-Loop.ps1. Existing smart-mode initialization enables startup selection, low-quota rotation, and rotation on actual quota errors. Removed account1 pin from controller_recovery_20261019.ps1 and explicitly enabled smart selection with per-turn quota checks and 20% threshold. Reproducible patch: scripts/validation/controller_smart_switch.patch.

Validation: parsed both scripts with PowerShell AST parser, zero errors; static assertions confirmed smart default and removal of recovery profile pin. No controller, AGY, quota query, account switch, SSH or scheduler operation executed. Runtime account availability is not claimed. Pre-existing dirty paths preserved. Session released before user launch.
