# Bridge research-priority repair - 15 November 2026

User explicitly requested workflow repair without disturbing the running AGY CLI.
Maintenance scope: bridge publisher/helper/policy, AGY rule entrypoints and isolated offline tests.
AGY session ownership, ACTIVE_TASK, ledgers, numerical source, solver evidence, PBS, running processes and live handoff files were not modified by this maintenance.

## Changes

- One canonical Method A/native recovered-stress MISESERI policy, applied to structured requests too.
- Explicit numerical purpose, native-versus-damage/synthetic provenance and causal-cutoff declarations.
- Hash-bound canonical rules; scope/embedded-priority conflicts reject before publication.
- CorrelationId compatibility alias; durable HND header validation and one PAD consumer.
- Strict outer/inner response identity/status/freshness checks; no catch-and-accept raw fallback.
- Browser code-block innerText representations accepted only as one JSON object.
- Invalid/pending transactions preserved for reconciliation; no automatic resubmission.
- Obsolete startup Method C directive marked historical; static instructions override stale roadmap.

## Verification and limits

49 isolated PowerShell checks PASS, including actual wrapper publication/response in TEMP with mocked response delivery and process launch denied. No live model/PAD/SSH/PBS call was made.
Initial idempotence test exposed a duplicate policy-hash line; fixed and rerun. A test fixture referencing a removed heading was updated, then the complete suite passed.
This establishes transport/control behavior only. Contract declarations do not prove numerical causality, native field provenance, whole-suite regeneration or authenticated scientific acceptance. F1793 remains AGY work; its existing request/lock was preserved.
No running CLI or bridge process was restarted or signalled. The already-loaded in-flight exchange retains its request snapshot; disk changes govern subsequent loads.

## SHA-256

| File | SHA-256 |
|---|---|
| .agents/scripts/Invoke-ChatGPTBridge.ps1 | bb427ee84796f0bf2e6b288bb3dfa9f936dd531e934ae69631e0c2136c371ede |
| .agents/scripts/Bridge-ResearchContract.ps1 | 4e115da0f2eebb8c86c33eed92125c9004242c6e3d59286dcbb19e760efd29ca |
| .agents/scripts/bridge_research_policy.json | 4173f9d1497b1d20a9a0f44ebf0a19f4343210fab40242058f85abeaca7b3fe8 |
| .agents/scripts/bridge_rules.txt | d017a2af8cf8fcc03510ad7099f02828cbf5a4cd67ec9afe62459b5d0ce0005e |
| tests/unit/test_bridge_research_contract.ps1 | 9aa793a6be5844011c75726e8064e107088f18830edd04386ad5825cfd50e20d |
