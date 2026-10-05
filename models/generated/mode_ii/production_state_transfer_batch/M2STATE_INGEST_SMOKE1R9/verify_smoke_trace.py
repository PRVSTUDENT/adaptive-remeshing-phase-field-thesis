#!/usr/bin/env python3
"""
Deterministic solver trace checker for M2STATE_INGEST_SMOKE1 fixture.
Task: F43STATE-M2-INGESTION-SMOKE1R9
"""
import sys
import re
import json
from pathlib import Path

def parse_trace(trace_text):
    """Parse [INGEST_TRACE] lines from solver output text."""
    records = []
    pattern = re.compile(
        r"\[INGEST_TRACE\]\s+ELEM=\s*(\d+)\s+JTYPE=\s*(\d+)\s+KSTEP=\s*(\d+)\s+KINC=\s*(\d+)\s+IP=\s*(\d+)"
    )
    for line in trace_text.splitlines():
        if "[INGEST_TRACE]" not in line:
            continue
        m = pattern.search(line)
        if not m:
            continue
        elem, jtype, kstep, kinc, ip = map(int, m.groups())
        rec = {
            "elem": elem,
            "jtype": jtype,
            "kstep": kstep,
            "kinc": kinc,
            "ip": ip,
            "raw_line": line
        }
        if "U_NODES=" in line:
            u_part = line.split("U_NODES=")[1].split("SV_H=")[0].strip()
            rec["u_nodes"] = [float(val) for val in u_part.split(",") if val.strip()]
        if "SV_H=" in line:
            sv_part = re.search(r"SV_H=\s*([0-9.E+e-]+)", line)
            if sv_part:
                rec["sv_h"] = float(sv_part.group(1))
        if "PH=" in line:
            ph_part = re.search(r"PH=\s*([0-9.E+e-]+)", line)
            if ph_part:
                rec["ph"] = float(ph_part.group(1))
        if "SDV14=" in line:
            s14_part = re.search(r"SDV14=\s*([0-9.E+e-]+)", line)
            if s14_part:
                rec["sdv14"] = float(s14_part.group(1))
        if "SDV15=" in line:
            s15_part = re.search(r"SDV15=\s*([0-9.E+e-]+)", line)
            if s15_part:
                rec["sdv15"] = float(s15_part.group(1))
        if "SDV16=" in line:
            s16_part = re.search(r"SDV16=\s*([0-9.E+e-]+)", line)
            if s16_part:
                rec["sdv16"] = float(s16_part.group(1))
        records.append(rec)
    return records

