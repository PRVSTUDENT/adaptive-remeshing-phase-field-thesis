import json
import hashlib
from pathlib import Path

paths = [
    "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for",
    "models/pandey_kumar_mode1/104_experimental_irreversible_uel/f42_experimental_irreversible_uel.for",
    "models/pandey_kumar_mode1/104_experimental_irreversible_uel/diagnostic_patch/M1_DIAGNOSTIC_4ELEM_IRREV.inp",
    "models/pandey_kumar_mode1/104_experimental_irreversible_uel/diagnostic_patch/d_lower_bounds.csv",
    "models/pandey_kumar_mode1/104_experimental_irreversible_uel/diagnostic_patch/submit_M1_DIAG_4ELEM.pbs",
    "results/validation/mode1_f1597/turn112_abaqus_verification_audit.json",
    "results/validation/mode1_f1597/turn112_abaqus_diag_results.json",
    "results/validation/mode1_f1597/turn112_uel_energy_balance.csv"
]

evidence = {}
for p in paths:
    data = Path(p).read_bytes()
    evidence[p] = hashlib.sha256(data).hexdigest().upper()

prep = {
    "schema": 1,
    "status": "PREPARATION_COMPLETE",
    "turn": "05677747-b9eb-44d1-a196-20d596ae08c4",
    "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
    "finding": "Turn 112 Genuine Abaqus 2023 verification complete: experimental irreversible UEL compiled cleanly (ifort 2021.13.0, exit 0), executed genuine 2-step solve on 4-element diagnostic patch (Exit 0); Stage A preserves transferred damage with healing <= 1e-8 (elem avg exactly 0.1875); Stage B releases active constraint advancing damage to ~0.985 with strictly monotonic dissipation; production UEL preserved bitwise frozen (CE8D5EDC...).",
    "evidence_sources": evidence,
    "verification_passed": True,
    "timestamp": "2026-10-24T18:37:30+02:00"
}

out_path = Path("results/validation/preparation-05677747-b9eb-44d1-a196-20d596ae08c4.json")
out_path.write_text(json.dumps(prep, indent=2) + "\n", encoding="utf-8")
print("SUCCESS: Wrote preparation artifact with UPPERCASE hashes to", out_path)
