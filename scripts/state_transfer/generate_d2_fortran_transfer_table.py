#!/usr/bin/env python3
"""Generate the executable Stage D2A tiny transfer-ingestion package."""

import argparse
import csv
import hashlib
import json
import math
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "models/state_transfer/d2_tiny_transfer"
EXECUTABLE = PACKAGE / "executable"
SOURCE = ROOT / "src/state_transfer/d2_tiny_transfer_uel.for"
PRESERVED_DECK = ROOT / "models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.inp"
PRESERVED_FORTRAN = ROOT / "models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.for"


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def finite_float(value: str, name: str) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{name} is not finite: {value}")
    return out


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def chunks(values: List[str], n: int = 8) -> List[str]:
    return [", ".join(values[i : i + n]) for i in range(0, len(values), n)]


def confirm_phase_dof() -> Dict[str, object]:
    deck = PRESERVED_DECK.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"\*User element,\s*nodes=4,\s*type=U1[^\n]*\n\s*([0-9,\s]+)", deck, re.IGNORECASE)
    if not m:
        raise RuntimeError("Could not find preserved U1 *User Element card")
    dofs = [int(x) for x in re.findall(r"\d+", m.group(1))]
    source = PRESERVED_FORTRAN.read_text(encoding="utf-8", errors="replace")
    source_checks = {
        "phase_from_u_i": "PHASE=PHASE+AN(I)*U(I)" in source,
        "u1_uploads_sdv15": "USRVAR(JELEM,I+NSTVTT,INPT)" in source,
        "history_uploads_sdv16": "USRVAR(JELEM,16,INPT)" in source,
    }
    if dofs != [3]:
        raise RuntimeError(f"Expected preserved U1 phase DOF [3], found {dofs}")
    if not all(source_checks.values()):
        raise RuntimeError(f"Preserved source checks failed: {source_checks}")
    return {"phase_dof": dofs[0], "source_checks": source_checks}


def validate_inputs(nodes, elements, nodal_d, ip_h) -> Dict[str, object]:
    node_labels = [int(r["node"]) for r in nodes]
    element_labels = [int(r["element"]) for r in elements]
    d_labels = [int(r["target_node"]) for r in nodal_d]
    ip_keys = [(int(r["target_element"]), int(r["target_ip"])) for r in ip_h]
    if len(node_labels) != len(set(node_labels)):
        raise RuntimeError("Duplicate target node labels")
    if len(element_labels) != len(set(element_labels)):
        raise RuntimeError("Duplicate target element labels")
    if len(d_labels) != len(set(d_labels)):
        raise RuntimeError("Duplicate target nodal d labels")
    if len(ip_keys) != len(set(ip_keys)):
        raise RuntimeError("Duplicate target element/IP history entries")
    if set(d_labels) != set(node_labels):
        raise RuntimeError("Target nodal d labels do not match target nodes")
    if {e for e, _ip in ip_keys} != set(element_labels):
        raise RuntimeError("Target H element labels do not match target elements")
    if {ip for _e, ip in ip_keys} != {1}:
        raise RuntimeError("D2A tiny package expects exactly target_ip=1")
    for row in nodal_d:
        d = finite_float(row["d_bounded"], "d_bounded")
        if d < 0.0 or d > 1.0:
            raise RuntimeError(f"d outside [0,1] at node {row['target_node']}: {d}")
    for row in ip_h:
        h = finite_float(row["H_bounded"], "H_bounded")
        if h < 0.0:
            raise RuntimeError(f"H < 0 at {row['target_element']}/{row['target_ip']}: {h}")
    return {
        "target_node_count": len(node_labels),
        "target_element_count": len(element_labels),
        "target_ip_count": len(ip_keys),
        "target_ip_set": sorted({ip for _e, ip in ip_keys}),
    }


