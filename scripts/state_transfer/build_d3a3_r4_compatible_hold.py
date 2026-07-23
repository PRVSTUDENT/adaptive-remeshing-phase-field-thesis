#!/usr/bin/env python3
"""Build the separate D3A3-R4 package_compatible_r2 active-set deck."""

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path


N_ELEM = 6400
N_IP = 4
NODE_OFFSET = 100000
CHECKPOINT_U2 = 0.003000000026077032
DEFAULT_MODEL = Path("models/state_transfer/d3_interrupted_transfer")
DEFAULT_PACKAGE = Path("runs/hpc/stage_d3/interrupted_transfer/package_compatible_r2")
DEFAULT_R3_EXE = Path("models/state_transfer/d3_interrupted_transfer/executable_r3_compatible")
DEFAULT_OUT = Path("models/state_transfer/d3_interrupted_transfer/executable_r4_compatible_r2")


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv_runtime(ip_csv, out_path):
    rows = read_csv(ip_csv)
    rows.sort(key=lambda row: (int(row["element"]), int(row["integration_point"])))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write("%d %d %.17e\n" % (int(row["element"]), int(row["integration_point"]), float(row["H"])))
    return rows


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def add_label_set(lines, name, labels, chunk=12):
    lines.append("*Nset, nset=%s" % name)
    for start in range(0, len(labels), chunk):
        lines.append(", ".join(str(label) for label in labels[start : start + chunk]))


def bool_value(text):
    return str(text).strip().lower() in ("true", "1", "yes")


