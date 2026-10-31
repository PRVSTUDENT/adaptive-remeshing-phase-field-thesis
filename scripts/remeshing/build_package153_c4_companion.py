#!/usr/bin/env python3
"""
Builds Package 153: Production C4 Companion Continuum Model for MISESERI Recovery.

Extracts the authentic 7,056-element mesh directly from Package 147
(M1_C4_CORRECTED_PACKAGE147_REF.inp), preserving:
1. 7,265 physical nodes + RP 999999.
2. 7,056 CPE4 continuum elements (elset=ALL_QUADS) with labels 1..7056.
3. 40 duplicate coincident slit-flank node pairs (nodes 3571..3610 and 7226..7265).
4. 45 shared ligament nodes (nodes 3611..3655).
5. Exact node sets N_TOP (85 nodes), N_BOTTOM (85 nodes), N_PIN (node 1), N_RP (node 999999).
6. 85 kinematic tie equations in DOF 2 (u_y) connecting N_TOP to RP 999999.
7. Linear-elastic material properties: E = 210.0 kN/mm^2, nu = 0.3.
8. Static step with displacement target u_y = 0.002000 mm (C1-2 terminal target).
9. Element output requesting S, MISESERI, MISESAVG, EVOL.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
C4_REF_INP = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "147_c4_corrected_reference", "M1_C4_CORRECTED_PACKAGE147_REF.inp"
)
PKG153_DIR = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "153_c4_companion_miseseri"
)


def compute_sha256(path: str) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest().upper()


def extract_c4_mesh_components(inp_path: str):
    """Extracts nodes, layer 1 phase elements (to re-label as CPE4), and equations/nsets."""
    nodes_lines = []
    elements_lines = []
    nsets_lines = []
    equations_lines = []

    current_section = None

    with open(inp_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("**"):
                continue

            if stripped.startswith("*"):
                upper = stripped.upper()
                if (upper == "*NODE" or upper.startswith("*NODE,")) and "OUTPUT" not in upper and "PRINT" not in upper:
                    current_section = "NODE"
                    continue
                elif (upper == "*ELEMENT" or upper.startswith("*ELEMENT,")) and "OUTPUT" not in upper and "PRINT" not in upper:
                    if "PHASE_QUADS" in upper or "TYPE=U1" in upper:
                        current_section = "PHASE_QUADS"
                    else:
                        current_section = "OTHER_ELEMENT"
                    continue
                elif upper.startswith("*NSET"):
                    current_section = "NSET"
                    nsets_lines.append(line)
                    continue
                elif upper.startswith("*EQUATION"):
                    current_section = "EQUATION"
                    equations_lines.append(line)
                    continue
                else:
                    current_section = "IGNORE"
                    continue

            parts = [p.strip() for p in stripped.split(",")]
            if current_section == "NODE":
                if len(parts) >= 3 and parts[0].isdigit():
                    nodes_lines.append(line)
            elif current_section == "PHASE_QUADS":
                if len(parts) >= 5 and parts[0].isdigit():
                    elements_lines.append(line)
            elif current_section == "NSET":
                nsets_lines.append(line)
            elif current_section == "EQUATION":
                equations_lines.append(line)

    return nodes_lines, elements_lines, nsets_lines, equations_lines


def build_package153(displacement_target: float = 0.002000):
    os.makedirs(PKG153_DIR, exist_ok=True)
    out_inp = os.path.join(PKG153_DIR, "M1_C4_COMPANION_MISESERI.inp")

    nodes_lines, elements_lines, nsets_lines, equations_lines = extract_c4_mesh_components(C4_REF_INP)

    assert len(elements_lines) == 7056, f"Expected 7056 elements, got {len(elements_lines)}"

    with open(out_inp, "w", encoding="utf-8") as f:
        f.write("*Heading\n")
        f.write("** Mode-I Production C4 Companion Continuum Model for MISESERI Recovery\n")
        f.write(f"** State: Stage C1-2 Target State (uy = {displacement_target:.9f} mm)\n")
        f.write("** Mesh: 7,056 CPE4 Continuum Quads, 7,265 Physical Nodes + RP 999999\n")
        f.write("** Protocol Version: 2 (Task F1597, Package 153)\n")
        f.write("*Preprint, echo=NO, model=NO, history=NO, contact=NO\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("** NODES (7,265 physical nodes + RP 999999)\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*Node\n")
        for l in nodes_lines:
            f.write(l)

        f.write("** ----------------------------------------------------------\n")
        f.write("** CONTINUUM CPE4 ELEMENTS (7,056 Quads)\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*Element, type=CPE4, elset=ALL_QUADS\n")
        for l in elements_lines:
            f.write(l)

        f.write("** ----------------------------------------------------------\n")
        f.write("** NODE SETS\n")
        f.write("** ----------------------------------------------------------\n")
        for l in nsets_lines:
            f.write(l)

        f.write("** ----------------------------------------------------------\n")
        f.write("** EQUATIONS: Tie all top nodes to RP in DOF 2 (u_y)\n")
        f.write("** ----------------------------------------------------------\n")
        for l in equations_lines:
            f.write(l)

        f.write("** ----------------------------------------------------------\n")
        f.write("** SOLID SECTION & ISOTROPIC ELASTICITY\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*Solid Section, elset=ALL_QUADS, material=STEEL\n")
        f.write("1.0\n")
        f.write("*Material, name=STEEL\n")
        f.write("*Elastic\n")
        f.write("210.0, 0.3\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("** BOUNDARY CONDITIONS & STATIC ELASTIC SOLVE\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*Boundary\n")
        f.write("N_PIN, 1, 1, 0.0\n")
        f.write("N_BOTTOM, 2, 2, 0.0\n")
        f.write("999999, 1, 1, 0.0\n")
        f.write("*Step, name=STATIC_ELASTIC, perturb\n")
        f.write("*Static\n")
        f.write("*Boundary\n")
        f.write(f"999999, 2, 2, {displacement_target:.9f}\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("** ELEMENT OUTPUT FOR AUTHENTIC MISESERI RECOVERY\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*Output, field, frequency=1\n")
        f.write("*Element Output, elset=ALL_QUADS\n")
        f.write("S, MISESERI, MISESAVG, EVOL\n")
        f.write("*Node Output\n")
        f.write("U, RF\n")
        f.write("*Output, history, frequency=1\n")
        f.write("*Node Output, nset=N_RP\n")
        f.write("RF2, U2\n")
        f.write("*End Step\n")

    print(f"Generated input deck: {out_inp}")
    inp_sha = compute_sha256(out_inp)
    print(f"Input deck SHA-256: {inp_sha}")

    # Build package manifest
    pkg_manifest = {
        "package_number": 153,
        "job_name": "M1_C4_COMPANION_MISESERI",
        "purpose": "Production C4 companion continuum static-elastic model (7,056 CPE4 quads, 7,265 nodes) to extract authentic MISESERI/MISESAVG error indicators for Method C C4->C5 adaptive remeshing.",
        "mesh_provenance": {
            "source_deck": "models/pandey_kumar_mode1/147_c4_corrected_reference/M1_C4_CORRECTED_PACKAGE147_REF.inp",
            "source_sha256": compute_sha256(C4_REF_INP),
            "elements": 7056,
            "nodes": 7265,
            "element_type": "CPE4",
            "duplicate_slit_flank_pairs": 40,
            "ligament_nodes": 45
        },
        "loading": {
            "step_name": "STATIC_ELASTIC",
            "perturbation": True,
            "prescribed_u2_mm": displacement_target
        },
        "output_fields_requested": ["S", "MISESERI", "MISESAVG", "EVOL", "U", "RF"],
        "files": {
            "M1_C4_COMPANION_MISESERI.inp": inp_sha
        }
    }
    manifest_path = os.path.join(PKG153_DIR, "PACKAGE_MANIFEST.json")
    with open(manifest_path, "w") as f:
        json.dump(pkg_manifest, f, indent=2)

    # Build execution manifest
    exec_manifest = {
        "schema": 1,
        "package_number": 153,
        "job_name": "M1_C4_COMPANION_MISESERI",
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "input_deck": "M1_C4_COMPANION_MISESERI.inp",
        "input_deck_sha256": inp_sha,
        "execution_mode": "SERIAL_STANDALONE_CONTINUUM",
        "cpus": 1,
        "memory_gb": 8,
        "walltime_hours": 1,
        "queue": "normal_imfdfkmq",
        "dependency": "C1_2_TERMINAL_EQUILIBRIUM_ACCEPTANCE"
    }
    exec_manifest_path = os.path.join(PKG153_DIR, "EXECUTION_MANIFEST.json")
    with open(exec_manifest_path, "w") as f:
        json.dump(exec_manifest, f, indent=2)

    # Build PBS script
    pbs_script = f"""#!/bin/bash
