#!/usr/bin/env python3
"""Static validation for the D3A3-R4 package_compatible_r2 active-set deck."""

import argparse
import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path


N_ELEM = 6400
N_IP = 4
N_NODES = 6601
EXPECTED_ACTIVE = 6446
EXPECTED_FREE = 155


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_tracked(path):
    return subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def bool_value(text):
    return str(text).strip().lower() in ("true", "1", "yes")


def runtime_validate(path):
    failures = []
    seen = set()
    records = 0
    h_min = None
    h_max = None
    duplicates = 0
    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) != 3:
                failures.append("invalid runtime record: " + line)
                continue
            element = int(parts[0])
            ip = int(parts[1])
            h = float(parts[2])
            key = (element, ip)
            if key in seen:
                duplicates += 1
            seen.add(key)
            records += 1
            if element < 1 or element > N_ELEM:
                failures.append("element out of range: %s" % element)
            if ip < 1 or ip > N_IP:
                failures.append("ip out of range: %s" % ip)
            if not math.isfinite(h):
                failures.append("nonfinite H for %s/%s" % key)
            if h < -1.0e-14:
                failures.append("negative H for %s/%s: %s" % (element, ip, h))
            h_min = h if h_min is None else min(h_min, h)
            h_max = h if h_max is None else max(h_max, h)
    expected = {(element, ip) for element in range(1, N_ELEM + 1) for ip in range(1, N_IP + 1)}
    missing = expected - seen
    if records != N_ELEM * N_IP:
        failures.append("records=%s expected=%s" % (records, N_ELEM * N_IP))
    if duplicates:
        failures.append("duplicates=%s" % duplicates)
    if missing:
        failures.append("missing_records=%s" % len(missing))
    return {
        "classification": (
            "stage_d3a3_r4_runtime_state_validation_pass"
            if not failures
            else "stage_d3a3_r4_runtime_state_validation_fail"
        ),
        "runtime_state_ok": not failures,
        "records": records,
        "duplicates": duplicates,
        "missing_records": len(missing),
        "minimum_H": h_min,
        "maximum_H": h_max,
        "sha256": sha256(path),
        "failures": failures,
    }


def parse_step_phase_bcs(inp_path):
    steps = {}
    current = None
    in_boundary = False
    for raw in inp_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        upper = line.upper()
        if upper.startswith("*STEP"):
            current = None
            for part in line.split(","):
                if part.strip().lower().startswith("name="):
                    current = part.split("=", 1)[1].strip()
            steps[current] = []
            in_boundary = False
            continue
        if upper.startswith("*END STEP"):
            current = None
            in_boundary = False
            continue
        if current is None:
            continue
        if upper.startswith("*BOUNDARY"):
            in_boundary = True
            continue
        if upper.startswith("*"):
            in_boundary = False
            continue
        if in_boundary:
            parts = [part.strip() for part in line.split(",")]
            if len(parts) >= 4:
                try:
                    node = int(parts[0])
                    dof1 = int(parts[1])
                    dof2 = int(parts[2])
                except ValueError:
                    continue
                if 1 <= node <= N_NODES and dof1 == 3 and dof2 == 3:
                    steps[current].append(node)
    return steps


