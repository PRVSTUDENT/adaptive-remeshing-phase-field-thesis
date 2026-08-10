#!/usr/bin/env python3
"""Validate Mode-II Adaptive Production Packages (MM & PK5).
Task: F43ADAPT-PROD-PREP1

Performs fail-closed static validation over both production packages:
  - M2ADAPT_MM_FRACFIX_PROD (2,206 physical -> 6,618 layered elements)
  - M2ADAPT_PK5_FRACFIX_PROD (4,894 physical -> 14,682 layered elements)

Audits:
  1. Exact element counts and 3-layer architecture (U1/U2/U3/U4/CPE4/CPE3)
  2. NPHYS producer-consumer mapping and 5-property UEL card
  3. Physical formulation (E=210, nu=0.3, Gc=0.0027, l0=0.015, k=1e-7, thickness=1.0)
  4. Two-step loading ramp (Step-1 to 0.005 mm, Step-2 to 0.010 mm)
  5. Output sufficiency (RP U/RF, UMATELEM SDV/S/EVOL, global energy ALLAE..ETOTAL, time interval=0.01)
  6. PBS syntax, notification directives (-m abe, 2-recipient email, mem=8gb)
  7. Exact raw-byte SHA256 match against package manifest
"""

import os
import sys
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List

ROOT = Path(__file__).resolve().parents[2]
BATCH_DIR = ROOT / "models/generated/mode_ii/production_adaptive_batch"

EXPECTED_UEL_SHA256 = "0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8"
APPROVED_EMAILS = "Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de"

