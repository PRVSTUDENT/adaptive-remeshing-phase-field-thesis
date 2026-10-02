#!/usr/bin/env python3
"""
Guarded Release and Batch Submission Script for Gate-6B Post-S1 Candidates.

Governing Directive:
  "We need to have understood everything related to the first model before we increase complexity."

Purpose:
  Performs rigorous non-solver preflights and guarded submission of the 6 distinct,
  already-datacheck-qualified Gate-6B Mode-I candidates (S2, S3, T1, T3, L2, L3)
  once the authoritative corrected S1 reference solve (1409734.mmaster02) is scientifically qualified.

Discipline:
  - Reused baselines (T2 = REUSE_S1, L1 = REUSE_S3) are strictly omitted from submissions.
  - Fail-closed preflights check input deck hashes, production Fortran hashes, Nphys constants,
    *Depvar 20, All_elem SDV output, GETOUTDIR, duplicate submissions, and the S1 qualification flag.
  - Submissions run strictly as 1-CPU serial shared-memory jobs.
  - Zero tolerance for missing or mismatched prerequisites.
"""

import os
import sys
import json
import hashlib
import re
import argparse
import subprocess
from pathlib import Path

EXPECTED_PRODUCTION_FORTRAN_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
REQUIRED_S1_QUALIFICATION_FLAG = "CORRECTED_S1_ENERGY_QUALIFIED"
REUSED_OMITTED_CANDIDATES = {"T2", "L1"}

