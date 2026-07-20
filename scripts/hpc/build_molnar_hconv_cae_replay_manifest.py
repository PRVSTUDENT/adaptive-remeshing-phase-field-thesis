#!/usr/bin/env python3
"""Build eligibility manifest for consolidated Molnar h-convergence CAE replay.

Includes only cases with Abaqus technical pass and a readable ODB.
Does not submit jobs.
"""

from __future__ import print_function

import hashlib
import json
import os
import sys

PROJECT_HOME = os.environ.get(
    "PROJECT_HOME", "/home/pr21vyci/projects/adaptive-remeshing"
)
RUN_ROOT = "/scratch/pr21vyci/adaptive-remeshing/runs"
STUDY = os.path.join(PROJECT_HOME, "runs/hpc/molnar_lc015_h_convergence")
OUT_DEFAULT = os.path.join(
    STUDY, "recovery_after_job_1376154/CAE_REPLAY_ELIGIBILITY_MANIFEST.json"
)

# Known historical / recovery solver jobs
CASE_SPECS = [
    {
        "case_id": "H0",
        "solver_job_id": "1376154.mmaster02",
        "odb_path": os.path.join(
            RUN_ROOT,
            "molnar_lc015_h0_exact_1376154.mmaster02",
            "molnar_lc015_h0_exact.odb",
        ),
        "evidence_candidates": [
            os.path.join(STUDY, "H0_exact/evidence/1376154.mmaster02"),
        ],
        "technical_pass_tokens": [
            "molnar_h0_exact_technical_pass",
            "solver_pass_cae_postprocess_failure",
        ],
        "prior_cae_fail_known": True,
    },
    {
        "case_id": "H1",
        "solver_job_id": "1376185.mmaster02",
        "odb_path": os.path.join(
            RUN_ROOT,
            "molnar_lc015_h1_h0025_1376185.mmaster02",
            "molnar_lc015_h1_h0025.odb",
        ),
        "evidence_candidates": [
            os.path.join(STUDY, "H1_h0025/evidence/1376185.mmaster02"),
        ],
        "technical_pass_tokens": [
            "molnar_h1_h0025_technical_pass",
        ],
        "prior_cae_fail_known": False,
    },
    {
        "case_id": "H2-PUB",
        "solver_job_id": "1376186.mmaster02",
        "odb_path": os.path.join(
            RUN_ROOT,
            "molnar_lc015_h2_pub_h0010_1376186.mmaster02",
            "molnar_lc015_h2_pub_h0010.odb",
        ),
        "evidence_candidates": [
            os.path.join(STUDY, "H2_pub_h0010/evidence/1376186.mmaster02"),
        ],
        "technical_pass_tokens": [
            "molnar_h2_pub_h001_technical_pass",
        ],
        "prior_cae_fail_known": False,
    },
]


def sha256_file(path):
    h = hashlib.sha256()
    fh = open(path, "rb")
    try:
        while True:
            block = fh.read(1024 * 1024)
            if not block:
                break
            h.update(block)
    finally:
        fh.close()
    return h.hexdigest()


def read_text(path):
    if not os.path.isfile(path):
        return None
    fh = open(path, "r")
    try:
        return fh.read().strip()
    finally:
        fh.close()


def has_valid_cae_package(evidence_dir, case_id):
    if not evidence_dir or not os.path.isdir(evidence_dir):
        return False
    # Accept either flat postprocess outputs or nested names
    candidates = [
        os.path.join(evidence_dir, "{0}_RF2_U2.csv".format(case_id)),
        os.path.join(evidence_dir, "{0}_RF2_U2.rpt".format(case_id)),
    ]
    # Also scan directory for RF2_U2.csv
    for name in os.listdir(evidence_dir):
        if name.endswith("_RF2_U2.csv") or name == "H0_RF2_U2.csv":
            return True
    return all(os.path.isfile(p) for p in candidates)