def make_include(ip_h: List[Dict[str, str]]) -> str:
    labels = [str(int(r["target_element"])) for r in ip_h]
    hvals = [f"{finite_float(r['H_bounded'], 'H_bounded'):.17E}" for r in ip_h]
    lines = [
        "      INTEGER D2_TRANSFER_COUNT",
        f"      PARAMETER (D2_TRANSFER_COUNT={len(labels)})",
        "      INTEGER D2_TRANSFER_ELEM(D2_TRANSFER_COUNT)",
        "      DOUBLE PRECISION D2_TRANSFER_H(D2_TRANSFER_COUNT)",
        "      DATA D2_TRANSFER_ELEM /",
    ]
    for i, line in enumerate(chunks(labels), start=1):
        suffix = "," if i < len(chunks(labels)) else "/"
        lines.append(f"     1 {line}{suffix}")
    lines.append("      DATA D2_TRANSFER_H /")
    h_chunks = chunks(hvals, 4)
    for i, line in enumerate(h_chunks, start=1):
        suffix = "," if i < len(h_chunks) else "/"
        lines.append(f"     1 {line}{suffix}")
    return "\n".join(lines) + "\n"


def make_deck(nodes, elements, nodal_d) -> str:
    node_d = {int(r["target_node"]): finite_float(r["d_bounded"], "d_bounded") for r in nodal_d}
    n_elem = len(elements)
    mech_node_offset = 1000
    lines = [
        "*Heading",
        "** Stage D2A serial transferred-state ingestion, generated package.",
        "** Phase DOF confirmed from preserved Molnar U1 card: DOF 3.",
        "** Phase nodes use target labels; mechanics/visualization nodes are duplicated at +1000.",
        "*Preprint, echo=NO, model=NO, history=NO, contact=NO",
        "*Node",
    ]
    for row in nodes:
        lines.append(f"{int(row['node'])}, {finite_float(row['x'], 'x'):.12g}, {finite_float(row['y'], 'y'):.12g}")
    for row in nodes:
        label = int(row["node"]) + mech_node_offset
        lines.append(f"{label}, {finite_float(row['x'], 'x'):.12g}, {finite_float(row['y'], 'y'):.12g}")
    lines += [
        "*User Element, nodes=4, type=U1, properties=3, coordinates=2, VARIABLES=2",
        "3",
        "*Element, type=U1, elset=PLATE",
    ]
    for row in elements:
        lines.append(f"{int(row['element'])}, {int(row['n1'])}, {int(row['n2'])}, {int(row['n3'])}, {int(row['n4'])}")
    lines += [
        "*Elset, elset=PLATE, generate",
        f"1, {n_elem}, 1",
        "*Uel Property, elset=PLATE",
        "0.015, 0.0027, 1.0",
        "*User Element, nodes=4, type=U2, properties=4, coordinates=2, VARIABLES=2",
        "1, 2",
        "*Element, type=U2, elset=PLATE_SS",
    ]
    for row in elements:
        label = int(row["element"]) + n_elem
        lines.append(
            f"{label}, {int(row['n1']) + mech_node_offset}, {int(row['n2']) + mech_node_offset}, "
            f"{int(row['n3']) + mech_node_offset}, {int(row['n4']) + mech_node_offset}"
        )
    lines += [
        "*Elset, elset=PLATE_SS, generate",
        f"{n_elem + 1}, {2*n_elem}, 1",
        "*Uel Property, elset=PLATE_SS",
        "1.0, 0.3, 1.0e-11, 1.0",
        "*Element, type=CPS4, elset=umatelem",
    ]
    for row in elements:
        label = int(row["element"]) + 2 * n_elem
        lines.append(
            f"{label}, {int(row['n1']) + mech_node_offset}, {int(row['n2']) + mech_node_offset}, "
            f"{int(row['n3']) + mech_node_offset}, {int(row['n4']) + mech_node_offset}"
        )
    lines += [
        "*Elset, elset=umatelem, generate",
        f"{2*n_elem + 1}, {3*n_elem}, 1",
        "*Solid Section, elset=umatelem, material=umatelem",
        "1.0,",
        "*Material, name=umatelem",
        "*Depvar",
        "16,",
        "*User Material, constants=2",
        "1.0, 0.3",
        "*Step, name=D2A_INIT, nlgeom=NO, inc=1",
        "*Static",
        "1.0, 1.0",
        "*Boundary",
    ]
    for label in sorted(node_d):
        lines.append(f"{label + mech_node_offset}, 1, 2, 0.0")
    for label in sorted(node_d):
        lines.append(f"{label}, 3, 3, {node_d[label]:.17g}")
    lines += [
        "*Restart, write, frequency=0",
        "*Output, field, frequency=1",
        "*Node Output",
        "U, RF",
        "*Element Output, elset=umatelem",
        "SDV",
        "*End Step",
    ]
    return "\n".join(lines) + "\n"