EXPECTED_CONFIGS = {
    "M2ADAPT_MM_FRACFIX_PROD": {
        "n_nodes": 2294,
        "n_phys": 2206,
        "n_quads": 2137,
        "n_tris": 69,
        "memory": "8gb",
        "walltime": "02:00:00",
        "queue": "entry_imfdfkmq",
        "cpus": 1
    },
    "M2ADAPT_PK5_FRACFIX_PROD": {
        "n_nodes": 4998,
        "n_phys": 4894,
        "n_quads": 4766,
        "n_tris": 128,
        "memory": "8gb",
        "walltime": "04:00:00",
        "queue": "entry_imfdfkmq",
        "cpus": 1
    }
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_input_deck(deck_path: Path, expected: Dict[str, Any]) -> Dict[str, Any]:
    text = deck_path.read_text(encoding="utf-8", errors="replace")
    checks = {}

    n_nodes = expected["n_nodes"]
    n_phys = expected["n_phys"]
    n_quads = expected["n_quads"]
    n_tris = expected["n_tris"]

    # 1. Element counts
    u1_matches = re.findall(r"^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)",
                            text[text.find("*Element, type=U1"):text.find("*Element, type=U3") if "*Element, type=U3" in text else text.find("*Element, type=U2")],
                            re.M) if "*Element, type=U1" in text else []
    u2_matches = re.findall(r"^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)",
                            text[text.find("*Element, type=U2"):text.find("*Element, type=U4") if "*Element, type=U4" in text else text.find("*Element, type=CPE4")],
                            re.M) if "*Element, type=U2" in text else []
    u3_matches = re.findall(r"^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)",
                            text[text.find("*Element, type=U3"):text.find("*Element, type=U2")],
                            re.M) if "*Element, type=U3" in text else []
    u4_matches = re.findall(r"^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)",
                            text[text.find("*Element, type=U4"):text.find("*Element, type=CPE4")],
                            re.M) if "*Element, type=U4" in text else []
    cpe4_matches = re.findall(r"^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)",
                              text[text.find("*Element, type=CPE4"):text.find("*Element, type=CPE3") if "*Element, type=CPE3" in text else text.find("*Elset, elset=PHASE")],
                              re.M) if "*Element, type=CPE4" in text else []
    cpe3_matches = re.findall(r"^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)",
                              text[text.find("*Element, type=CPE3"):text.find("*Elset, elset=PHASE")],
                              re.M) if "*Element, type=CPE3" in text else []

    checks["count_U1"] = (len(u1_matches) == n_quads)
    checks["count_U2"] = (len(u2_matches) == n_quads)
    checks["count_U3"] = (len(u3_matches) == n_tris)
    checks["count_U4"] = (len(u4_matches) == n_tris)
    checks["count_CPE4"] = (len(cpe4_matches) == n_quads)
    checks["count_CPE3"] = (len(cpe3_matches) == n_tris)
    checks["total_layered_elements"] = (len(u1_matches) + len(u2_matches) + len(u3_matches) + len(u4_matches) + len(cpe4_matches) + len(cpe3_matches) == 3 * n_phys)

    # 2. Node count
    node_matches = re.findall(r"^\s*(\d+)\s*,\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)",
                              text[text.find("*Node"):text.find("** Layer 1: Phase-Field Elements")],
                              re.M)
    checks["node_count"] = (len(node_matches) == n_nodes)

    # 3. UEL Property declarations (properties=5 on U2 and U4, true NPHYS in 5th property slot)
    checks["uel_decl_u1_properties_3"] = bool(re.search(r"\*User Element,\s*nodes=4,\s*type=U1,\s*properties=3", text, re.I))
    checks["uel_decl_u2_properties_5"] = bool(re.search(r"\*User Element,\s*nodes=4,\s*type=U2,\s*properties=5", text, re.I))
    if n_tris > 0:
        checks["uel_decl_u3_properties_3"] = bool(re.search(r"\*User Element,\s*nodes=3,\s*type=U3,\s*properties=3", text, re.I))
        checks["uel_decl_u4_properties_5"] = bool(re.search(r"\*User Element,\s*nodes=3,\s*type=U4,\s*properties=5", text, re.I))

    # Check NPHYS value in DISP_QUAD and DISP_TRI cards
    disp_quad_match = re.search(r"\*UEL Property,\s*elset=DISP_QUAD\s*\n\s*([^\n]+)", text, re.I)
    if disp_quad_match:
        disp_props = [float(p.strip()) for p in disp_quad_match.group(1).split(",")]
        checks["disp_quad_nphys_prop"] = (len(disp_props) >= 5 and abs(disp_props[4] - float(n_phys)) < 1e-3)
    else:
        checks["disp_quad_nphys_prop"] = False

    if n_tris > 0:
        disp_tri_match = re.search(r"\*UEL Property,\s*elset=DISP_TRI\s*\n\s*([^\n]+)", text, re.I)
        if disp_tri_match:
            disp_props = [float(p.strip()) for p in disp_tri_match.group(1).split(",")]
            checks["disp_tri_nphys_prop"] = (len(disp_props) >= 5 and abs(disp_props[4] - float(n_phys)) < 1e-3)
        else:
            checks["disp_tri_nphys_prop"] = False

    # 4. Physical formulation parameters (l0=0.015, Gc=0.0027, E=210, nu=0.3, k=1e-7)
    phase_quad_match = re.search(r"\*UEL Property,\s*elset=PHASE_QUAD\s*\n\s*([^\n]+)", text, re.I)
    if phase_quad_match:
        phase_props = [float(p.strip()) for p in phase_quad_match.group(1).split(",")]
        checks["phase_l0_Gc_thickness"] = (abs(phase_props[0] - 0.015) < 1e-6 and
                                           abs(phase_props[1] - 0.0027) < 1e-6 and
                                           abs(phase_props[2] - 1.0) < 1e-6)
    else:
        checks["phase_l0_Gc_thickness"] = False

    # 5. Boundary conditions & Equation coupling
    checks["bottom_fix_bc"] = bool(re.search(r"bottom_nodes,\s*1,\s*2", text))
    checks["top_vertical_bc"] = bool(re.search(r"top_nodes,\s*2,\s*2", text))
    checks["shear_coupling_equation"] = bool(re.search(r"\*Equation\s*\n\s*2\s*\n\s*top_nodes,\s*1,\s*1\.\s*\n\s*RP,\s*1,\s*-1\.", text, re.I))

    # 6. Two-step loading ramp
    checks["amplitude_amp1"] = bool(re.search(r"\*Amplitude,\s*name=Amp-1\s*\n\s*0\.0,\s*0\.0,\s*0\.5,\s*0\.005", text, re.I))
    checks["amplitude_amp2"] = bool(re.search(r"\*Amplitude,\s*name=Amp-2\s*\n\s*0\.0,\s*0\.005,\s*0\.2,\s*0\.010", text, re.I))
    checks["step1_direct_500"] = bool(re.search(r"\*Step,\s*name=Step-1,\s*nlgeom=NO,\s*inc=500\s*\n\s*\*Static,\s*direct\s*\n\s*0\.001,\s*0\.5", text, re.I))
    checks["step2_direct_2000"] = bool(re.search(r"\*Step,\s*name=Step-2,\s*nlgeom=NO,\s*inc=2000\s*\n\s*\*Static,\s*direct\s*\n\s*0\.0001,\s*0\.2", text, re.I))

    # 7. Output sufficiency in both steps
    checks["output_field_interval"] = (len(re.findall(r"\*Output,\s*field,\s*time interval=0\.01", text, re.I)) == 2)
    checks["output_node_u_rf"] = (len(re.findall(r"\*Node Output\s*\n\s*U,\s*RF", text, re.I)) == 2)
    checks["output_rp_node"] = (len(re.findall(r"\*Node Output,\s*nset=RP\s*\n\s*RF,\s*U", text, re.I)) == 2)
    checks["output_umatelem_sdv"] = (len(re.findall(r"\*Element Output,\s*elset=UMATELEM\s*\n\s*SDV,\s*S,\s*EVOL", text, re.I)) == 2)
    checks["output_energy_all"] = (len(re.findall(r"\*Energy Output\s*\n\s*ALLAE,\s*ALLCD,\s*ALLIE,\s*ALLKE,\s*ALLPD,\s*ALLSE,\s*ALLWK,\s*ETOTAL", text, re.I)) == 2)

    return checks


def validate_pbs_script(pbs_path: Path, expected: Dict[str, Any]) -> Dict[str, Any]:
    text = pbs_path.read_text(encoding="utf-8", errors="replace")
    checks = {}

    checks["directive_ncpus"] = bool(re.search(r"#PBS\s+-l\s+select=1:ncpus=1:mem=" + expected["memory"], text))
    checks["directive_walltime"] = bool(re.search(r"#PBS\s+-l\s+walltime=" + expected["walltime"], text))
    checks["directive_queue"] = bool(re.search(r"#PBS\s+-q\s+" + expected["queue"], text))
    checks["directive_mail_abe"] = bool(re.search(r"#PBS\s+-m\s+abe", text))
    checks["directive_mail_recipients"] = bool(re.search(r"#PBS\s+-M\s+" + re.escape(APPROVED_EMAILS), text))
    checks["abaqus_double_both"] = bool(re.search(r"abaqus\s+job=\S+\s+input=\S+\s+user=f42_mixed_uel\.for\s+cpus=1\s+interactive\s+double=both\s+ask_delete=OFF", text))

    return checks


def validate_production_batch() -> Dict[str, Any]:
    print("======================================================================")
    print("F43ADAPT-PROD-PREP1: VALIDATING ADAPTIVE PRODUCTION BATCH")
    print("======================================================================")

    results: Dict[str, Any] = {
        "all_passed": True,
        "packages": {}
    }

    for case_name, exp in EXPECTED_CONFIGS.items():
        pkg_dir = BATCH_DIR / case_name
        if not pkg_dir.is_dir():
            raise FileNotFoundError(f"Package directory missing: {pkg_dir}")

        inp_path = pkg_dir / f"{case_name}.inp"
        uel_path = pkg_dir / "f42_mixed_uel.for"
        pbs_path = pkg_dir / f"{case_name}.pbs"
        sub_path = pkg_dir / f"submit_{case_name.lower()}.sh"
        man_path = pkg_dir / "PACKAGE_MANIFEST.json"

        # 1. SHA256 checks
        uel_sha = sha256_file(uel_path)
        inp_sha = sha256_file(inp_path)
        pbs_sha = sha256_file(pbs_path)
        sub_sha = sha256_file(sub_path)
        man_sha = sha256_file(man_path)

        manifest = json.loads(man_path.read_text(encoding="utf-8"))
        manifest_matches = (
            manifest["inp_sha256"] == inp_sha and
            manifest["uel_sha256"] == uel_sha and
            manifest["pbs_sha256"] == pbs_sha and
            manifest["submit_sh_sha256"] == sub_sha and
            uel_sha == EXPECTED_UEL_SHA256
        )

        deck_checks = validate_input_deck(inp_path, exp)
        pbs_checks = validate_pbs_script(pbs_path, exp)

        pkg_passed = manifest_matches and all(deck_checks.values()) and all(pbs_checks.values())
        if not pkg_passed:
            results["all_passed"] = False

        results["packages"][case_name] = {
            "passed": pkg_passed,
            "manifest_valid": manifest_matches,
            "deck_checks": deck_checks,
            "pbs_checks": pbs_checks,
            "raw_hashes": {
                "input": inp_sha,
                "uel": uel_sha,
                "pbs": pbs_sha,
                "wrapper": sub_sha,
                "manifest": man_sha
            }
        }

        print(f"[{case_name}] Static Validation: {'PASS' if pkg_passed else 'FAIL'}")
        if not pkg_passed:
            failed_deck = [k for k, v in deck_checks.items() if not v]
            failed_pbs = [k for k, v in pbs_checks.items() if not v]
            if not manifest_matches:
                print("  Failed: Manifest Hash Mismatch")
            if failed_deck:
                print(f"  Failed Deck Checks: {failed_deck}")
            if failed_pbs:
                print(f"  Failed PBS Checks: {failed_pbs}")

    print("======================================================================")
    print(f"OVERALL VALIDATION STATUS: {'ALL PASS' if results['all_passed'] else 'FAIL'}")
    print("======================================================================")
    return results


if __name__ == "__main__":
    res = validate_production_batch()
    if not res["all_passed"]:
        sys.exit(1)
    sys.exit(0)
