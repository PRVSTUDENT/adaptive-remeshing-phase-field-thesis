import hashlib
import json
from pathlib import Path

repo = Path(__file__).resolve().parent.parent.parent

files = [
    "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/candidate_donor_h0025_visual.inp",
    "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/f42_mixed_uel.for",
    "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/job_notifications.sh",
    "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/submit_M1_CANDIDATE_DONOR_H0025_VISUAL.pbs",
    "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/PACKAGE_MANIFEST.json",
    "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/CANDIDATE_DONOR_H0025_VISUAL_AUTHORIZATION.json",
    "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/MODE1_DONOR_H0025_VISUAL_PREFLIGHT_REPORT.json",
    "tests/unit/test_mode1_f1597_package76_donor_visual.py"
]

evidence = {}
for rel in files:
    p = repo / rel
    assert p.is_file(), f"Missing file: {p}"
    h = hashlib.sha256(p.read_bytes()).hexdigest().upper()
    evidence[rel] = h

finding = (
    "Constructed and qualified Package 76 instrumented Mode-I candidate donor calculation "
    "(1600 quads, h=2.5 um, u_top=0.0050 mm) under bitwise frozen production UEL f42_mixed_uel.for. "
    "Resolved ODB field omission by configuring DUMMY_MAT with *User Material constants=3 (210.0, 0.3, 1600.0) "
    "and *Depvar 20 on Layer 3 CPE4 overlay (elements 3201..4800), requesting SDV, S, E output at frequency=1 "
    "to capture full pointwise damage d and integration-point history H directly in the donor ODB. "
    "Technical preflight passed with datachecks=PASS_BOTH (exit code 0, ANALYSIS DATACHECK COMPLETE) and "
    "job successfully submitted to PBS scheduler as Job ID 1416301.mmaster02. "
    "Method C Gate C1-1 remains FAILED pending verified receiver continuity."
)

checkpoint = {
    "schema": 1,
    "status": "PREPARATION_COMPLETE",
    "task": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
    "turn": "8410b808-6a0c-4b56-8391-bf7235e59a7d",
    "classification": "QUALIFIED_DONOR_SUBMITTED_SDV_INSTRUMENTED",
    "finding": finding,
    "pbs_job_id": "1416301.mmaster02",
    "gate_c1_1_status": "FAILED",
    "verification_passed": True,
    "evidence_sources": evidence
}

out_path = repo / "results" / "validation" / "preparation-8410b808-6a0c-4b56-8391-bf7235e59a7d.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(checkpoint, indent=2) + "\n", encoding="utf-8")
print(f"Written checkpoint to {out_path}")