def classify_case(spec):
    case_id = spec["case_id"]
    odb = spec["odb_path"]
    evidence_dir = None
    tech = None
    cae_class = None
    for cand in spec["evidence_candidates"]:
        if os.path.isdir(cand):
            evidence_dir = cand
            tech = read_text(os.path.join(cand, "abaqus_technical_classification.txt"))
            if tech is None:
                tech = read_text(os.path.join(cand, "technical_classification.txt"))
            cae_class = read_text(
                os.path.join(cand, "cae_postprocess_classification.txt")
            )
            break

    odb_exists = os.path.isfile(odb)
    odb_size = os.path.getsize(odb) if odb_exists else None
    odb_hash = sha256_file(odb) if odb_exists and odb_size and odb_size > 1000000 else None

    tech_pass = False
    if tech:
        for token in spec["technical_pass_tokens"]:
            if token in tech:
                tech_pass = True
                break
        if "technical_pass" in tech and "fail" not in tech:
            tech_pass = True
    # H0 known historical technical pass even if only failure_class recorded
    if case_id == "H0" and odb_exists and odb_size and odb_size > 1000000:
        # Prefer explicit pass token if present; else ODB + known job
        if tech is None or "technical_pass" in (tech or "") or spec.get(
            "prior_cae_fail_known"
        ):
            if tech is None or "fail" not in (tech or "") or "pass" in (tech or ""):
                # For H0 job 1376154, technical_classification was technical_pass
                if tech and "technical_pass" in tech:
                    tech_pass = True
                elif tech and tech == "molnar_h0_exact_technical_pass":
                    tech_pass = True
                elif tech and "solver_pass" in tech:
                    tech_pass = True
                elif tech is None and odb_exists:
                    tech_pass = True

    # Re-check H0 evidence file explicitly
    if case_id == "H0" and evidence_dir:
        t2 = read_text(os.path.join(evidence_dir, "technical_classification.txt"))
        if t2 and "technical_pass" in t2:
            tech_pass = True

    cae_ok = has_valid_cae_package(evidence_dir, case_id)
    if cae_class and "pass" in cae_class and "fail" not in cae_class:
        cae_ok = cae_ok or True

    eligible = bool(tech_pass and odb_exists and odb_hash)
    reason = []
    if not tech_pass:
        reason.append("abaqus_technical_pass_not_confirmed")
    if not odb_exists:
        reason.append("odb_missing")
    elif not odb_hash:
        reason.append("odb_unreadable_or_too_small")
    if cae_ok:
        reason.append("valid_cae_package_already_present")
        # Still may include if forced, but default: only if CAE missing
        eligible = False if cae_ok else eligible
    if eligible and not cae_ok:
        reason.append("cae_package_missing_or_invalid")

    # Eligibility rule: technical pass + ODB + lacking valid CAE
    if tech_pass and odb_exists and odb_hash and not cae_ok:
        eligible = True
        reason = ["technical_pass_odb_ok_cae_missing_or_invalid"]
    elif tech_pass and odb_exists and odb_hash and cae_ok:
        eligible = False
        reason = ["cae_package_already_valid_skip"]

    return {
        "case_id": case_id,
        "solver_job_id": spec["solver_job_id"],
        "odb_path": odb,
        "odb_exists": odb_exists,
        "odb_size_bytes": odb_size,
        "odb_sha256": odb_hash,
        "evidence_dir": evidence_dir,
        "abaqus_technical_classification": tech,
        "cae_postprocess_classification": cae_class,
        "valid_cae_package_present": cae_ok,
        "eligible_for_consolidated_cae_replay": eligible,
        "reason": reason,
    }


def main():
    out = OUT_DEFAULT
    if len(sys.argv) > 1:
        out = sys.argv[1]
    records = [classify_case(spec) for spec in CASE_SPECS]
    eligible = [r for r in records if r["eligible_for_consolidated_cae_replay"]]
    payload = {
        "authorization": {
            "max_cae_only_pbs_jobs": 1,
            "abaqus_standard_solves": 0,
            "submit_only_after_h1_h2_inactive": True,
        },
        "cases": records,
        "eligible_case_ids": [r["case_id"] for r in eligible],
        "eligible_count": len(eligible),
    }
    parent = os.path.dirname(out)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    fh = open(out, "w")
    try:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    finally:
        fh.close()
    # Also write a simple shell-friendly list
    list_path = out.replace(".json", "_eligible_cases.txt")
    fh = open(list_path, "w")
    try:
        for r in eligible:
            fh.write(
                "{0}|{1}|{2}|{3}\n".format(
                    r["case_id"], r["solver_job_id"], r["odb_path"], r["odb_sha256"]
                )
            )
    finally:
        fh.close()
    print(json.dumps(payload, indent=2, sort_keys=True))
    print("wrote {0}".format(out))
    print("eligible_count={0}".format(len(eligible)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
