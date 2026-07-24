#!/usr/bin/env python3
"""Static Stage-P scan for shared-state and file-I/O constructs in Fortran."""
from __future__ import annotations
import argparse, csv, json, os, re
from collections import Counter
from pathlib import Path

PATTERNS = {
    "COMMON": re.compile(r"\bCOMMON\b", re.I),
    "SAVE": re.compile(r"\bSAVE\b", re.I),
    "DATA": re.compile(r"^\s*(?:\d+\s+)?DATA\b", re.I),
    "BLOCK_DATA": re.compile(r"\bBLOCK\s+DATA\b", re.I),
    "OPEN": re.compile(r"\bOPEN\s*\(", re.I),
    "READ": re.compile(r"\bREAD\s*\(", re.I),
    "WRITE": re.compile(r"\bWRITE\s*\(", re.I),
    "USRVAR": re.compile(r"\bUSRVAR\b", re.I),
    "TRANSFER_DONE": re.compile(r"\bTRANSFER_DONE\b", re.I),
    "UEXTERNALDB": re.compile(r"\bUEXTERNALDB\b", re.I),
}
EXTS = {".for", ".f", ".f90", ".inc"}

def access(line: str) -> str:
    s=line.upper().replace(" ","")
    if "=" in s and not s.lstrip().startswith(("IF(","DO","PARAMETER")):
        left=s.split("=",1)[0]
        if "USRVAR(" in left or "TRANSFER_DONE(" in left:
            return "write"
    if "USRVAR" in s or "TRANSFER_DONE" in s:
        return "read_or_control"
    if any(k in s for k in ("OPEN(","READ(","WRITE(")):
        return "file_io"
    return "declaration_or_control"

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--output-dir", default="results/validation/stage_p_static_audit")
    ns=ap.parse_args()
    root=Path(ns.root).resolve(); out=(root/ns.output_dir); out.mkdir(parents=True,exist_ok=True)
    scan_roots=[root/"models/baseline_original/molnar_gravouil_2017",
                root/"models/state_transfer/d2_tiny_transfer/executable",
                root/"models/state_transfer/d3_interrupted_transfer"]
    rows=[]; files=set()
    for base in scan_roots:
        if not base.exists(): continue
        for p in base.rglob("*"):
            if p.suffix.lower() not in EXTS or not p.is_file(): continue
            rel=p.relative_to(root).as_posix()
            for no,line in enumerate(p.read_text(encoding="utf-8",errors="replace").splitlines(),1):
                hits=[name for name,rx in PATTERNS.items() if rx.search(line)]
                for name in hits:
                    files.add(rel)
                    rows.append({"file":rel,"line":no,"construct":name,"access":access(line),
                                 "snippet":line.strip()[:240]})
    csv_path=out/"SHARED_VARIABLE_ACCESS.csv"
    with csv_path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(
            f,
            fieldnames=["file","line","construct","access","snippet"],
            lineterminator=os.linesep,
        )
        w.writeheader(); w.writerows(rows)
    counts=Counter(r["construct"] for r in rows)
    risky=sorted({r["file"] for r in rows if r["construct"] in
                  {"COMMON","SAVE","DATA","BLOCK_DATA","USRVAR","TRANSFER_DONE","OPEN","READ","WRITE"}})
    result={
      "classification":"stage_p_static_audit_risk_identified",
      "solver_executed":False,
      "scope":{"roots":[str(x.relative_to(root)).replace("\\","/") for x in scan_roots],
               "fortran_files_with_matches":len(files),"matched_records":len(rows)},
      "construct_counts":dict(sorted(counts.items())),
      "risk_summary":{
        "thread_safety_general_established":False,
        "mpi_state_sharing_established":False,
        "files_with_risky_constructs":len(risky),
        "principal_findings":[
          "COMMON/SAVE/DATA storage is present in preserved and transfer variants.",
          "USRVAR is read and written from UEL and UMAT call paths.",
          "TRANSFER_DONE uses a check-then-write initialization path in D2.",
          "UEXTERNALDB variants load history into shared COMMON storage and perform file I/O.",
          "Static source alone cannot prove call ordering, same-thread execution, or same-rank layer ownership."
        ]
      },
      "outputs":{"access_csv":csv_path.relative_to(root).as_posix()},
      "risky_files":risky
    }
    package = root / "models/parallelization/minimal_externaldb_commonblock_test"
    required_package = [
        package / "P3S_serial_diagnostic.inp",
        package / "p2_instrumented_commonblock.for",
        package / "d2_transfer_table.inc",
        root / "scripts/hpc/stage_p/01_p3s_serial_diagnostic.pbs",
        root / "scripts/hpc/stage_p/submit_p3s_serial_diagnostic.sh",
        root / "scripts/postprocessing/extract_p3s_diagnostic_state.py",
        root / "scripts/postprocessing/parse_p3_diagnostic_log.py",
        root / "scripts/validation/validate_p3s_serial_diagnostic.py",
    ]
    missing = [path.relative_to(root).as_posix() for path in required_package if not path.is_file()]
    source_text = (package / "p2_instrumented_commonblock.for").read_text(
        encoding="utf-8", errors="replace"
    ) if not missing else ""
    pbs_text = (root / "scripts/hpc/stage_p/01_p3s_serial_diagnostic.pbs").read_text(
        encoding="utf-8", errors="replace"
    ) if not missing else ""
    wrapper_text = (root / "scripts/hpc/stage_p/submit_p3s_serial_diagnostic.sh").read_text(
        encoding="utf-8", errors="replace"
    ) if not missing else ""
    required_tokens = [
        "GETRANK()", "GETTHREADID()", "P3_ACCESS", "P3_CONFLICT",
        "P3_FINAL_CONFLICTS", "MUTEXLOCK(91)", "MUTEXUNLOCK(91)",
    ]
    missing_tokens = [token for token in required_tokens if token not in source_text]
    package_failures = []
    if missing:
        package_failures.append("missing P3-S files")
    if missing_tokens:
        package_failures.append("missing diagnostic source tokens")
    if "cpus=1 mp_mode=threads" not in pbs_text or "OMP_NUM_THREADS=1" not in pbs_text:
        package_failures.append("serial execution configuration not frozen")
    if "P3S_EXECUTION_AUTHORIZATION.json" not in wrapper_text:
        package_failures.append("submission authorization guard absent")
    if "p3t4_authorized" not in wrapper_text:
        package_failures.append("P3-T4 denial guard absent")
    if "python/gcc/11.4.0/3.11.7" not in pbs_text or "python/gcc/11.4.0/3.11.7" not in wrapper_text:
        package_failures.append("qualified Python 3.11.7 module not bound")
    result["p3s_preparation"] = {
        "classification": "stage_p3s_lane_prepared_static_pass" if not package_failures else "stage_p3s_lane_prepared_static_fail",
        "solver_executed": False,
        "hpc_submitted": False,
        "missing_files": missing,
        "missing_diagnostic_tokens": missing_tokens,
        "failures": package_failures,
    }
    (out/"PARALLEL_SAFETY_AUDIT.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"classification":result["classification"],"records":len(rows),"files":len(files),
                      "p3s_preparation":result["p3s_preparation"]["classification"]}))
    return 0 if not package_failures else 1
if __name__=="__main__": raise SystemExit(main())
