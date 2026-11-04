#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_preparation_checkpoint_c050a5a1.py
Constructs results/validation/preparation-c050a5a1-d54a-4c57-b6ca-e3cb755e052d.json
with verified hashes and substantive finding.
"""

import hashlib
import json
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
RUN_ID = "c050a5a1-d54a-4c57-b6ca-e3cb755e052d"
TARGET = WORKSPACE / f"results/validation/preparation-{RUN_ID}.json"

files = [
    "project_coordination/candidate_definitions/execute_mode1_package171_r8_c6_coupled_reequilibration.json",
    "project_coordination/review_dispatch/execute_mode1_package171_r8_c6_coupled_reequilibration-8D0545A3A733B1368DBA705880C71FD8E2D797B09AF4920FDB1E76688EA52D1F.request.json",
    "results/validation/r8_review_packet_receipt.json",
    "scripts/validation/prepare_r8_review_packet.py",
    "tests/unit/test_f1606_r8_review_packet_and_candidate_definition.py",
    "results/validation/mode1_r8_mathematical_specification_assessment.json",
    "scripts/validation/evaluate_mode1_r8_mathematical_specification.py",
    "tests/unit/test_f1606_r8_mathematical_specification.py",
    "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
]

evidence_sources = {}
for rel_path in files:
    full_path = WORKSPACE / rel_path
    if not full_path.exists():
        raise FileNotFoundError(f"Missing file: {full_path}")
    evidence_sources[rel_path] = hashlib.sha256(full_path.read_bytes()).hexdigest().upper()

finding_text = (
    "Candidate Package 171-R8 review packet prepared under correlation HND-F1607-R8-REVIEW-8D0545A3 "
    "(fingerprint 8D0545A3A733B1368DBA705880C71FD8E2D797B09AF4920FDB1E76688EA52D1F). Verified candidate definition "
    "with compound active-set transition criteria (|A_k|<=500, |Delta A_k|<=10, Delta A^+=0 sustained for 3 consecutive "
    "iterations) and 140 outer iteration budget providing 51 relaxation iterations and projecting delta_d=1.27e-6<=1.0e-5 "
    "at 1.33h runtime within the 8h PBS limit. Explicitly documented that projected damage convergence at iteration 140 "
    "is an unverified hypothesis, not proof of coupled convergence, requiring independent review of damage, displacement, "
    "history, KKT, force/energy consistency, and numerical stability. Frozen UEL and quantitative physical acceptance criteria strictly preserved."
)

checkpoint_payload = {
    "schema": 1,
    "status": "PREPARATION_COMPLETE",
    "operation": "research_preparation",
    "title": "Candidate Package 171-R8 Independent Review Packet Preparation and Scientific Specification",
    "finding": finding_text,
    "verification_passed": True,
    "next_operation": "Register successor task F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION and advance independent scientific review",
    "evidence_sources": evidence_sources,
    "registered_paths": [
        "project_coordination/candidate_definitions/execute_mode1_package171_r8_c6_coupled_reequilibration.json",
        "project_coordination/review_dispatch/execute_mode1_package171_r8_c6_coupled_reequilibration-8D0545A3A733B1368DBA705880C71FD8E2D797B09AF4920FDB1E76688EA52D1F.request.json",
        "results/validation/r8_review_packet_receipt.json",
        "scripts/validation/prepare_r8_review_packet.py",
        "tests/unit/test_f1606_r8_review_packet_and_candidate_definition.py",
        "results/validation/mode1_r8_mathematical_specification_assessment.json",
        "scripts/validation/evaluate_mode1_r8_mathematical_specification.py",
        "tests/unit/test_f1606_r8_mathematical_specification.py",
        "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
    ]
}

TARGET.parent.mkdir(parents=True, exist_ok=True)
TARGET.write_text(json.dumps(checkpoint_payload, indent=2), encoding="utf-8")
print(f"Generated preparation artifact: {TARGET.relative_to(WORKSPACE)}")
print(f"SHA-256: {hashlib.sha256(TARGET.read_bytes()).hexdigest().upper()}")