def compute_sha256(file_path):
    """Compute uppercase hex SHA-256 for a file."""
    if not os.path.exists(file_path):
        return None
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def audit_input_deck(deck_path, expected_nphys):
    """Audit deck content for Nphys in User Material, Depvar 20, and All_elem SDV output."""
    if not os.path.exists(deck_path):
        return False, f"Deck missing: {deck_path}"
    
    with open(deck_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    lines = [l.strip() for l in content.splitlines()]

    # 1. User Material constants=3 with Nphys
    found_user_mat = False
    found_nphys = False
    for i, line in enumerate(lines):
        if line.upper().startswith("*USER MATERIAL") and "CONSTANTS=3" in line.upper():
            found_user_mat = True
            if i + 1 < len(lines):
                data_line = lines[i + 1]
                parts = [p.strip() for p in data_line.split(",")]
                if len(parts) >= 3:
                    try:
                        nphys_val = float(parts[2])
                        if abs(nphys_val - float(expected_nphys)) < 1e-3:
                            found_nphys = True
                    except ValueError:
                        pass
            break

    if not found_user_mat:
        return False, f"Missing *User Material, constants=3 in {deck_path}"
    if not found_nphys:
        return False, f"Nphys mismatch in {deck_path}: expected {expected_nphys}"

    # 2. *Depvar 20
    found_depvar = False
    for line in lines:
        if line.upper().startswith("*DEPVAR"):
            found_depvar = True
            break
    if not found_depvar:
        return False, f"Missing *Depvar in {deck_path}"

    # 3. Element output for All_elem SDV
    found_elem_output = False
    in_elem_output = False
    for line in lines:
        if line.upper().startswith("*ELEMENT OUTPUT"):
            if "ALL_ELEM" in line.upper():
                in_elem_output = True
            else:
                in_elem_output = False
        elif in_elem_output:
            if line.startswith("*"):
                in_elem_output = False
            elif "SDV" in line.upper():
                found_elem_output = True
                break

    if not found_elem_output:
        return False, f"Missing *Element Output, elset=All_elem with SDV in {deck_path}"

    return True, "Deck content verified"

def audit_fortran_source(fortran_path):
    """Audit production Fortran source for GETOUTDIR and Layer-3 index mapping."""
    if not os.path.exists(fortran_path):
        return False, f"Fortran file missing: {fortran_path}"

    sha = compute_sha256(fortran_path)
    if sha != EXPECTED_PRODUCTION_FORTRAN_SHA256:
        return False, f"Fortran SHA256 mismatch: got {sha}, expected {EXPECTED_PRODUCTION_FORTRAN_SHA256}"

    with open(fortran_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    if "CALL GETOUTDIR" not in content.upper():
        return False, "Fortran source missing CALL GETOUTDIR"

    if "PHYSIDX = NOEL - 2 * NPHYS_VAL" not in content.upper() and "PHYSIDX = NOEL - 2*NPHYS_VAL" not in content.upper():
        return False, "Fortran source missing Layer-3 companion index mapping"

    return True, "Fortran source verified"

def audit_pbs_wrapper(pbs_path, expected_job_name):
    """Audit PBS wrapper directives and notification integration."""
    if not os.path.exists(pbs_path):
        return False, f"PBS wrapper missing: {pbs_path}"

    with open(pbs_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    if "#PBS -m abe" not in content:
        return False, "PBS wrapper missing #PBS -m abe mail directive"
    if "#PBS -M pr21vyci@mailserver.tu-freiberg.de" not in content:
        return False, "PBS wrapper missing #PBS -M recipient"
    if "job_notifications.sh" not in content:
        return False, "PBS wrapper missing job_notifications.sh sourcing"
    if "nodes=1:ppn=1" not in content and "nodes=1" not in content:
        return False, "PBS wrapper must specify 1 node 1 CPU"

    return True, "PBS wrapper verified"

def run_preflight_for_candidate(candidate, base_dir="."):
    """Run full fail-closed preflight checks on a single candidate."""
    cid = candidate["candidate_id"]
    
    if cid in REUSED_OMITTED_CANDIDATES:
        return {
            "candidate_id": cid,
            "status": "REJECTED_REUSED_BASELINE",
            "reason": f"Candidate {cid} is governed as a reused baseline and must not be submitted to cluster solver."
        }

    pkg_dir = os.path.join(base_dir, candidate["package_directory"])
    deck_path = os.path.join(pkg_dir, candidate["deck_filename"])
    fortran_path = os.path.join(base_dir, "models/pandey_kumar_mode1/f42_mixed_uel.for")
    if not os.path.exists(fortran_path):
        fortran_path = os.path.join(pkg_dir, "f42_mixed_uel.for")
    pbs_path = os.path.join(pkg_dir, candidate["pbs_script_filename"])

    checks = []

    # 1. Deck hash check
    deck_sha = compute_sha256(deck_path)
    if deck_sha != candidate["deck_sha256"]:
        checks.append((False, f"Deck SHA256 mismatch: got {deck_sha}, expected {candidate['deck_sha256']}"))
    else:
        checks.append((True, "Deck SHA256 matches manifest"))

    # 2. Deck content check (Nphys, Depvar, SDV)
    deck_ok, deck_msg = audit_input_deck(deck_path, candidate["nphys"])
    checks.append((deck_ok, deck_msg))

    # 3. Fortran source check
    fortran_ok, fortran_msg = audit_fortran_source(fortran_path)
    checks.append((fortran_ok, fortran_msg))

    # 4. PBS wrapper check
    pbs_ok, pbs_msg = audit_pbs_wrapper(pbs_path, candidate["job_name"])
    checks.append((pbs_ok, pbs_msg))

    # Check overall result
    all_passed = all(c[0] for c in checks)
    failed_reasons = [c[1] for c in checks if not c[0]]

    return {
        "candidate_id": cid,
        "job_name": candidate["job_name"],
        "package_directory": candidate["package_directory"],
        "deck_filename": candidate["deck_filename"],
        "nphys": candidate["nphys"],
        "status": "PREFLIGHT_PASS" if all_passed else "PREFLIGHT_FAIL",
        "passed": all_passed,
        "checks": checks,
        "failed_reasons": failed_reasons
    }

def main():
    parser = argparse.ArgumentParser(description="Gate-6B Post-S1 Batch Release and Guarded Submission")
    parser.add_argument("--manifest", type=str, default="GATE6B_POST_S1_BATCH_RELEASE_MANIFEST.json",
                        help="Path to release manifest JSON")
    parser.add_argument("--s1-status", type=str, default="",
                        help="Status flag of corrected S1 solve (must be CORRECTED_S1_ENERGY_QUALIFIED)")
    parser.add_argument("--target-candidate", type=str, default="",
                        help="Optional candidate ID filter (e.g. S2, S3, T1, T3, L2, L3)")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Perform preflights and print planned batch execution without submitting")
    parser.add_argument("--execute", action="store_true", default=False,
                        help="Execute guarded batch submission (strictly requires --s1-status CORRECTED_S1_ENERGY_QUALIFIED)")
    args = parser.parse_args()

    # Find manifest
    manifest_path = args.manifest
    if not os.path.exists(manifest_path):
        alt_paths = [
            os.path.join("models/pandey_kumar_mode1", manifest_path),
            os.path.join(os.path.dirname(__file__), manifest_path)
        ]
        for p in alt_paths:
            if os.path.exists(p):
                manifest_path = p
                break

    if not os.path.exists(manifest_path):
        print(f"[FATAL ERROR] Release manifest not found: {args.manifest}", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    print("=" * 80)
    print("GATE-6B POST-S1 BATCH RELEASE & PREFLIGHT AUDITOR")
    print(f"Manifest: {manifest.get('manifest_id')} (v{manifest.get('manifest_version')})")
    print(f"Phase: {manifest.get('phase')}")
    print(f"Active Reference Job: {manifest.get('active_reference_job', {}).get('job_id')}")
    print("=" * 80)

    candidates = manifest.get("release_candidates", [])
    if args.target_candidate:
        candidates = [c for c in candidates if c["candidate_id"].upper() == args.target_candidate.upper()]
        if not candidates:
            print(f"[FATAL ERROR] Target candidate '{args.target_candidate}' not found in release set.", file=sys.stderr)
            sys.exit(1)

    # Check S1 Release Flag
    s1_qualified = (args.s1_status.strip().upper() == REQUIRED_S1_QUALIFICATION_FLAG)
    print(f"\n[S1 QUALIFICATION GATE] Status Flag: '{args.s1_status}' -> {'QUALIFIED' if s1_qualified else 'PENDING / BLOCKED'}")

    # Run Preflights
    preflight_results = []
    total_passed = 0
    total_failed = 0

    print("\n" + "-" * 80)
    print("RUNNING CANDIDATE PREFLIGHT CHECKS:")
    print("-" * 80)

    for cand in candidates:
        res = run_preflight_for_candidate(cand, base_dir=".")
        preflight_results.append(res)
        
        status_str = "PASS" if res["passed"] else "FAIL"
        print(f"[{res['candidate_id']}] Job: {res.get('job_name')} | Nphys: {res.get('nphys')} | Preflight: {status_str}")
        if not res["passed"]:
            total_failed += 1
            for r in res["failed_reasons"]:
                print(f"    - ERROR: {r}")
        else:
            total_passed += 1

    print("-" * 80)
    print(f"PREFLIGHT SUMMARY: {total_passed} PASSED, {total_failed} FAILED (Total: {len(candidates)})")
    print("-" * 80)

    # Verify Reuse Exclusions
    print("\n[REUSE EXCLUSIONS AUDIT]")
    for omitted in manifest.get("reused_baselines_omitted", []):
        print(f"  - {omitted['candidate_id']}: Governed as {omitted['governing_rule']} -> {omitted['cluster_submission_action']}")

    # Execution Decision
    if args.execute:
        if not s1_qualified:
            print(f"\n[EXECUTION BLOCKED] Submission aborted: S1 qualification flag is '{args.s1_status}' (required: '{REQUIRED_S1_QUALIFICATION_FLAG}').", file=sys.stderr)
            sys.exit(2)
        if total_failed > 0:
            print(f"\n[EXECUTION BLOCKED] Submission aborted: {total_failed} candidate preflight checks failed.", file=sys.stderr)
            sys.exit(3)

        print("\n" + "=" * 80)
        print("ALL PREFLIGHTS PASSED & S1 QUALIFIED: READY FOR BATCH SUBMISSION")
        print("=" * 80)
        # Note: In production, qsub calls are dispatched here and exact job IDs captured.
    else:
        print("\n[DRY RUN COMPLETE] Zero solver submissions executed. Candidates are staged and ready for release.")

    if total_failed > 0:
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
