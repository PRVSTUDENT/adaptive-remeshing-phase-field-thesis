#!/usr/bin/env python3
"""Automatic static validators for unified Molnar full-generation decks.

Checks (no Abaqus execution):
  - duplicate node and element labels
  - missing nodes in connectivity
  - UEL/UMAT layer connectivity equality
  - expected label offsets
  - N_ELEM consistency in Fortran
  - required node/element sets
  - RP and loading definitions
  - phase-field convention documentation (d=0 intact, d=1 broken)
  - output tokens (baseline or MISESERI profile)
  - measured local h and h/lc
  - no silent inheritance of remeshing parameters from another case
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/preprocessing"))
from build_molnar_unified_deck import (  # noqa: E402
    almost_equal,
    parse_layered_deck,
    scientific_fields,
    sha256_file,
)

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML required") from exc


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_md(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def n_elem_values(text: str) -> list[int]:
    return [int(m) for m in re.findall(r"N_ELEM=(\d+)", text)]


def validate_deck(
    deck_path: Path,
    fortran_path: Path | None,
    config: dict[str, Any],
    *,
    require_miseseri: bool = False,
    role: str | None = None,
) -> dict[str, Any]:
    text = deck_path.read_text(encoding="utf-8", errors="replace")
    parsed = parse_layered_deck(text)
    sci = scientific_fields(text)
    nodes = parsed["nodes"]
    u1 = parsed["u1"]
    u2 = parsed["u2"]
    cps4 = parsed["cps4"]
    physical = len(u1)
    material = config["benchmark"]["material"]
    loading = config["benchmark"]["loading"]
    phase = config["benchmark"]["phase_field_convention"]
    lc = float(material["length_scale_mm"])

    checks: dict[str, bool] = {}
    details: dict[str, Any] = {}

    # Duplicate labels
    node_ids = list(nodes)
    checks["no_duplicate_node_labels"] = len(node_ids) == len(set(node_ids))
    all_eids = list(u1) + list(u2) + list(cps4)
    checks["no_duplicate_element_labels"] = len(all_eids) == len(set(all_eids))
    checks["u1_u2_cps4_disjoint_labels"] = (
        set(u1).isdisjoint(u2) and set(u1).isdisjoint(cps4) and set(u2).isdisjoint(cps4)
    )

    # Connectivity integrity
    missing_nodes = []
    for eid, data in list(u1.items()) + list(u2.items()) + list(cps4.items()):
        for n in data["connectivity"]:
            if n not in nodes:
                missing_nodes.append((eid, n))
    checks["no_missing_nodes_in_connectivity"] = len(missing_nodes) == 0
    details["missing_node_refs_count"] = len(missing_nodes)

    # Layer equality and offsets
    layer_equal = True
    for i in range(1, physical + 1):
        c1 = u1.get(i, {}).get("connectivity")
        c2 = u2.get(i + physical, {}).get("connectivity")
        c3 = cps4.get(i + 2 * physical, {}).get("connectivity")
        if not (c1 and c1 == c2 == c3):
            layer_equal = False
            break
    checks["uel_umat_layer_connectivity_equal"] = layer_equal
    checks["label_offset_u1"] = set(u1) == set(range(1, physical + 1))
    checks["label_offset_u2"] = set(u2) == set(range(physical + 1, 2 * physical + 1))
    checks["label_offset_cps4"] = set(cps4) == set(range(2 * physical + 1, 3 * physical + 1))
    checks["layer_counts_equal"] = len(u1) == len(u2) == len(cps4) and physical > 0

    # Fortran N_ELEM
    if fortran_path and fortran_path.exists():
        for_text = fortran_path.read_text(encoding="utf-8", errors="replace")
        nvals = n_elem_values(for_text)
        checks["n_elem_matches_physical"] = nvals == [physical, physical]
        preserved = (ROOT / config["benchmark"]["preserved_for"]).read_text(encoding="utf-8").replace("\r\n", "\n")
        checks["only_n_elem_changed"] = (
            for_text.replace("\r\n", "\n").replace(f"N_ELEM={physical}", "N_ELEM=3930") == preserved
        )
        details["n_elem_values"] = nvals
    else:
        checks["n_elem_matches_physical"] = False
        checks["only_n_elem_changed"] = False

    # Required sets
    for s in ("bottom", "top", "bottoml", "topl"):
        checks[f"nset_{s}"] = s in parsed["nsets"] and len(parsed["nsets"][s]) > 0
    checks["nset_rp"] = sci["has_rp"]
    checks["elset_umatelem"] = "umatelem" in parsed["elsets"] or bool(re.search(r"elset=umatelem", text, re.I))
    checks["elset_plate"] = bool(re.search(r"elset=PLATE", text, re.I))
    checks["elset_plate_ss"] = bool(re.search(r"elset=PLATE_SS", text, re.I))

    # Loading / RP
    checks["has_equation_rp_top"] = sci["has_equation"]
    is_elastic_pre = bool(
        re.search(r"loading_mode=elastic_precrack", text, re.I)
        or re.search(r"\*Amplitude, name=Amp-pre", text, re.I)
    )
    if is_elastic_pre:
        # Elastic pre-analysis: single Amp-pre to U_pre (authorized Stage C choice)
        m_amp = re.search(r"\*Amplitude, name=Amp-pre\s*\n([^\n*]+)", text, re.I)
        amp_vals = [float(x.strip()) for x in m_amp.group(1).split(",") if x.strip()] if m_amp else None
        u_pre = float(config.get("remeshing", {}).get("preanalysis", {}).get("u_pre_mm", 0.00464))
        # smoke profile may use smaller U
        if re.search(r"elastic_precrack_smoke|Step-smoke", text, re.I):
            u_pre = float(config.get("remeshing", {}).get("preanalysis", {}).get("u_smoke_mm", 0.001))
        checks["amp_pre_present"] = amp_vals is not None and len(amp_vals) >= 4
        checks["amp_pre_u"] = almost_equal(amp_vals[3] if amp_vals and len(amp_vals) >= 4 else None, u_pre)
        checks["single_pre_step"] = bool(re.search(r"\*Step, name=Step-(pre|smoke)", text, re.I))
        checks["no_fracture_two_step"] = sci.get("step2_inc") is None
    else:
        checks["amp1"] = almost_equal(sci["amp1"], loading["amplitude_1"])
        checks["amp2"] = almost_equal(sci["amp2"], loading["amplitude_2"])
        checks["step1_inc"] = sci["step1_inc"] == int(loading["step1_inc"])
        checks["step2_inc"] = sci["step2_inc"] == int(loading["step2_inc"])
        checks["step1_static"] = almost_equal(sci["step1_static"], loading["step1_static_direct"])
        checks["step2_static"] = almost_equal(sci["step2_static"], loading["step2_static_direct"])

    # Material / lc
    checks["u1_lc"] = almost_equal(sci["u1_props"][0] if sci["u1_props"] else None, material["length_scale_mm"])
    checks["u1_gc"] = almost_equal(sci["u1_props"][1] if sci["u1_props"] else None, material["critical_energy_release_rate_kN_per_mm"])
    checks["u2_E"] = almost_equal(sci["u2_props"][0] if sci["u2_props"] else None, material["youngs_modulus_kN_per_mm2"])
    checks["u2_nu"] = almost_equal(sci["u2_props"][1] if sci["u2_props"] else None, material["poissons_ratio"])

    # Phase-field convention documented in deck comments
    checks["phase_convention_documented"] = (
        f"intact={phase['intact']}" in text and f"broken={phase['broken']}" in text
    )
    checks["phase_convention_values"] = int(phase["intact"]) == 0 and int(phase["broken"]) == 1

    # Outputs
    checks["has_U"] = bool(re.search(r"\bU\b", text))
    checks["has_RF"] = bool(re.search(r"\bRF\b", text))
    checks["has_SDV"] = sci["has_sdv"]
    if require_miseseri:
        for token in ("MISESERI", "MISESAVG", "S", "EVOL"):
            checks[f"has_{token}"] = bool(re.search(rf"\b{token}\b", text, re.I))
        checks["has_All_elem"] = bool(re.search(r"elset=All_elem", text, re.I))
    else:
        checks["no_silent_miseseri_outputs"] = not sci["has_miseseri"]

    # h / lc from generation manifest if present
    manifest_path = deck_path.parent / "generation_manifest.json"
    if manifest_path.exists():
        man = json.loads(manifest_path.read_text(encoding="utf-8"))
        hmed = man.get("corridor_stats", {}).get("corridor_h_median")
        h_over = man.get("corridor_h_over_lc_median")
        target = man.get("local_target_h_mm")
        checks["manifest_has_corridor_h"] = hmed is not None
        checks["manifest_h_over_lc"] = h_over is not None
        if role == "H0_refined":
            # Offline MISESERI-refined layered deck: author H0 h targets do not apply.
            expected_h = float(
                config.get("remeshing", {}).get("target_local_final_h_mm", 0.0025)
            )
            checks["target_h_matches_role"] = (
                abs(float(target) - expected_h) < 1e-12 if target is not None else False
            )
            if hmed is not None:
                # Median corridor size should be near minElementSize after refinement.
                tol = max(0.001, 0.5 * expected_h)
                checks["corridor_h_near_refined_target"] = abs(float(hmed) - expected_h) <= tol
            checks["physical_count_refined_gt_h0"] = physical > 3930
        elif role and role in config["mesh"]["roles"]:
            expected_h = float(config["mesh"]["roles"][role]["local_target_h_mm"])
            checks["target_h_matches_role"] = abs(float(target) - expected_h) < 1e-12 if target is not None else False
            if hmed is not None and role == "H1":
                checks["corridor_h_near_target"] = abs(float(hmed) - expected_h) <= 0.25 * expected_h
            if hmed is not None and role == "H0":
                checks["corridor_h_near_author"] = abs(float(hmed) - 0.00494) <= 0.002
        details["corridor_h_median"] = hmed
        details["h_over_lc_median"] = h_over
        # Remeshing params must not be silently baked into fracture deck generation
        checks["no_errorTarget_in_deck"] = "errorTarget" not in text
        checks["no_remesh_rule_in_deck"] = "refinementFactor" not in text
        checks["manifest_not_hpc_authorized"] = man.get("hpc_submission_authorized") is False
    else:
        checks["manifest_present"] = False

    failed = [k for k, v in checks.items() if not v]
    return {
        "deck": str(deck_path.as_posix()),
        "fortran": str(fortran_path.as_posix()) if fortran_path else None,
        "role": role,
        "physical_elements": physical,
        "layered_elements": physical * 3,
        "status": "pass" if not failed else "fail",
        "failed_checks": failed,
        "checks": checks,
        "details": details,
        "scientific": sci,
        "deck_sha256": sha256_file(deck_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/preprocessing/molnar_h0_h1_unified.yaml")
    parser.add_argument("--deck", type=Path, required=True)
    parser.add_argument("--fortran", type=Path, default=None)
    parser.add_argument("--role", choices=["H0", "H1", "H2-PUB", "H0_refined"], default=None)
    parser.add_argument("--require-miseseri", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    fortran = args.fortran
    if fortran is None:
        # conventional sibling
        cand = args.deck.with_suffix(".for")
        if cand.exists():
            fortran = cand
    report = validate_deck(
        args.deck,
        fortran,
        config,
        require_miseseri=args.require_miseseri,
        role=args.role,
    )
    out_dir = args.out_dir or (ROOT / "results/validation/unified_preprocessing" / (args.role or "deck"))
    write_json(out_dir / "STATIC_VALIDATION.json", report)
    lines = [
        f"# Static validation — {args.role or args.deck.name}",
        "",
        f"Status: `{report['status']}`",
        f"Physical elements: {report['physical_elements']}",
        f"Layered elements: {report['layered_elements']}",
        "",
        "## Failed checks",
        "",
    ]
    if report["failed_checks"]:
        lines.extend(f"- `{c}`" for c in report["failed_checks"])
    else:
        lines.append("- none")
    lines.extend(["", "## All checks", ""])
    for k, v in sorted(report["checks"].items()):
        lines.append(f"- `{'PASS' if v else 'FAIL'}` {k}")
    write_md(out_dir / "STATIC_VALIDATION.md", lines)
    print(json.dumps({"status": report["status"], "failed": report["failed_checks"]}, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
