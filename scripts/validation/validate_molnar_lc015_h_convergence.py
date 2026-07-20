#!/usr/bin/env python3
"""Static validation for Molnar lc=0.015 h-convergence study cases."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
PRESERVED_INP = ROOT / "models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.inp"
PRESERVED_FOR = ROOT / "models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.for"
EXPECTED_INP = "89ce3f32e396b0e484be6753a272dd6bbb2a2f9daff426d6a57419f57d665b72"
EXPECTED_FOR = "18944e5bb2a3b7973fd0d4bff03f8e078eef667965343d8a29156d093f53f5f1"
STUDY_DIR = ROOT / "models/generated/molnar_gravouil_2017/h_convergence_lc015"
OUT_DIR = ROOT / "results/validation/molnar_lc015_h_convergence"
LC = 0.015
TOL = 1.0e-9


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def parse_scientific(text: str) -> dict:
    def amp(name: str):
        m = re.search(rf"\*Amplitude, name={re.escape(name)}\s*\n([^\n*]+)", text, re.I)
        if not m:
            return None
        return [float(x.strip()) for x in m.group(1).split(",") if x.strip()]

    def step_inc(name: str):
        m = re.search(rf"\*Step, name={re.escape(name)},[^\n]*inc=(\d+)", text, re.I)
        return int(m.group(1)) if m else None

    def static_after(name: str):
        m = re.search(
            rf"\*Step, name={re.escape(name)},[^\n]*\n\*Static, direct\s*\n([^\n*]+)",
            text,
            re.I,
        )
        if not m:
            return None
        return [float(x.strip()) for x in m.group(1).split(",") if x.strip()]

    def uel_props(elset: str):
        m = re.search(
            rf"\*Uel property, elset={re.escape(elset)}\s*\n([^\n*]+)",
            text,
            re.I,
        )
        if not m:
            return None
        return [float(x.strip()) for x in m.group(1).split(",") if x.strip()]

    umat = re.search(r"\*User Material, constants=2\s*\n([^\n*]+)", text, re.I)
    thickness = re.search(r"\*Solid Section, elset=umatelem, material=umatelem\s*\n([^\n*]+)", text, re.I)
    return {
        "u1_props": uel_props("PLATE"),
        "u2_props": uel_props("PLATE_SS"),
        "umat_props": [float(x.strip()) for x in umat.group(1).split(",") if x.strip()] if umat else None,
        "thickness": float(thickness.group(1).strip()) if thickness else None,
        "amp1": amp("Amp-1"),
        "amp2": amp("Amp-2"),
        "step1_inc": step_inc("Step-1"),
        "step2_inc": step_inc("Step-2"),
        "step1_static": static_after("Step-1"),
        "step2_static": static_after("Step-2"),
        "has_u1": bool(re.search(r"type=U1", text, re.I)),
        "has_u2": bool(re.search(r"type=U2", text, re.I)),
        "has_cps4": bool(re.search(r"type=CPS4", text, re.I)),
        "has_rp": bool(re.search(r"\*Nset, nset=RP", text, re.I)),
        "has_bottom": bool(re.search(r"\*Nset, nset=bottom", text, re.I)),
        "has_top": bool(re.search(r"\*Nset, nset=top", text, re.I)),
        "has_bottoml": bool(re.search(r"\*Nset, nset=bottoml", text, re.I)),
        "has_topl": bool(re.search(r"\*Nset, nset=topl", text, re.I)),
        "has_equation": "*Equation" in text,
        "has_sdv": bool(re.search(r"SDV", text, re.I)),
        "total_disp": amp("Amp-2")[3] if amp("Amp-2") and len(amp("Amp-2")) >= 4 else None,
    }


def almost_equal(a, b, tol=TOL) -> bool:
    if a is None or b is None:
        return a is b
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            return False
        return all(abs(float(x) - float(y)) <= tol for x, y in zip(a, b))
    return abs(float(a) - float(b)) <= tol


def n_elem_values(text: str) -> list[int]:
    return [int(m) for m in re.findall(r"N_ELEM=(\d+)", text)]


def physical_from_deck(text: str) -> int | None:
    m = re.search(r"\*Elset, elset=PLATE, generate\s*\n\s*1,\s*(\d+),\s*1", text, re.I)
    return int(m.group(1)) if m else None


def load_stats(case_dir: Path) -> dict:
    path = case_dir / "generation_manifest.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def lf_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def validate_h0() -> dict:
    case_dir = STUDY_DIR / "H0_exact"
    deck = case_dir / "SingleNotch.inp"
    fortran = case_dir / "SingleNotch.for"
    checks = {}
    # Working-tree preserved files may be CRLF on Windows; README documents those hashes.
    checks["preserved_inp_working_tree_sha"] = sha256(PRESERVED_INP) == EXPECTED_INP
    checks["preserved_for_working_tree_sha"] = sha256(PRESERVED_FOR) == EXPECTED_FOR
    checks["h0_deck_exists"] = deck.exists()
    checks["h0_for_exists"] = fortran.exists()
    # Tracked H0 copies are LF-normalized for Git/HPC hash consistency and must match
    # the LF-normalized preserved author content.
    checks["h0_matches_lf_normalized_preserved_deck"] = (
        deck.exists() and deck.read_bytes() == lf_bytes(PRESERVED_INP)
    )
    checks["h0_matches_lf_normalized_preserved_source"] = (
        fortran.exists() and fortran.read_bytes() == lf_bytes(PRESERVED_FOR)
    )
    checks["byte_identical_to_preserved_scientific_content"] = (
        checks["h0_matches_lf_normalized_preserved_deck"]
        and checks["h0_matches_lf_normalized_preserved_source"]
    )
    sci = parse_scientific(deck.read_text(encoding="utf-8", errors="replace")) if deck.exists() else {}
    checks["lc_015"] = almost_equal(sci.get("u1_props", [None])[0], 0.015) if sci.get("u1_props") else False
    checks["gc"] = almost_equal(sci.get("u1_props", [None, None])[1], 0.0027) if sci.get("u1_props") else False
    checks["E"] = almost_equal(sci.get("u2_props", [None])[0], 210.0) if sci.get("u2_props") else False
    checks["nu"] = almost_equal(sci.get("u2_props", [None, None])[1], 0.3) if sci.get("u2_props") else False
    checks["k"] = almost_equal(sci.get("u2_props", [None, None, None, None])[3], 1e-7) if sci.get("u2_props") else False
    classification = "exact_author_inputs_verified" if all(checks.values()) else "exact_author_inputs_failed"
    runnable = classification == "exact_author_inputs_verified"
    report = {
        "case": "H0",
        "classification": classification,
        "runnable": runnable,
        "checks": checks,
        "scientific": sci,
        "hashes": {
            "deck": sha256(deck) if deck.exists() else None,
            "source": sha256(fortran) if fortran.exists() else None,
        },
        "stats": load_stats(case_dir),
    }
    return report


def validate_generated(case_key: str, folder: str, deck_name: str, for_name: str, target_h: float, require_pub: bool = False) -> dict:
    case_dir = STUDY_DIR / folder
    deck = case_dir / deck_name
    fortran = case_dir / for_name
    h0_text = (STUDY_DIR / "H0_exact" / "SingleNotch.inp").read_text(encoding="utf-8", errors="replace")
    h0_sci = parse_scientific(h0_text)
    text = deck.read_text(encoding="utf-8", errors="replace") if deck.exists() else ""
    for_text = fortran.read_text(encoding="utf-8", errors="replace") if fortran.exists() else ""
    sci = parse_scientific(text)
    physical = physical_from_deck(text)
    n_elems = n_elem_values(for_text)
    stats = load_stats(case_dir)
    checks = {
        "deck_exists": deck.exists(),
        "fortran_exists": fortran.exists(),
        "material_E": almost_equal(sci.get("u2_props"), h0_sci.get("u2_props")),
        "lc_gc_thickness_u1": almost_equal(sci.get("u1_props"), h0_sci.get("u1_props")),
        "umat_residual": almost_equal(sci.get("umat_props"), h0_sci.get("umat_props")),
        "thickness_section": almost_equal(sci.get("thickness"), h0_sci.get("thickness")),
        "amp1": almost_equal(sci.get("amp1"), h0_sci.get("amp1")),
        "amp2": almost_equal(sci.get("amp2"), h0_sci.get("amp2")),
        "step1_inc": sci.get("step1_inc") == h0_sci.get("step1_inc"),
        "step2_inc": sci.get("step2_inc") == h0_sci.get("step2_inc"),
        "step1_static": almost_equal(sci.get("step1_static"), h0_sci.get("step1_static")),
        "step2_static": almost_equal(sci.get("step2_static"), h0_sci.get("step2_static")),
        "total_prescribed_displacement": almost_equal(sci.get("total_disp"), h0_sci.get("total_disp")),
        "has_u1_u2_cps4": all([sci.get("has_u1"), sci.get("has_u2"), sci.get("has_cps4")]),
        "has_bc_sets": all([sci.get("has_rp"), sci.get("has_bottom"), sci.get("has_top"), sci.get("has_bottoml"), sci.get("has_topl")]),
        "has_equation": sci.get("has_equation") is True,
        "has_sdv_output": sci.get("has_sdv") is True,
        "n_elem_matches_physical": physical is not None and n_elems == [physical, physical],
        "only_n_elem_changed": (
            physical is not None
            and "N_ELEM=" in for_text
            and for_text.replace(f"N_ELEM={physical}", "N_ELEM=3930").replace("\r\n", "\n")
            == PRESERVED_FOR.read_text(encoding="utf-8").replace("\r\n", "\n")
        ),
        "negative_jacobian_zero": stats.get("negative_jacobian_count", 1) == 0,
        "target_h_recorded": abs(float(stats.get("local_target_h_mm", -1)) - target_h) < 1e-12,
        "corridor_h_near_target": (
            stats.get("actual_local_h_corridor_median") is not None
            and abs(float(stats["actual_local_h_corridor_median"]) - target_h) <= 0.25 * target_h
        ),
    }
    if require_pub:
        checks["publication_resolution_target"] = abs(target_h - 0.001) < 1e-12
        checks["publication_resolution_measured"] = (
            stats.get("actual_local_h_corridor_median") is not None
            and abs(float(stats["actual_local_h_corridor_median"]) - 0.001) <= 1.5e-4
        )
    passed = all(checks.values())
    classification = "h_convergence_static_validation_pass" if passed else "h_convergence_static_validation_fail"
    if require_pub and passed:
        classification = "h_convergence_static_validation_pass"
        pub_ok = checks.get("publication_resolution_measured", False)
    else:
        pub_ok = False
    report = {
        "case": case_key,
        "classification": classification,
        "publication_resolution_verified": bool(require_pub and pub_ok),
        "runnable": passed,
        "checks": checks,
        "scientific": sci,
        "physical_elements": physical,
        "n_elem": n_elems,
        "hashes": {
            "deck": sha256(deck) if deck.exists() else None,
            "source": sha256(fortran) if fortran.exists() else None,
        },
        "stats": stats,
    }
    return report


def check_repeatability() -> dict:
    script = ROOT / "scripts/model_generation/build_molnar_lc015_h_convergence.py"
    results = {}
    for case, folder, deck_name, h in [
        ("H1", "H1_h0025", "H1_h0025.inp", 0.0025),
        ("H2-PUB", "H2_pub_h0010", "H2_pub_h0010.inp", 0.001),
    ]:
        expected = sha256(STUDY_DIR / folder / deck_name) if (STUDY_DIR / folder / deck_name).exists() else None
        with tempfile.TemporaryDirectory(prefix="hconv_det_") as d1, tempfile.TemporaryDirectory(prefix="hconv_det_") as d2:
            ok = True
            hashes = []
            for d in (d1, d2):
                out = Path(d) / "out"
                rc = subprocess.run(
                    ["python", str(script), "--out-root", str(out), "--cases", case],
                    cwd=str(ROOT),
                    check=False,
                    capture_output=True,
                    text=True,
                )
                if rc.returncode != 0:
                    ok = False
                    break
                # Find generated deck
                deck = next(out.rglob("*.inp"), None)
                if deck is None:
                    ok = False
                    break
                hashes.append(sha256(deck))
            results[case] = {
                "repeatable": ok and len(hashes) == 2 and hashes[0] == hashes[1],
                "matches_committed": ok and expected is not None and hashes and hashes[0] == expected,
                "hashes": hashes,
                "expected": expected,
            }
    return results


def write_report(path: Path, report: dict) -> None:
    lines = [
        f"# Static Validation: {report['case']}",
        "",
        f"Classification: `{report['classification']}`",
        f"Runnable: `{report['runnable']}`",
        "",
        "## Checks",
        "",
    ]
    for key, value in report.get("checks", {}).items():
        lines.append(f"- `{key}`: `{value}`")
    if "publication_resolution_verified" in report:
        lines.extend(["", f"publication_resolution_verified: `{report['publication_resolution_verified']}`"])
    lines.extend(["", "## Hashes", ""])
    for key, value in report.get("hashes", {}).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Physical elements", "", f"`{report.get('physical_elements')}`", ""])
    write_text(path, "\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-repeatability", action="store_true")
    args = parser.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    h0 = validate_h0()
    h1 = validate_generated("H1", "H1_h0025", "H1_h0025.inp", "H1_h0025.for", 0.0025)
    h2 = validate_generated("H2-PUB", "H2_pub_h0010", "H2_pub_h0010.inp", "H2_pub_h0010.for", 0.001, require_pub=True)

    write_report(OUT_DIR / "H0_STATIC_VALIDATION.md", h0)
    write_report(OUT_DIR / "H1_STATIC_VALIDATION.md", h1)
    write_report(OUT_DIR / "H2_PUB_STATIC_VALIDATION.md", h2)

    rows = []
    for rep in (h0, h1, h2):
        for k, v in rep.get("checks", {}).items():
            rows.append([rep["case"], k, v])
    with (OUT_DIR / "STUDY_EQUIVALENCE_MATRIX.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["case", "check", "passed"])
        writer.writerows(rows)

    repeat = {} if args.skip_repeatability else check_repeatability()
    all_ok = h0["runnable"] and h1["runnable"] and h2["runnable"]
    if repeat:
        all_ok = all_ok and all(v.get("repeatable") and v.get("matches_committed") for v in repeat.values())

    decision = {
        "overall_pass": all_ok,
        "H0": h0["classification"],
        "H1": h1["classification"],
        "H2-PUB": h2["classification"],
        "H2_publication_resolution_verified": h2.get("publication_resolution_verified"),
        "runnable": {
            "H0": h0["runnable"],
            "H1": h1["runnable"],
            "H2-PUB": h2["runnable"],
        },
        "element_counts": {
            "H0": h0.get("stats", {}).get("physical_element_count"),
            "H1": h1.get("physical_elements"),
            "H2-PUB": h2.get("physical_elements"),
        },
        "measured_local_h_corridor_median": {
            "H0": h0.get("stats", {}).get("actual_local_h_corridor_median"),
            "H1": h1.get("stats", {}).get("actual_local_h_corridor_median"),
            "H2-PUB": h2.get("stats", {}).get("actual_local_h_corridor_median"),
        },
        "repeatability": repeat,
    }
    write_text(OUT_DIR / "STUDY_EQUIVALENCE_DECISION.json", json.dumps(decision, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Study Equivalence Decision",
        "",
        f"Overall pass: `{all_ok}`",
        "",
        f"- H0: `{h0['classification']}` runnable=`{h0['runnable']}`",
        f"- H1: `{h1['classification']}` runnable=`{h1['runnable']}`",
        f"- H2-PUB: `{h2['classification']}` publication_resolution_verified=`{h2.get('publication_resolution_verified')}` runnable=`{h2['runnable']}`",
        "",
        "## Element counts",
        "",
        f"- H0: `{decision['element_counts']['H0']}`",
        f"- H1: `{decision['element_counts']['H1']}`",
        f"- H2-PUB: `{decision['element_counts']['H2-PUB']}`",
        "",
        "## Measured corridor local h (median)",
        "",
        f"- H0: `{decision['measured_local_h_corridor_median']['H0']}`",
        f"- H1: `{decision['measured_local_h_corridor_median']['H1']}`",
        f"- H2-PUB: `{decision['measured_local_h_corridor_median']['H2-PUB']}`",
        "",
        "## Repeatability",
        "",
        "```json",
        json.dumps(repeat, indent=2),
        "```",
        "",
    ]
    if not all_ok:
        lines.append("Decision: **stop without submission**.")
    else:
        lines.append("Decision: static validation pass; submission permitted for exactly three serial jobs.")
    write_text(OUT_DIR / "STUDY_EQUIVALENCE_DECISION.md", "\n".join(lines) + "\n")
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0 if all_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