def make_d2b_deck(nodes, elements, nodal_d) -> str:
    lines = make_deck(nodes, elements, nodal_d).splitlines()
    lines[1] = "** Stage D2B serial transferred-state persistence and tiny continuation."
    first_end = lines.index("*End Step")
    lines[first_end:first_end] = [
        "*Output, history, frequency=1",
        "*Energy Output, variable=ALL",
    ]
    lines.extend(
        [
            "*Step, name=D2B_RELEASE_HOLD, nlgeom=NO, inc=2",
            "*Static",
            "0.5, 1.0",
            "*Boundary, op=NEW",
            "1001, 1, 2, 0.0",
            "1005, 2, 2, 0.0",
            "*Output, field, frequency=1",
            "*Node Output",
            "U, RF",
            "*Element Output, elset=umatelem",
            "SDV",
            "*Output, history, frequency=1",
            "*Energy Output, variable=ALL",
            "*End Step",
            "*Step, name=D2B_TINY_CONTINUATION, nlgeom=NO, inc=2",
            "*Static",
            "0.5, 1.0",
            "*Boundary, op=NEW",
            "1001, 1, 2, 0.0",
            "1005, 2, 2, 0.0",
            "1011, 2, 2, 1.0e-5",
            "1012, 2, 2, 1.0e-5",
            "1013, 2, 2, 1.0e-5",
            "1014, 2, 2, 1.0e-5",
            "1015, 2, 2, 1.0e-5",
            "*Output, field, frequency=1",
            "*Node Output",
            "U, RF",
            "*Element Output, elset=umatelem",
            "SDV",
            "*Output, history, frequency=1",
            "*Energy Output, variable=ALL",
            "*End Step",
        ]
    )
    return "\n".join(lines) + "\n"


def generate(out_dir: Path = EXECUTABLE) -> Dict[str, object]:
    nodes = read_csv(PACKAGE / "target_nodes.csv")
    elements = read_csv(PACKAGE / "target_elements.csv")
    nodal_d = read_csv(PACKAGE / "target_transferred_nodal_d.csv")
    ip_h = read_csv(PACKAGE / "target_transferred_ip_H.csv")
    phase = confirm_phase_dof()
    checks = validate_inputs(nodes, elements, nodal_d, ip_h)
    out_dir.mkdir(parents=True, exist_ok=True)
    inc = out_dir / "d2_transfer_table.inc"
    deck = out_dir / "D2A_serial_ingestion.inp"
    d2b_deck = out_dir / "D2B_serial_continuation.inp"
    source_copy = out_dir / "d2_tiny_transfer_uel.for"
    write_text(inc, make_include(ip_h))
    write_text(deck, make_deck(nodes, elements, nodal_d))
    write_text(d2b_deck, make_d2b_deck(nodes, elements, nodal_d))
    shutil.copyfile(SOURCE, source_copy)
    validation = {
        "classification": "stage_d2a_executable_package_static_pass",
        "D2A_ok": False,
        "phase_dof_confirmed": phase["phase_dof"],
        "phase_dof_evidence": "Preserved Molnar *User Element type=U1 card lists DOF 3; source computes PHASE from U(I).",
        "layer_offsets": {"U1": "1..8", "U2": "9..16", "visualization": "17..24", "physical_from_visualization": "label - 16"},
        "node_layers": {"phase_target_nodes": "1..15", "mechanics_visualization_nodes": "1001..1015"},
        "fortran_n_elem": 8,
        "transfer_mode": 1,
        "transfer_mode_scope": "D2-only source variant; production jobs keep transfer disabled by not using this source.",
        "static_checks": checks,
        "files": {
            "deck": rel(deck),
            "d2b_deck": rel(d2b_deck),
            "include": rel(inc),
            "source": rel(source_copy),
        },
        "hashes": {p.name: sha256(p) for p in [deck, d2b_deck, inc, source_copy]},
    }
    write_text(out_dir / "PACKAGE_VALIDATION.json", json.dumps(validation, indent=2, sort_keys=True) + "\n")
    return validation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=EXECUTABLE)
    args = parser.parse_args()
    validation = generate(args.out_dir)
    print(json.dumps(validation, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
