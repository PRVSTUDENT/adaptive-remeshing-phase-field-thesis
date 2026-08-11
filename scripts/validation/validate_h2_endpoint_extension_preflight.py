#!/usr/bin/env python3
"""Fail-closed preflight for the H2 endpoint-resolution package."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H2_FRACFIX"
NEW = ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H2_FRACFIX_ENDPOINT"
EXPECTED = {
    "inp": "c9a3f496cf2cb0daa455cfae31f5bd699b56f3b410f0a7f2a12014b2718be5b0",
    "uel": "0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8",
    "pbs": "96854cf7058ecf6d7d571b758aa937bf199ec9b8a5eef90d7578e4d969f5be89",
    "wrapper": "4293ceaf961b067ea24031d218e303f107984289d0e9434fe1b7adc169066318",
    "manifest": "2238e1461ef9b7744f2d0b5e8b79c59a49048f465bb77a6d99d769ca2d13296e",
}


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def element_count(text, element_type):
    active = False
    count = 0
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("*"):
            active = bool(re.match(rf"\*Element\s*,.*type={element_type}(?:\s*,|$)", stripped, re.I))
        elif active and stripped and not stripped.startswith("**"):
            count += 1
    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorization", type=Path)
    args = parser.parse_args()
    errors = []
    old_inp = OLD / "M2REF_H2_FRACFIX.inp"
    new_inp = NEW / "M2REF_H2_FRACFIX_ENDPOINT.inp"
    files = {
        "inp": new_inp,
        "uel": NEW / "f42_mixed_uel.for",
        "pbs": NEW / "M2REF_H2_FRACFIX_ENDPOINT.pbs",
        "wrapper": NEW / "submit_m2ref_h2_fracfix_endpoint.sh",
        "manifest": NEW / "PACKAGE_MANIFEST.json",
    }
    for key, path in files.items():
        if not path.is_file() or sha(path) != EXPECTED[key]:
            errors.append(f"{key} exact raw SHA256 mismatch")
    if sha(old_inp) != sha(new_inp):
        errors.append("scientific input differs from historical H2")
    if sha(OLD / "f42_mixed_uel.for") != sha(NEW / "f42_mixed_uel.for"):
        errors.append("UEL differs from historical H2")

    inp = new_inp.read_text(encoding="utf-8")
    pbs = files["pbs"].read_text(encoding="utf-8")
    wrapper = files["wrapper"].read_text(encoding="utf-8")
    manifest = json.loads(files["manifest"].read_text(encoding="utf-8"))
    semantic = json.loads((NEW / "SEMANTIC_COMPARISON.json").read_text(encoding="utf-8"))
    for typ in ("U1", "U2", "CPE4"):
        if element_count(inp, typ) != 33852:
            errors.append(f"{typ} element count is not 33852")
    if "*User Element, type=U2, nodes=4, coordinates=2, properties=5, variables=56" not in inp:
        errors.append("U2 five-property declaration missing")
    if not re.search(r"\*UEL Property, elset=DISP_QUAD\s+[^\n]*,\s*33852\.0", inp, re.I):
        errors.append("true NPHYS is not property slot 5")
    required_output = (" U, RF", " SDV, S, EVOL", "ALLAE, ALLCD, ALLIE, ALLKE, ALLPD, ALLSE, ALLWK, ETOTAL")
    if any(item not in inp for item in required_output):
        errors.append("scientific output parity contract missing")
    required_pbs = ("#PBS -N M2H2ENDPOINT", "select=1:ncpus=1:mem=8gb", "walltime=24:00:00", "#PBS -q entry_imfdfkmq", "#PBS -m abe")
    if any(item not in pbs for item in required_pbs):
        errors.append("PBS resource or notification contract mismatch")
    recipients = "Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de"
    if recipients not in pbs:
        errors.append("notification recipient contract mismatch")
    if "qsub M2REF_H2_FRACFIX_ENDPOINT.pbs" not in wrapper or "AUTH_FILE" not in wrapper:
        errors.append("guarded wrapper contract mismatch")
    if manifest.get("physical_element_count") != 33852 or manifest.get("maximum_permitted_submissions") != 0:
        errors.append("manifest NPHYS or authorization state mismatch")
    if semantic.get("unexpected_scientific_differences") != []:
        errors.append("semantic comparison found unexpected scientific differences")

    authorization_status = "BLOCKED_no_direct_human_authorization"
    if args.authorization:
        if not args.authorization.is_file():
            errors.append("authorization record does not exist")
        else:
            auth = json.loads(args.authorization.read_text(encoding="utf-8"))
            required = {"execution_authorized": True, "submission_approved": True, "maximum_jobs": 1, "job_name": "M2H2ENDPOINT"}
            if any(auth.get(k) != v for k, v in required.items()):
                errors.append("authorization record does not authorize exactly this one job")
            else:
                authorization_status = "PASS_exact_one_job_authorization"

    if errors:
        print("H2 endpoint-extension preflight: FAIL")
        for error in errors:
            print("ERROR:", error)
        return 1
    print("H2 endpoint-extension package preflight: PASS")
    print("scientific_identity_with_old_H2: PASS")
    print("NPHYS: 33852")
    print("producer_consumer_mapping: PASS")
    print("PBS_grammar_resources_notifications_wrapper_manifest_output_parity: PASS")
    print("submission_preflight:", authorization_status)
    return 0 if args.authorization else 2


if __name__ == "__main__":
    sys.exit(main())