def validate(args):
    failures = []
    nodes = read_csv(args.model_dir / "target" / "target_nodes.csv")
    elements = read_csv(args.model_dir / "target" / "target_elements.csv")
    nodal = read_csv(args.package_dir / "D3_TRANSFERRED_NODAL_D.csv")
    lower = read_csv(args.package_dir / "D3_LOWER_BOUND_NODAL_D.csv")
    ip_rows = read_csv(args.package_dir / "D3_TRANSFERRED_IP_H.csv")
    active_rows = read_csv(args.active_set_csv)
    active_nodes = sorted(int(row["node"]) for row in active_rows if bool_value(row["active_lower_bound"]))
    free_nodes = sorted(int(row["node"]) for row in active_rows if not bool_value(row["active_lower_bound"]))
    compatible = {int(row["node"]): float(row["d"]) for row in nodal}
    lower_d = {int(row["node"]): float(row["d_lower_bound"]) for row in lower}
    active_by_node = {int(row["node"]): row for row in active_rows}

    if not (args.d3a5_dir / "D3A5.ok").exists() or not git_tracked(args.d3a5_dir / "D3A5.ok"):
        failures.append("D3A5.ok missing or untracked")
    if not (args.package_dir / "D3_PACKAGE_COMPATIBLE_R2.ok").exists() or not git_tracked(
        args.package_dir / "D3_PACKAGE_COMPATIBLE_R2.ok"
    ):
        failures.append("D3_PACKAGE_COMPATIBLE_R2.ok missing or untracked")
    if not (args.exe_dir / "d3_transfer_h.dat").exists():
        failures.append("R4 executable runtime d3_transfer_h.dat missing")
    if len(nodes) != N_NODES:
        failures.append("target nodes=%s expected=%s" % (len(nodes), N_NODES))
    if len(elements) != N_ELEM:
        failures.append("target elements=%s expected=%s" % (len(elements), N_ELEM))
    if len(ip_rows) != N_ELEM * N_IP:
        failures.append("target IPs=%s expected=%s" % (len(ip_rows), N_ELEM * N_IP))
    if len(active_nodes) != EXPECTED_ACTIVE:
        failures.append("active nodes=%s expected=%s" % (len(active_nodes), EXPECTED_ACTIVE))
    if len(free_nodes) != EXPECTED_FREE:
        failures.append("free nodes=%s expected=%s" % (len(free_nodes), EXPECTED_FREE))
    if len(active_nodes) + len(free_nodes) != N_NODES:
        failures.append("active+free != 6601")
    if len(set(active_nodes)) != len(active_nodes):
        failures.append("duplicate active labels")
    if set(active_nodes) & set(free_nodes):
        failures.append("active/free overlap")
    if set(active_nodes) | set(free_nodes) != set(range(1, N_NODES + 1)):
        failures.append("missing active/free labels")

    active_failures = []
    free_failures = []
    for node in active_nodes:
        row = active_by_node[node]
        d_comp = float(row.get("d_compatible", compatible[node]))
        d_lb = float(row.get("d_lb", lower_d[node]))
        if not bool_value(row["active_lower_bound"]):
            active_failures.append(node)
        if abs(d_comp - d_lb) > 1.0e-12:
            active_failures.append(node)
        if abs(compatible[node] - lower_d[node]) > 1.0e-12:
            active_failures.append(node)
    for node in free_nodes:
        if bool_value(active_by_node[node]["active_lower_bound"]):
            free_failures.append(node)
        if compatible[node] < lower_d[node] - 1.0e-12:
            free_failures.append(node)
    if active_failures:
        failures.append("active lower-bound audit failures=%s" % len(set(active_failures)))
    if free_failures:
        failures.append("free-node audit failures=%s" % len(set(free_failures)))

    deck = args.exe_dir / "D3A3_R4_compatible_hold.inp"
    step_bcs = parse_step_phase_bcs(deck)
    counts = {name: len(labels) for name, labels in step_bcs.items()}
    if counts.get("INGEST_COMPATIBLE_R2") != N_NODES:
        failures.append("Step 1 phase BC count != 6601: %s" % counts.get("INGEST_COMPATIBLE_R2"))
    if counts.get("CHECKPOINT_EQUILIBRATION_COMPATIBLE_R2_FIXED") != N_NODES:
        failures.append(
            "Step 2 phase BC count != 6601: %s" % counts.get("CHECKPOINT_EQUILIBRATION_COMPATIBLE_R2_FIXED")
        )
    if counts.get("ACTIVE_SET_R2_RELEASE_HOLD") != EXPECTED_ACTIVE:
        failures.append(
            "Step 3 active phase BC count != 6446: %s" % counts.get("ACTIVE_SET_R2_RELEASE_HOLD")
        )
    step3 = set(step_bcs.get("ACTIVE_SET_R2_RELEASE_HOLD", []))
    if step3 != set(active_nodes):
        failures.append("Step 3 phase BC labels do not match active set")
    free_bc = len(step3 & set(free_nodes))
    if free_bc != 0:
        failures.append("Step 3 free-node phase BC count != 0: %s" % free_bc)

    runtime = runtime_validate(args.exe_dir / "d3_transfer_h.dat")
    failures.extend("runtime: " + failure for failure in runtime["failures"])

    r3_fortran = args.r3_exe_dir / "d3_transfer_uel.for"
    r4_fortran = args.exe_dir / "d3_transfer_uel.for"
    source_hash_identical = sha256(r3_fortran) == sha256(r4_fortran)
    if not source_hash_identical:
        failures.append("UEL source hash differs from accepted R3 source")
    if (args.exe_dir / "d3_transfer_table.inc").exists():
        failures.append("obsolete d3_transfer_table.inc present")
    deck_text = deck.read_text(encoding="utf-8", errors="replace")
    if "mp_mode=mpi" in deck_text.lower():
        failures.append("MPI token present in deck")

    active_audit = {
        "classification": (
            "stage_d3a3_r4_active_set_boundary_audit_pass"
            if not failures
            else "stage_d3a3_r4_active_set_boundary_audit_fail"
        ),
        "active_nodes": len(active_nodes),
        "free_nodes": len(free_nodes),
        "active_plus_free": len(active_nodes) + len(free_nodes),
        "duplicate_active_labels": len(active_nodes) - len(set(active_nodes)),
        "missing_active_free_labels": len(set(range(1, N_NODES + 1)) - (set(active_nodes) | set(free_nodes))),
        "step_phase_bc_counts": counts,
        "step3_free_node_phase_bc_count": free_bc,
        "step3_active_boundary_exact": step3 == set(active_nodes),
        "step3_active_phase_bc_count": len(step3),
    }
    status = {
        "classification": (
            "stage_d3a3_r4_static_validation_pass" if not failures else "stage_d3a3_r4_static_validation_fail"
        ),
        "D3A3_R4_static_ok": not failures,
        "target_nodes": len(nodes),
        "target_elements": len(elements),
        "target_ips": len(ip_rows),
        "runtime_H_sha256": runtime["sha256"],
        "runtime_H_tracked": git_tracked(args.exe_dir / "d3_transfer_h.dat"),
        "runtime_H_records": runtime["records"],
        "runtime_H_duplicates": runtime["duplicates"],
        "runtime_H_missing_records": runtime["missing_records"],
        "source_hash_identical_to_r3": source_hash_identical,
        "r3_source_sha256": sha256(r3_fortran),
        "r4_source_sha256": sha256(r4_fortran),
        "obsolete_transfer_table_absent": not (args.exe_dir / "d3_transfer_table.inc").exists(),
        "mpi_absent": "mp_mode=mpi" not in deck_text.lower(),
        "expected_active": EXPECTED_ACTIVE,
        "expected_free": EXPECTED_FREE,
        "failures": failures,
    }
    provenance = json.loads((args.exe_dir / "D3A3_R4_INPUT_PROVENANCE.json").read_text(encoding="utf-8"))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "D3A3_R4_STATIC_VALIDATION.json", status)
    write_json(args.out_dir / "D3A3_R4_ACTIVE_SET_BOUNDARY_AUDIT.json", active_audit)
    write_json(args.out_dir / "D3A3_R4_RUNTIME_STATE_VALIDATION.json", runtime)
    write_json(args.out_dir / "D3A3_R4_INPUT_PROVENANCE.json", provenance)
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=Path("models/state_transfer/d3_interrupted_transfer"))
    parser.add_argument(
        "--package-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/package_compatible_r2"),
    )
    parser.add_argument(
        "--d3a5-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/compatibility_reprojection_d3a5"),
    )
    parser.add_argument(
        "--active-set-csv",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/package_compatible_r2/D3_ACTIVE_SET_BY_NODE.csv"),
    )
    parser.add_argument(
        "--exe-dir",
        type=Path,
        default=Path("models/state_transfer/d3_interrupted_transfer/executable_r4_compatible_r2"),
    )
    parser.add_argument(
        "--r3-exe-dir",
        type=Path,
        default=Path("models/state_transfer/d3_interrupted_transfer/executable_r3_compatible"),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r4_compatible_datacheck"),
    )
    args = parser.parse_args()
    status = validate(args)
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if status["D3A3_R4_static_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