#PBS -N M1_C4_COMPANION_MISESERI
#PBS -l select=1:ncpus=1:mem=8gb
#PBS -l walltime=01:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail
cd "$PBS_O_WORKDIR"

export JOB_NAME="M1_C4_COMPANION_MISESERI"
export NOTIFICATION_CONFIG="${{NOTIFICATION_CONFIG:-${{HOME}}/.config/adaptive-remeshing/notifications.env}}"
source ./job_notifications.sh
notification_load_config
notification_install_terminal_trap
notify_start

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

abaqus job=M1_C4_COMPANION_MISESERI input=M1_C4_COMPANION_MISESERI.inp interactive
EXIT_CODE=$?

echo "Companion solve finished with exit code: ${{EXIT_CODE}}"
exit ${{EXIT_CODE}}
"""
    pbs_path = os.path.join(PKG153_DIR, "submit_M1_C4_COMPANION_MISESERI.pbs")
    with open(pbs_path, "w", newline="\n") as f:
        f.write(pbs_script)

    # Build datacheck runner
    dc_script = """#!/bin/bash
set -euo pipefail
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus datacheck job=M1_C4_COMPANION_MISESERI_DC input=M1_C4_COMPANION_MISESERI.inp interactive
EXIT_CODE=$?
echo "Datacheck exit code: ${EXIT_CODE}"
exit ${EXIT_CODE}
"""
    dc_path = os.path.join(PKG153_DIR, "run_datacheck.sh")
    with open(dc_path, "w", newline="\n") as f:
        f.write(dc_script)

    print("Package 153 generation complete.")


if __name__ == "__main__":
    build_package153()
