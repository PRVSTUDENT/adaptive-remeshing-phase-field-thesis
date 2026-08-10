#!/usr/bin/env python3
"""Pair-2 Common Preflight Validator for M2REF_H1_FRACFIX and M2REF_H2_FRACFIX.

Validates BOTH jobs before either can be authorized or submitted:
1. Exact physical element counts (H1 = 12,064; H2 = 33,852)
2. UEL SHA256 matches 0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8
3. Explicit #PBS -m abe notification contract with exact 2 approved recipients
4. Raw SHA256 execution hashes freeze
5. Preflight read-only integrity.
"""

import sys
import os
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EXPECTED_HASHES = {
    "M2REF_H1_FRACFIX": {
        "n_phys": 12064,
        "inp": "407f88694d35d86bdc321d090c0678f6c9a348a462249690b4ac2c06d708f10c",
        "uel": "0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8",
        "pbs": "80c1a509a621c8e6a66a03174a3c1890303b3f137365d3bd01603b9b0fa6373d",
        "sh":  "2d354ec6e00e09657b867d36fcadde69269f09c78b6e10dea537679d3d5c57a3",
        "memory": "8 GB",
        "walltime": "02:00:00",
    },
    "M2REF_H2_FRACFIX": {
        "n_phys": 33852,
        "inp": "c9a3f496cf2cb0daa455cfae31f5bd699b56f3b410f0a7f2a12014b2718be5b0",
        "uel": "0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8",
        "pbs": "f7040080f6efd80619b32eece2f52c047ab21894fc304b39c15937fa9e2d19f3",
        "sh":  "dd3f85dcc62fe855f965a1a58478228d032a394b9f61573a240bd8fc8ca66053",
        "memory": "8 GB",
        "walltime": "04:00:00",
    }
}

APPROVED_RECIPIENTS = {
    "Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de",
    "pr21vyci@mailserver.tu-freiberg.de"
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_pair2_preflight():
    errors = []
    base_dir = ROOT / "models/generated/mode_ii/reference_convergence"

    for case_name, exp in EXPECTED_HASHES.items():
        pkg_dir = base_dir / case_name
        if not pkg_dir.exists():
            errors.append(f"Package directory {pkg_dir} missing")
            continue

        inp_path = pkg_dir / f"{case_name}.inp"
        uel_path = pkg_dir / "f42_mixed_uel.for"
        pbs_path = pkg_dir / f"{case_name}.pbs"
        sh_path  = pkg_dir / f"submit_{case_name.lower()}.sh"
        man_path = pkg_dir / "PACKAGE_MANIFEST.json"

        for p in [inp_path, uel_path, pbs_path, sh_path, man_path]:
            if not p.exists():
                errors.append(f"Required file {p.name} in {case_name} missing")

        if errors:
            continue

        # Check raw hashes
        inp_h = sha256_file(inp_path)
        uel_h = sha256_file(uel_path)
        pbs_h = sha256_file(pbs_path)
        sh_h  = sha256_file(sh_path)

        if inp_h != exp["inp"]:
            errors.append(f"{case_name} INP hash mismatch: {inp_h} != {exp['inp']}")
        if uel_h != exp["uel"]:
            errors.append(f"{case_name} UEL hash mismatch: {uel_h} != {exp['uel']}")
        if pbs_h != exp["pbs"]:
            errors.append(f"{case_name} PBS hash mismatch: {pbs_h} != {exp['pbs']}")
        if sh_h != exp["sh"]:
            errors.append(f"{case_name} SH hash mismatch: {sh_h} != {exp['sh']}")

        # Validate notification contract
        mail_points = None
        recipients = []
        for line in pbs_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("#PBS -m "):
                mail_points = line.split(None, 2)[2].strip()
            elif line.startswith("#PBS -M "):
                raw_recips = line.split(None, 2)[2].strip()
                recipients.extend([r.strip() for r in raw_recips.split(",") if r.strip()])

        if mail_points != "abe":
            errors.append(f"{case_name} PBS mail points must be 'abe', found {mail_points!r}")

        if len(recipients) != 2:
            errors.append(f"{case_name} PBS recipient count must be 2, found {len(recipients)}")

        if set(recipients) != APPROVED_RECIPIENTS:
            errors.append(f"{case_name} PBS recipients {set(recipients)} mismatch approved set")

        # Validate manifest contents
        manifest = json.loads(man_path.read_text(encoding="utf-8"))
        if manifest.get("physical_element_count") != exp["n_phys"]:
            errors.append(f"{case_name} manifest physical_element_count {manifest.get('physical_element_count')} != {exp['n_phys']}")

    if errors:
        print("=== Pair-2 Preflight FAIL ===")
        for e in errors:
            print("  ERROR: " + e)
        return False, errors

    print("=== Pair-2 Preflight PASS ===")
    print("  M2REF_H1_FRACFIX: NPHYS=12064, Hash Match PASS, #PBS -m abe PASS")
    print("  M2REF_H2_FRACFIX: NPHYS=33852, Hash Match PASS, #PBS -m abe PASS")
    return True, []


if __name__ == "__main__":
    ok, errs = validate_pair2_preflight()
    sys.exit(0 if ok else 1)