def verify_trace(records, artifact):
    """
    Verify trace records against expected artifact sentinels. Fail closed on any error.
    Rule: Probe state MUST come strictly from KSTEP=2, KINC=1 startup calls.
    """
    if not records:
        return False, "FAIL: Zero trace records found", {"SDV14": "FAIL", "SDV15": "FAIL", "SDV16": "FAIL"}
    
    # Filter strictly for Step 2 Increment 1 (Step-2-IngestProbe startup)
    step2_recs = [r for r in records if r["kstep"] == 2 and r["kinc"] == 1]
    if not step2_recs:
        return False, "FAIL: Missing required KSTEP=2 KINC=1 startup ingestion records", {"SDV14": "FAIL", "SDV15": "FAIL", "SDV16": "FAIL"}

    # Take the FIRST call for each element/IP in KSTEP=2 KINC=1 to isolate initial carried state
    first_calls = {}
    for r in step2_recs:
        key = (r["elem"], r["jtype"], r["ip"])
        if key not in first_calls:
            first_calls[key] = r
    
    probe_recs = list(first_calls.values())

    # Check element coverage
    elems_found = {r["elem"] for r in probe_recs}
    expected_elems = {1, 2, 5, 6, 9, 10, 13, 14}
    if not expected_elems.issubset(elems_found):
        return False, f"FAIL: Missing element records in KSTEP=2 KINC=1. Expected {expected_elems}, got {elems_found}", {"SDV14": "FAIL", "SDV15": "FAIL", "SDV16": "FAIL"}

    # Check node sentinel phase for U1 ELEM=1
    e1_recs = [r for r in probe_recs if r["elem"] == 1 and r.get("jtype") == 1]
    if not e1_recs:
        return False, "FAIL: Missing ELEM=1 JTYPE=1 trace record in startup probe", {"SDV14": "FAIL", "SDV15": "FAIL", "SDV16": "FAIL"}
    
    e1_u = e1_recs[0].get("u_nodes", [])
    expected_u1 = [0.11, 0.23, 0.37, 0.61]
    if len(e1_u) != 4 or any(abs(a - b) > 1e-3 for a, b in zip(e1_u, expected_u1)):
        return False, f"FAIL: ELEM=1 u_nodes mismatch in startup probe. Got {e1_u}, expected {expected_u1}", {"SDV14": "FAIL", "SDV15": "FAIL", "SDV16": "FAIL"}
    
    # Check IP history sentinels & IP ordering for ELEM=1 (IPs 1..4)
    expected_h_e1 = [0.00011, 0.00012, 0.00013, 0.00014]
    for ip_idx in range(1, 5):
        ip_recs = [r for r in e1_recs if r["ip"] == ip_idx]
        if not ip_recs:
            return False, f"FAIL: ELEM=1 missing IP={ip_idx} startup record", {"SDV14": "FAIL", "SDV15": "FAIL", "SDV16": "FAIL"}
        actual_h = ip_recs[0].get("sv_h", 0.0)
        expected_h = expected_h_e1[ip_idx - 1]
        if abs(actual_h - expected_h) > 1e-6:
            return False, f"FAIL: ELEM=1 IP={ip_idx} SV_H mismatch in startup probe. Got {actual_h}, expected {expected_h}", {"SDV14": "FAIL", "SDV15": "FAIL", "SDV16": "FAIL"}

    # Check SDV14 / SDV15 / SDV16 contracts
    sdv15_ok = any("sdv15" in r for r in probe_recs if r.get("jtype") in (1, 3))
    sdv14_ok = any("sdv14" in r for r in probe_recs if r.get("jtype") in (2, 4))
    sdv16_ok = any("sdv16" in r for r in probe_recs if r.get("jtype") in (2, 4))

    sdv_contracts = {
        "SDV14": "PASS" if sdv14_ok else "FAIL",
        "SDV15": "PASS" if sdv15_ok else "FAIL",
        "SDV16": "PASS" if sdv16_ok else "FAIL"
    }

    if not (sdv14_ok and sdv15_ok and sdv16_ok):
        return False, f"FAIL: Reporting contract check failed: {sdv_contracts}", sdv_contracts

    return True, "PASS: Solver runtime state ingestion & SDV contracts verified", sdv_contracts

def main():
    if len(sys.argv) < 2:
        print("Usage: verify_smoke_trace.py <trace_file> [artifact_json]")
        sys.exit(1)
    
    trace_path = Path(sys.argv[1])
    artifact_path = Path(sys.argv[2]) if len(sys.argv) > 2 else trace_path.parent / "STATE_TRANSFER_ARTIFACT.json"
    
    if not trace_path.is_file():
        print(f"ERROR: Trace file {trace_path} not found")
        sys.exit(1)
        
    with open(artifact_path, "r") as f:
        artifact = json.load(f)
        
    trace_text = trace_path.read_bytes().decode("utf-8", errors="ignore")
    records = parse_trace(trace_text)
    ok, msg, sdv_status = verify_trace(records, artifact)
    print(msg)
    print(f"SDV14_contract = {sdv_status['SDV14']}")
    print(f"SDV15_contract = {sdv_status['SDV15']}")
    print(f"SDV16_contract = {sdv_status['SDV16']}")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
