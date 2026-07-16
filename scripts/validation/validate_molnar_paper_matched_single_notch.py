#!/usr/bin/env python3
"""Static checks for Molnar paper-matched single-notch candidates."""

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


TOL = 1.0e-9


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv_dict(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def parse_deck(deck_text: str) -> dict:
    nodes: dict[int, tuple[float, float]] = {}
    elements: dict[int, dict] = {}
    nsets: dict[str, list[int]] = defaultdict(list)
    elsets: dict[str, list[int]] = defaultdict(list)
    current = None
    current_name = None
    current_etype = None
    generate = False
    for raw in deck_text.splitlines():
        line = raw.strip()
        lower = line.lower()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            current = None
            current_name = None
            current_etype = None
            generate = "generate" in lower
            if lower.startswith("*node"):
                current = "node"
            elif lower.startswith("*element"):
                current = "element"
                match = re.search(r"type=([^,\s]+)", line, re.I)
                current_etype = match.group(1).upper() if match else ""
                match = re.search(r"elset=([^,\s]+)", line, re.I)
                current_name = match.group(1) if match else ""
            elif lower.startswith("*nset"):
                current = "nset"
                match = re.search(r"nset=([^,\s]+)", line, re.I)
                current_name = match.group(1) if match else ""
            elif lower.startswith("*elset"):
                current = "elset"
                match = re.search(r"elset=([^,\s]+)", line, re.I)
                current_name = match.group(1) if match else ""
            continue
        parts = [part.strip() for part in line.split(",") if part.strip()]
        if current == "node" and len(parts) >= 3:
            nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
        elif current == "element" and len(parts) >= 5:
            eid = int(parts[0])
            elements[eid] = {"type": current_etype, "elset": current_name, "connectivity": [int(part) for part in parts[1:5]]}
        elif current == "nset" and current_name:
            nsets[current_name].extend(int(part) for part in parts)
        elif current == "elset" and current_name:
            values = [int(part) for part in parts]
            if generate and len(values) >= 3:
                elsets[current_name].extend(range(values[0], values[1] + 1, values[2]))
            else:
                elsets[current_name].extend(values)
    return {"nodes": nodes, "elements": elements, "nsets": dict(nsets), "elsets": dict(elsets)}


def signed_area(coords: list[tuple[float, float]]) -> float:
    area = 0.0
    for (x0, y0), (x1, y1) in zip(coords, coords[1:] + coords[:1]):
        area += x0 * y1 - x1 * y0
    return 0.5 * area


def aspect_ratio(coords: list[tuple[float, float]]) -> float:
    lengths = []
    for (x0, y0), (x1, y1) in zip(coords, coords[1:] + coords[:1]):
        lengths.append(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5)
    return max(lengths) / min(lengths)


def amplitude_values(text: str, name: str) -> tuple[float, float] | None:
    match = re.search(rf"\*Amplitude, name={re.escape(name)}\s*\n([^*\n]+)", text, re.I)
    if not match:
        return None
    values = [float(part.strip()) for part in match.group(1).split(",") if part.strip()]
    return (values[1], values[3]) if len(values) >= 4 else None


def step_inc(text: str, name: str) -> int | None:
    match = re.search(rf"\*Step, name={re.escape(name)},[^\n]*inc=(\d+)", text, re.I)
    return int(match.group(1)) if match else None


def check_determinism(config_path: Path, version: str, expected_hash: str) -> bool:
    script = Path("scripts/model_generation/build_molnar_paper_matched_single_notch.py")
    with tempfile.TemporaryDirectory(prefix="molnar_v2_det_") as d1, tempfile.TemporaryDirectory(prefix="molnar_v2_det_") as d2:
        for out_dir in [d1, d2]:
            result = subprocess.run(
                ["python", str(script), "--config", str(config_path), "--version", version, "--out-dir", out_dir],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if result.returncode != 0:
                return False
        h1 = sha256(Path(d1) / f"paper_matched_single_notch_{version}.inp")
        h2 = sha256(Path(d2) / f"paper_matched_single_notch_{version}.inp")
        return h1 == h2 == expected_hash


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/molnar_paper_matched_single_notch.yaml")
    parser.add_argument("--version", default="v2")
    parser.add_argument("--deck", default=None)
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()
    config_path = Path(args.config)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    generated_dir = Path("models/generated/molnar_gravouil_2017") / f"paper_matched_single_notch_{args.version}"
    deck_path = Path(args.deck) if args.deck else generated_dir / f"paper_matched_single_notch_{args.version}.inp"
    out_dir = Path(args.out_dir) if args.out_dir else Path("results/validation") / f"molnar_paper_matched_single_notch_{args.version}"
    manifest_path = generated_dir / "generation_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    user_subroutine_path = Path(manifest.get("user_subroutine", ""))
    text = deck_path.read_text(encoding="utf-8")
    user_subroutine_text = user_subroutine_path.read_text(encoding="utf-8") if user_subroutine_path.exists() else ""
    parsed = parse_deck(text)
    nodes = parsed["nodes"]
    elements = parsed["elements"]
    ids = list(elements)
    referenced_nodes = {node for element in elements.values() for node in element["connectivity"]}
    physical = int(config["mesh"]["estimated_physical_element_count"])
    u1_ids = sorted(eid for eid, e in elements.items() if e["type"] == "U1")
    u2_ids = sorted(eid for eid, e in elements.items() if e["type"] == "U2")
    cps4_ids = sorted(eid for eid, e in elements.items() if e["type"] == "CPS4")
    coords = list(nodes.values())
    xs = [x for x, _ in coords]
    ys = [y for _, y in coords]
    physical_coords = [[nodes[n] for n in elements[eid]["connectivity"]] for eid in u1_ids]
    areas = [signed_area(c) for c in physical_coords]
    aspects = [aspect_ratio(c) for c in physical_coords]
    lower = set(parsed["nsets"].get("notch_lower_face", []))
    upper = set(parsed["nsets"].get("notch_upper_face", []))
    open_notch_shared = bool(lower & upper)
    bridges = 0
    for eid in u1_ids:
        elem_nodes = set(elements[eid]["connectivity"])
        if elem_nodes & lower and elem_nodes & upper:
            bridges += 1
    amp1 = amplitude_values(text, "Amp-1")
    amp2 = amplitude_values(text, "Amp-2")
    inc1 = step_inc(text, "Step-1")
    inc2 = step_inc(text, "Step-2")
    loading = config["loading"]
    spacing_x = read_csv_dict(generated_dir / "mesh_spacing_x.csv")
    spacing_y = read_csv_dict(generated_dir / "mesh_spacing_y.csv")
    mesh_stats = {row["quantity"]: row["value"] for row in read_csv_dict(generated_dir / "mesh_statistics.csv")}
    source_hashes = (generated_dir / "source_hashes.txt").read_text(encoding="utf-8")
    required_hash_paths = [
        "models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.inp",
        "models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.for",
    ]
    checks = {
        "deck_exists": deck_path.exists(),
        "deck_hash_matches_manifest": sha256(deck_path) == manifest["deck_sha256"],
        "user_subroutine_exists": user_subroutine_path.exists(),
        "user_subroutine_hash_matches_manifest": user_subroutine_path.exists() and sha256(user_subroutine_path) == manifest.get("user_subroutine_sha256"),
        "user_subroutine_n_elem_matches_physical": user_subroutine_text.count(f"N_ELEM={physical}") == 2,
        "preserved_source_not_modified_in_place": "N_ELEM=3930" in Path("models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.for").read_text(encoding="utf-8"),
        "generator_determinism_pass": check_determinism(config_path, args.version, manifest["deck_sha256"]),
        "domain_is_1mm_by_1mm": abs(min(xs) + 0.5) < TOL and abs(max(xs) - 0.5) < TOL and abs(min(ys) + 0.5) < TOL and abs(max(ys) - 0.5) < TOL,
        "notch_length_is_0p5mm": len(lower) == len(upper) and min(nodes[n][0] for n in lower) == -0.5 and max(nodes[n][0] for n in lower) < 0.0 and 0.0 in xs,
        "notch_tip_coordinates_represented": any(abs(x) < TOL and abs(y) < TOL for x, y in coords),
        "opposing_notch_faces_not_tied": not open_notch_shared,
        "no_physical_elements_bridge_notch_faces": bridges == 0,
        "visualization_layer_count_matches_physical": len(cps4_ids) == len(u1_ids),
        "no_duplicate_element_ids": len(ids) == len(set(ids)),
        "node_ids_unique": len(nodes) == len(set(nodes)),
        "connectivity_references_valid_nodes": referenced_nodes.issubset(nodes),
        "positive_physical_element_area": min(areas) > 0.0,
        "acceptable_aspect_ratio": max(aspects) <= float(config["mesh"]["recipe"]["element_aspect_ratio_limit"]) + TOL,
        "actual_local_h_near_target": abs(float(mesh_stats["minimum_edge_size_mm"]) - float(config["mesh"]["local_element_size"])) < TOL,
        "actual_global_h_near_target": abs(float(mesh_stats["maximum_edge_size_mm"]) - float(config["mesh"]["recipe"]["global_element_size"])) < TOL,
        "actual_graded_transition_present": len(set(row["dx_mm"] for row in spacing_x)) > 3 and len(set(row["dy_mm"] for row in spacing_y)) > 3,
        "neighboring_size_ratio_within_limit": max(float(mesh_stats["max_neighbor_size_ratio_x"]), float(mesh_stats["max_neighbor_size_ratio_y"])) <= float(config["mesh"]["recipe"]["maximum_neighbouring_size_ratio"]) + TOL,
        "refined_region_physically_present": int(mesh_stats["refined_region_physical_elements"]) > 0,
        "u1_declaration_complete": re.search(r"\*User Element, nodes=4, type=U1, properties=3, coordinates=2, VARIABLES=8", text, re.I) is not None,
        "u2_declaration_complete": re.search(r"\*User Element, nodes=4, type=U2, properties=4, coordinates=2, VARIABLES=56", text, re.I) is not None,
        "uel_property_blocks_complete": "*Uel property, elset=PLATE" in text and "*Uel property, elset=PLATE_SS" in text,
        "property_ordering_matches_source": "PROPS(U1): lc, Gc, thickness" in text and "PROPS(U2): E, nu, thickness, residual stiffness k" in text,
        "non_overlapping_element_offsets": u1_ids == list(range(1, physical + 1)) and u2_ids == list(range(physical + 1, 2 * physical + 1)) and cps4_ids == list(range(2 * physical + 1, 3 * physical + 1)),
        "expected_layer_counts": len(u1_ids) == len(u2_ids) == len(cps4_ids) == physical,
        "top_and_bottom_sets_exist": bool(parsed["nsets"].get("top")) and bool(parsed["nsets"].get("bottom")),
        "rigid_body_motion_removed": "bottoml, 1, 1" in text and "topl, 1, 1" in text,
        "horizontal_overconstraint_absent": "bottom, 1, 1" not in text and "top, 1, 1" not in text,
        "vertical_loading_consistent": "*Equation" in text and "top, 2, 1." in text and "RP, 2, -1." in text and "bottom, 2, 2" in text,
        "rf_extraction_set_valid": "*Nset, nset=RP" in text and "*Node Output, nset=RP" in text,
        "loading_step1_arithmetic": inc1 is not None and amp1 is not None and abs((amp1[1] - amp1[0]) - inc1 * float(loading["step1_displacement_increment"])) < TOL,
        "loading_step2_arithmetic": inc2 is not None and amp2 is not None and abs((amp2[1] - amp2[0]) - inc2 * float(loading["step2_displacement_increment"])) < TOL,
        "loading_final_sum": abs(float(loading["step1_displacement_change"]) + float(loading["step2_displacement_change"]) - float(loading["final_displacement"])) < TOL,
        "deck_final_displacement_matches_config": amp2 is not None and abs(amp2[1] - float(loading["final_displacement"])) < TOL,
        "required_outputs_exist": "*Node Output, nset=RP" in text and "RF, U" in text and "SDV" in text,
        "contour_state_plan_exists": bool(config.get("contour_comparison_states")),
        "source_hashes_recorded": all(path in source_hashes for path in required_hash_paths),
        "no_windows_paths": re.search(r"[A-Za-z]:\\\\", text) is None,
        "no_hpc_paths": "/scratch/" not in text and "/home/" not in text,
        "candidate_v1_preserved": Path("models/generated/molnar_gravouil_2017/paper_matched_single_notch_v1/paper_matched_single_notch_v1.inp").exists()
        and Path("results/validation/molnar_paper_matched_single_notch_v1/STATIC_VALIDATION.md").exists(),
    }
    classification = "static_validation_pass" if all(checks.values()) else "static_validation_fail"
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "candidate": f"paper_matched_candidate_{args.version}",
        "classification": classification,
        "runnable_recommendation": classification == "static_validation_pass",
        "checks": checks,
        "metrics": {
            "physical_elements": physical,
            "layered_elements": len(ids),
            "node_count": len(nodes),
            "min_area": min(areas),
            "max_aspect_ratio": max(aspects),
            "h_over_l": float(config["mesh"]["h_over_l"]),
            "notch_face_nodes_per_side": len(lower),
            "max_neighbor_size_ratio_x": float(mesh_stats["max_neighbor_size_ratio_x"]),
            "max_neighbor_size_ratio_y": float(mesh_stats["max_neighbor_size_ratio_y"]),
        },
    }
    (out_dir / "VALIDATION_RESULTS.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        f"# Static Validation - Molnar Paper-Matched Single-Notch {args.version}",
        "",
        f"Classification: `{classification}`",
        "",
        "| Check | Result |",
        "|---|---|",
    ]
    for key, ok in checks.items():
        lines.append(f"| `{key}` | `{'pass' if ok else 'fail'}` |")
    lines.extend(
        [
            "",
            "## Metrics",
            "",
            f"- Physical elements: `{physical}`",
            f"- Layered elements: `{len(ids)}`",
            f"- h/l: `{float(config['mesh']['h_over_l'])}`",
            f"- Maximum aspect ratio: `{max(aspects):.6g}`",
            f"- Notch face nodes per side: `{len(lower)}`",
            "",
            "Static validation does not include Abaqus execution or PBS submission.",
            "",
        ]
    )
    (out_dir / "STATIC_VALIDATION.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"classification={classification}")
    return 0 if classification == "static_validation_pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