def generate_inp(path, model_dir, package_dir):
    nodes = read_csv(model_dir / "target" / "target_nodes.csv")
    elements = read_csv(model_dir / "target" / "target_elements.csv")
    compatible = {int(row["node"]): float(row["d"]) for row in read_csv(package_dir / "D3_TRANSFERRED_NODAL_D.csv")}
    lower = {int(row["node"]): float(row["d_lower_bound"]) for row in read_csv(package_dir / "D3_LOWER_BOUND_NODAL_D.csv")}
    active_rows = read_csv(package_dir / "D3_ACTIVE_SET_BY_NODE.csv")
    active_nodes = sorted(int(row["node"]) for row in active_rows if bool_value(row["active_lower_bound"]))
    free_nodes = sorted(int(row["node"]) for row in active_rows if not bool_value(row["active_lower_bound"]))

    lines = [
        "*Heading",
        "** D3A3-R4 compatible R2 active-set release hold.",
        "** Compatible nodal d and H from package_compatible_r2 (D3A5 actual-history reprojection).",
        "*Preprint, echo=NO, model=NO, history=NO, contact=NO",
        "*Node",
    ]
    for row in nodes:
        lines.append("%s, %s, %s" % (row["node"], row["x"], row["y"]))
    for row in nodes:
        lines.append("%d, %s, %s" % (int(row["node"]) + NODE_OFFSET, row["x"], row["y"]))

    lines += [
        "*User Element, nodes=4, type=U1, properties=3, coordinates=2, VARIABLES=8",
        "3",
        "*Element, type=U1, elset=PHASE",
    ]
    for row in elements:
        lines.append("%s, %s, %s, %s, %s" % (row["element"], row["n1"], row["n2"], row["n3"], row["n4"]))
    lines += ["*Elset, elset=PHASE, generate", "1, %d, 1" % N_ELEM, "*Uel Property, elset=PHASE", "0.015, 0.0027, 1.0"]

    lines += ["*User Element, nodes=4, type=U2, properties=4, coordinates=2, VARIABLES=56", "1, 2", "*Element, type=U2, elset=DISP"]
    for row in elements:
        label = int(row["element"]) + N_ELEM
        conn = [int(row["n%d" % i]) + NODE_OFFSET for i in range(1, 5)]
        lines.append("%d, %d, %d, %d, %d" % (label, conn[0], conn[1], conn[2], conn[3]))
    lines += ["*Elset, elset=DISP, generate", "%d, %d, 1" % (N_ELEM + 1, 2 * N_ELEM), "*Uel Property, elset=DISP", "210, 0.3, 1, 1e-07"]

    lines += ["*Element, type=CPS4, elset=UMATVIS"]
    for row in elements:
        label = int(row["element"]) + 2 * N_ELEM
        conn = [int(row["n%d" % i]) + NODE_OFFSET for i in range(1, 5)]
        lines.append("%d, %d, %d, %d, %d" % (label, conn[0], conn[1], conn[2], conn[3]))
    lines += [
        "*Elset, elset=UMATVIS, generate",
        "%d, %d, 1" % (2 * N_ELEM + 1, 3 * N_ELEM),
        "*Solid Section, elset=UMATVIS, material=UMATVIS",
        "1.0,",
        "*Material, name=UMATVIS",
        "*Depvar",
        "18,",
        "*User Material, constants=2",
        "1.0e-11, 0.3",
    ]

    top = [int(row["node"]) + NODE_OFFSET for row in nodes if abs(float(row["y"]) - 0.5) < 1e-12]
    bottom = [int(row["node"]) + NODE_OFFSET for row in nodes if abs(float(row["y"]) + 0.5) < 1e-12]
    node_by_label = {int(row["node"]): row for row in nodes}
    left_bottom = min(bottom, key=lambda n: abs(float(node_by_label[n - NODE_OFFSET]["x"]) + 0.5))
    add_label_set(lines, "TOP", top)
    add_label_set(lines, "BOTTOM", bottom)
    add_label_set(lines, "ANCHOR", [left_bottom])
    add_label_set(lines, "ACTIVE_PHASE", active_nodes)
    add_label_set(lines, "FREE_PHASE", free_nodes)

    def phase_bcs(values, labels):
        for node in sorted(labels):
            lines.append("%d, 3, 3, %.17g" % (node, values[node]))

    lines += [
        "*Step, name=INGEST_COMPATIBLE_R2, nlgeom=NO",
        "*Static",
        "1.0, 1.0",
        "*Boundary",
        "BOTTOM, 2, 2, 0.0",
        "ANCHOR, 1, 1, 0.0",
    ]
    phase_bcs(compatible, compatible)
    lines += ["*Output, field", "*Element Output, elset=UMATVIS", "SDV", "*Node Output", "U, RF", "*End Step"]

    lines += [
        "*Step, name=CHECKPOINT_EQUILIBRATION_COMPATIBLE_R2_FIXED, nlgeom=NO",
        "*Static",
        "0.1, 1.0, 1.0e-08, 0.1",
        "*Boundary",
        "BOTTOM, 2, 2, 0.0",
        "ANCHOR, 1, 1, 0.0",
        "TOP, 2, 2, %.17g" % CHECKPOINT_U2,
    ]
    phase_bcs(compatible, compatible)
    lines += ["*Output, field", "*Element Output, elset=UMATVIS", "SDV", "*Node Output", "U, RF", "*End Step"]

    lines += [
        "*Step, name=ACTIVE_SET_R2_RELEASE_HOLD, nlgeom=NO",
        "*Static",
        "0.1, 1.0, 1.0e-08, 0.1",
        "*Boundary, op=NEW",
        "BOTTOM, 2, 2, 0.0",
        "ANCHOR, 1, 1, 0.0",
        "TOP, 2, 2, %.17g" % CHECKPOINT_U2,
    ]
    phase_bcs(lower, active_nodes)
    lines += ["*Output, field", "*Element Output, elset=UMATVIS", "SDV", "*Node Output", "U, RF", "*End Step"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"active_nodes": active_nodes, "free_nodes": free_nodes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--package-dir", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--r3-exe-dir", type=Path, default=DEFAULT_R3_EXE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    src_fortran = args.r3_exe_dir / "d3_transfer_uel.for"
    dst_fortran = args.out_dir / "d3_transfer_uel.for"
    shutil.copyfile(src_fortran, dst_fortran)
    active = generate_inp(args.out_dir / "D3A3_R4_compatible_hold.inp", args.model_dir, args.package_dir)
    runtime_rows = write_csv_runtime(args.package_dir / "D3_TRANSFERRED_IP_H.csv", args.out_dir / "d3_transfer_h.dat")
    manifest = {
        "classification": "stage_d3a3_r4_runtime_h_state_generated",
        "source_csv": str(args.package_dir / "D3_TRANSFERRED_IP_H.csv"),
        "runtime_state_file": str(args.out_dir / "d3_transfer_h.dat"),
        "records": len(runtime_rows),
        "expected_records": N_ELEM * N_IP,
        "elements": N_ELEM,
        "integration_points_per_element": N_IP,
        "sha256": sha256(args.out_dir / "d3_transfer_h.dat"),
        "format": "three whitespace-separated columns without header: element integration_point H",
        "sorted_by": ["element", "integration_point"],
    }
    write_json(args.out_dir / "D3A3_R4_RUNTIME_MANIFEST.json", manifest)
    provenance = {
        "classification": "stage_d3a3_r4_input_prepared",
        "deck": str(args.out_dir / "D3A3_R4_compatible_hold.inp"),
        "compatible_package": str(args.package_dir),
        "d3a5_projection": "runs/hpc/stage_d3/interrupted_transfer/compatibility_reprojection_d3a5",
        "r3_fortran_source": str(src_fortran),
        "r4_fortran_source": str(dst_fortran),
        "r3_fortran_sha256": sha256(src_fortran),
        "r4_fortran_sha256": sha256(dst_fortran),
        "fortran_byte_identical_to_r3": sha256(src_fortran) == sha256(dst_fortran),
        "active_nodes": len(active["active_nodes"]),
        "free_nodes": len(active["free_nodes"]),
        "runtime_H_sha256": manifest["sha256"],
        "original_package_r1_replaced": False,
        "package_r2_source": str(args.package_dir),
    }
    write_json(args.out_dir / "D3A3_R4_INPUT_PROVENANCE.json", provenance)
    print(json.dumps(provenance, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
