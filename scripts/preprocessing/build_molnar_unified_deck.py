#!/usr/bin/env python3
"""Full config-driven Molnar H0/H1 layered-deck generator.

Pipeline:
  configuration
    -> geometry / physical mesh
    -> phase-field UEL layer (U1)
    -> displacement UEL layer (U2)
    -> UMAT/facsimile visualization layer (CPS4)
    -> element-label mappings
    -> sets, sections, loads, BCs
    -> output requests
    -> complete Abaqus input deck + Fortran N_ELEM source

H0 physical mesh is parsed from the preserved author supplementary deck so the
generated layered model remains scientifically equivalent to frozen H0.
H1/H2 physical meshes use the graded MeshBuilder (same family as h-convergence).

Does not submit PBS/Abaqus jobs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required: pip install pyyaml") from exc

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
MODEL_GEN = ROOT / "scripts/model_generation"
if str(MODEL_GEN) not in sys.path:
    sys.path.insert(0, str(MODEL_GEN))

from build_molnar_lc015_h_convergence import (  # noqa: E402
    MeshBuilder,
    make_axis_spacings,
    max_neighbor_ratio,
    mesh_quality,
    paper_like_config,
)
from estimate_molnar_paper_mesh import AxisSpacing  # noqa: E402

DEFAULT_CONFIG = ROOT / "configs/preprocessing/molnar_h0_h1_unified.yaml"
DEFAULT_OUT = ROOT / "models/generated/molnar_gravouil_2017/unified_preprocessing"
LC_DEFAULT = 0.015
TOL = 1.0e-10

ROLE_FOLDERS = {
    "H0": "H0_fullgen",
    "H1": "H1_fullgen",
    "H2-PUB": "H2_PUB_fullgen",
}


def role_folder(role: str, output_profile: str) -> str:
    base = ROLE_FOLDERS[role]
    if output_profile and output_profile != "fracture_baseline":
        return f"{base}_{output_profile}"
    return base


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, payload: Any) -> None:
    write_text_lf(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def chunked_numbers(numbers: list[int], width: int = 16) -> list[str]:
    lines = []
    for start in range(0, len(numbers), width):
        chunk = numbers[start : start + width]
        lines.append(", ".join(f"{n:6d}" for n in chunk))
    return lines


def load_config(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return data


def lf_normalize(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")


# ---------------------------------------------------------------------------
# Physical mesh sources
# ---------------------------------------------------------------------------


def parse_author_physical_mesh(inp_path: Path) -> dict[str, Any]:
    """Parse part nodes, U1 connectivity, and assembly BC nsets from author deck."""
    text = inp_path.read_text(encoding="utf-8", errors="replace")
    nodes: dict[int, tuple[float, float]] = {}
    conn: list[tuple[int, int, int, int]] = []
    nsets: dict[str, list[int]] = defaultdict(list)
    section: str | None = None
    current_nset: str | None = None
    in_part_nodes = False
    in_assembly = False
    saw_first_user_element = False

    for raw in text.splitlines():
        line = raw.strip()
        lower = line.lower()
        if not line:
            continue
        if line.startswith("**"):
            continue
        if line.startswith("*"):
            if lower.startswith("*assembly"):
                in_assembly = True
                in_part_nodes = False
                section = None
                current_nset = None
            elif lower.startswith("*end assembly"):
                in_assembly = False
                section = None
                current_nset = None
            elif lower.startswith("*user element") or lower.startswith("*user element"):
                saw_first_user_element = True
                in_part_nodes = False
                section = None
                current_nset = None
            elif lower.startswith("*node") and "nset" not in lower:
                if not in_assembly and not saw_first_user_element:
                    in_part_nodes = True
                    section = "part_node"
                elif in_assembly:
                    section = "assembly_node"
                    in_part_nodes = False
                else:
                    section = None
                current_nset = None
            elif lower.startswith("*element") and "type=u1" in lower:
                section = "u1"
                current_nset = None
            elif lower.startswith("*nset"):
                m = re.search(r"nset=([^,\s]+)", line, re.I)
                current_nset = m.group(1) if m else None
                section = "nset"
            elif lower.startswith("*"):
                if not (section == "nset" and current_nset):
                    section = None
                    current_nset = None
                if lower.startswith("*elset") or lower.startswith("*equation") or lower.startswith("*end"):
                    section = None
                    current_nset = None
            continue

        parts = [p.strip() for p in line.split(",") if p.strip() != ""]
        if not parts:
            continue
        if section == "part_node" and len(parts) >= 3:
            nodes[int(float(parts[0]))] = (float(parts[1]), float(parts[2]))
        elif section == "u1" and len(parts) >= 5:
            conn.append(
                (
                    int(float(parts[1])),
                    int(float(parts[2])),
                    int(float(parts[3])),
                    int(float(parts[4])),
                )
            )
        elif section == "nset" and current_nset and current_nset.lower() != "rp":
            for p in parts:
                try:
                    nsets[current_nset].append(int(float(p)))
                except ValueError:
                    continue

    if not nodes or not conn:
        raise RuntimeError(f"Failed to parse author physical mesh from {inp_path}")
    required = ["bottom", "top", "bottoml", "topl"]
    missing = [s for s in required if s not in nsets or not nsets[s]]
    if missing:
        raise RuntimeError(f"Author deck missing nsets: {missing}")
    return {
        "nodes": nodes,
        "connectivity": conn,
        "nsets": {k: sorted(set(v)) for k, v in nsets.items()},
        "source": "author_supplementary_parsed",
        "source_path": str(inp_path.as_posix()),
    }


def build_graded_physical_mesh(local_h: float, study: dict) -> dict[str, Any]:
    cfg = paper_like_config(local_h, study)
    x_axis, y_axis = make_axis_spacings(cfg)
    mesh = MeshBuilder(x_axis, y_axis)
    mesh.build_nodes()
    conn = mesh.element_connectivity()
    nsets = {
        "bottom": mesh.bottom_nodes(),
        "top": mesh.top_nodes(),
        "bottoml": [mesh.bottom_left_node()],
        "topl": [mesh.top_left_node()],
        "notch_lower_face": mesh.notch_face_nodes("lower"),
        "notch_upper_face": mesh.notch_face_nodes("upper"),
    }
    return {
        "nodes": mesh.node_coords,
        "connectivity": conn,
        "nsets": nsets,
        "source": "graded_mesh_builder",
        "x_node_count": len(x_axis.coordinates),
        "y_node_count": len(y_axis.coordinates),
        "max_neighbour_size_ratio": max(
            max_neighbor_ratio(x_axis.spacings), max_neighbor_ratio(y_axis.spacings)
        ),
        "x_axis": x_axis,
        "y_axis": y_axis,
    }


# ---------------------------------------------------------------------------
# Deck assembly
# ---------------------------------------------------------------------------


def format_float(value: float) -> str:
    # Stable, Abaqus-friendly formatting.
    if abs(value) >= 1.0e-3 or value == 0.0:
        text = f"{value:.10g}"
    else:
        text = f"{value:.10e}"
    return text


def resolve_loading_plan(config: dict[str, Any], output_profile: str) -> dict[str, Any]:
    """Return loading plan for fracture baseline or elastic pre-analysis profiles."""
    loading = config["benchmark"]["loading"]
    if output_profile in ("elastic_preanalysis", "miseseri_preanalysis"):
        # Authorized engineering choice: U_pre = 0.8 * U_peak_H1 = 0.8 * 0.0058 = 0.00464 mm
        u_pre = float(
            config.get("remeshing", {})
            .get("preanalysis", {})
            .get("u_pre_mm", 0.00464)
        )
        return {
            "mode": "elastic_precrack_single_step",
            "u_pre_mm": u_pre,
            "amp_pre": [0.0, 0.0, 1.0, u_pre],
            "step_name": "Step-pre",
            "step_inc": int(config.get("remeshing", {}).get("preanalysis", {}).get("step_inc", 200)),
            "static_direct": list(
                config.get("remeshing", {}).get("preanalysis", {}).get("static_direct", [0.005, 1.0])
            ),
            "dt_out": float(
                config.get("remeshing", {}).get("preanalysis", {}).get("field_output_time_interval", 0.05)
            ),
            "notes": "elastic pre-crack loading; initial engineering choice Upre=0.8*Upeak_H1",
        }
    if output_profile == "elastic_preanalysis_smoke":
        u_smoke = float(
            config.get("remeshing", {})
            .get("preanalysis", {})
            .get("u_smoke_mm", 0.001)
        )
        return {
            "mode": "elastic_precrack_smoke",
            "u_pre_mm": u_smoke,
            "amp_pre": [0.0, 0.0, 1.0, u_smoke],
            "step_name": "Step-smoke",
            "step_inc": 50,
            "static_direct": [0.02, 1.0],
            "dt_out": 0.1,
            "notes": "short smoke load for MISESERI output availability only",
        }
    return {
        "mode": "fracture_two_step",
        "amp1": list(loading["amplitude_1"]),
        "amp2": list(loading["amplitude_2"]),
        "step1_inc": int(loading["step1_inc"]),
        "step2_inc": int(loading["step2_inc"]),
        "s1": list(loading["step1_static_direct"]),
        "s2": list(loading["step2_static_direct"]),
        "dt_out": float(loading.get("field_output_time_interval", 0.01)),
    }


def build_layered_deck_text(
    *,
    case_id: str,
    physical_nodes: dict[int, tuple[float, float]],
    connectivity: list[tuple[int, int, int, int]],
    nsets: dict[str, list[int]],
    config: dict[str, Any],
    local_target_h: float,
    output_profile: str,
) -> str:
    material = config["benchmark"]["material"]
    phase_conv = config["benchmark"]["phase_field_convention"]
    profiles = config.get("outputs", {}).get("profiles", {})
    # MISESERI field requests for any pre-analysis profile
    if output_profile in ("elastic_preanalysis", "elastic_preanalysis_smoke", "miseseri_preanalysis"):
        profile = profiles.get(
            "miseseri_preanalysis",
            {
                "node": ["U"],
                "rp": ["RF", "U"],
                "element_umatelem": ["SDV", "S", "EVOL", "MISESERI", "MISESAVG"],
                "create_all_elem_set": True,
            },
        )
    else:
        profile = profiles.get(output_profile, profiles.get("fracture_baseline", {}))
    load_plan = resolve_loading_plan(config, output_profile)

    physical = len(connectivity)
    max_part_node = max(physical_nodes)
    rp_node = max_part_node + 1
    lc = float(material["length_scale_mm"])
    gc = float(material["critical_energy_release_rate_kN_per_mm"])
    thickness = float(material["thickness_mm"])
    E = float(material["youngs_modulus_kN_per_mm2"])
    nu = float(material["poissons_ratio"])
    k_u2 = float(material["residual_stiffness_u2"])
    k_umat = float(material["residual_stiffness_umat"])

    lines: list[str] = [
        "*Heading",
        f"** Unified full generation: {case_id}",
        f"** mesh_role={case_id}",
        f"** local_target_h_mm={local_target_h}",
        f"** physical_elements={physical}",
        f"** layered_elements={physical * 3}",
        f"** phase_field_convention intact={phase_conv['intact']} broken={phase_conv['broken']}",
        f"** output_profile={output_profile}",
        f"** loading_mode={load_plan.get('mode')}",
        f"** config_id={config.get('config_id', 'unknown')}",
        "** Pipeline: geometry/mesh -> U1 -> U2 -> CPS4 -> sets/BC -> outputs",
        "*Preprint, echo=NO, model=NO, history=NO, contact=NO",
        "*Part, name=Part-1",
        "*Node",
    ]
    for nid in sorted(physical_nodes):
        x, y = physical_nodes[nid]
        lines.append(f"{nid}, {format_float(x)}, {format_float(y)}")

    # U1 phase-field layer: labels 1..N
    lines.extend(
        [
            "*User Element, nodes=4, type=U1, properties=3, coordinates=2, VARIABLES=8",
            "3",
            "*Element, type=U1, elset=PLATE",
        ]
    )
    for idx, c in enumerate(connectivity, start=1):
        lines.append(f"{idx}, {c[0]}, {c[1]}, {c[2]}, {c[3]}")
    lines.extend(
        [
            "*Elset, elset=PLATE, generate",
            f"1, {physical}, 1",
            "*Uel property, elset=PLATE",
            f"{format_float(lc)}, {format_float(gc)}, {format_float(thickness)}",
        ]
    )

    # U2 displacement layer: labels N+1..2N
    lines.extend(
        [
            "*User Element, nodes=4, type=U2, properties=4, coordinates=2, VARIABLES=56",
            "1, 2",
            "*Element, type=U2, elset=PLATE_SS",
        ]
    )
    for idx, c in enumerate(connectivity, start=physical + 1):
        lines.append(f"{idx}, {c[0]}, {c[1]}, {c[2]}, {c[3]}")
    lines.extend(
        [
            "*Elset, elset=PLATE_SS, generate",
            f"{physical + 1}, {2 * physical}, 1",
            "*Uel property, elset=PLATE_SS",
            f"{format_float(E)}, {format_float(nu)}, {format_float(thickness)}, {format_float(k_u2)}",
        ]
    )

    # CPS4 visualization / UMAT facsimile: labels 2N+1..3N
    lines.append("*Element, type=CPS4, elset=umatelem")
    for idx, c in enumerate(connectivity, start=2 * physical + 1):
        lines.append(f"{idx}, {c[0]}, {c[1]}, {c[2]}, {c[3]}")
    lines.extend(
        [
            "*Solid Section, elset=umatelem, material=umatelem",
            f"{format_float(thickness)}",
            "*End Part",
            "*Assembly, name=Assembly",
            "*Instance, name=Part-1-1, part=Part-1",
            "*End Instance",
            "*Node",
            f"{rp_node}, 0.5, 0.5, 0.0",
            "*Nset, nset=RP",
            f"{rp_node},",
        ]
    )

    def write_nset(name: str, ids: list[int]) -> None:
        lines.append(f"*Nset, nset={name}, instance=Part-1-1")
        lines.extend(chunked_numbers(list(ids)))

    write_nset("bottom", nsets["bottom"])
    write_nset("top", nsets["top"])
    write_nset("bottoml", nsets["bottoml"])
    write_nset("topl", nsets["topl"])
    for optional in ("notch_lower_face", "notch_upper_face"):
        if optional in nsets and nsets[optional]:
            write_nset(optional, nsets[optional])

    lines.extend(
        [
            "*Elset, elset=umatelem, instance=Part-1-1, generate",
            f"{2 * physical + 1}, {3 * physical}, 1",
        ]
    )
    if profile.get("create_all_elem_set"):
        lines.extend(
            [
                "*Elset, elset=All_elem, instance=Part-1-1, generate",
                f"1, {3 * physical}, 1",
            ]
        )
    lines.extend(
        [
            "*Equation",
            "2",
            "top, 2, 1.",
            "RP, 2, -1.",
            "*End Assembly",
        ]
    )

    # Amplitudes
    if load_plan["mode"].startswith("elastic_precrack"):
        amp = load_plan["amp_pre"]
        lines.extend(
            [
                f"** loading_mode={load_plan['mode']}; Upre={load_plan['u_pre_mm']} mm",
                f"** {load_plan.get('notes', '')}",
                "*Amplitude, name=Amp-pre",
                f"{format_float(amp[0])}, {format_float(amp[1])}, {format_float(amp[2])}, {format_float(amp[3])}",
            ]
        )
    else:
        amp1 = load_plan["amp1"]
        amp2 = load_plan["amp2"]
        lines.extend(
            [
                "*Amplitude, name=Amp-1",
                f"{format_float(amp1[0])}, {format_float(amp1[1])}, {format_float(amp1[2])}, {format_float(amp1[3])}",
                "*Amplitude, name=Amp-2",
                f"{format_float(amp2[0])}, {format_float(amp2[1])}, {format_float(amp2[2])}, {format_float(amp2[3])}",
            ]
        )

    lines.extend(
        [
            "*Material, name=umatelem",
            "*Depvar",
            "16,",
            "*User Material, constants=2",
            f"{format_float(k_umat)}, {format_float(nu)}",
        ]
    )

    elem_tokens = profile.get("element_umatelem", ["SDV"])
    rp_tokens = profile.get("rp", ["RF", "U"])
    node_tokens = profile.get("node", ["U"])

    def step_block(name: str, inc: int, static_vals: list[float], amp: str, include_supports: bool, dt_out: float) -> None:
        lines.extend(
            [
                f"*Step, name={name}, nlgeom=NO, inc={inc}",
                "*Static, direct",
                f"{format_float(static_vals[0])}, {format_float(static_vals[1])},",
                f"*Boundary, amplitude={amp}",
                "RP, 2, 2, 1.",
            ]
        )
        if include_supports:
            lines.extend(
                [
                    "*Boundary",
                    "bottom, 2, 2",
                    "*Boundary",
                    "bottoml, 1, 1",
                    "*Boundary",
                    "topl, 1, 1",
                ]
            )
        lines.extend(
            [
                "*Restart, write, frequency=0",
                f"*Output, field, time interval={format_float(dt_out)}",
                "*Node Output",
                ", ".join(node_tokens) + ",",
                "*Node Output, nset=RP",
                ", ".join(rp_tokens),
                "*Element Output, elset=umatelem",
                ", ".join(elem_tokens),
                "*End Step",
            ]
        )

    if load_plan["mode"].startswith("elastic_precrack"):
        step_block(
            load_plan["step_name"],
            int(load_plan["step_inc"]),
            list(load_plan["static_direct"]),
            "Amp-pre",
            include_supports=True,
            dt_out=float(load_plan["dt_out"]),
        )
    else:
        step_block("Step-1", int(load_plan["step1_inc"]), list(load_plan["s1"]), "Amp-1", True, float(load_plan["dt_out"]))
        step_block("Step-2", int(load_plan["step2_inc"]), list(load_plan["s2"]), "Amp-2", False, float(load_plan["dt_out"]))
    return "\n".join(lines) + "\n"


def write_fortran_source(preserved_for: Path, physical: int, out_path: Path) -> dict[str, Any]:
    text = preserved_for.read_text(encoding="utf-8")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if text.count("N_ELEM=3930") != 2:
        raise RuntimeError("Expected exactly two N_ELEM=3930 occurrences in preserved Fortran")
    updated = text.replace("N_ELEM=3930", f"N_ELEM={physical}")
    write_text_lf(out_path, updated)
    return {
        "physical_elements": physical,
        "n_elem_occurrences": updated.count(f"N_ELEM={physical}"),
        "only_n_elem_changed": updated.replace(f"N_ELEM={physical}", "N_ELEM=3930") == text,
        "sha256": sha256_file(out_path),
    }


# ---------------------------------------------------------------------------
# Equivalence / validation helpers
# ---------------------------------------------------------------------------


def parse_layered_deck(text: str) -> dict[str, Any]:
    nodes: dict[int, tuple[float, float]] = {}
    elements: dict[int, dict[str, Any]] = {}
    nsets: dict[str, list[int]] = defaultdict(list)
    elsets: dict[str, list[int]] = defaultdict(list)
    section = None
    etype = None
    name = None
    generate = False
    in_assembly = False
    for raw in text.splitlines():
        line = raw.strip()
        lower = line.lower()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            generate = "generate" in lower
            section = None
            etype = None
            name = None
            if lower.startswith("*assembly"):
                in_assembly = True
            elif lower.startswith("*end assembly"):
                in_assembly = False
            elif lower.startswith("*node") and "nset" not in lower:
                section = "node"
            elif lower.startswith("*element") and "output" not in lower:
                # Exclude "*Element Output" requests.
                section = "element"
                m = re.search(r"type=([^,\s]+)", line, re.I)
                etype = m.group(1).upper() if m else ""
            elif lower.startswith("*nset"):
                section = "nset"
                m = re.search(r"nset=([^,\s]+)", line, re.I)
                name = m.group(1) if m else ""
            elif lower.startswith("*elset"):
                section = "elset"
                m = re.search(r"elset=([^,\s]+)", line, re.I)
                name = m.group(1) if m else ""
            continue
        parts = [p.strip() for p in line.split(",") if p.strip() != ""]
        if section == "node" and len(parts) >= 3 and not in_assembly:
            try:
                nodes[int(float(parts[0]))] = (float(parts[1]), float(parts[2]))
            except ValueError:
                continue
        elif section == "element" and len(parts) >= 5:
            try:
                eid = int(float(parts[0]))
                conn = tuple(int(float(p)) for p in parts[1:5])
            except ValueError:
                continue
            elements[eid] = {
                "type": etype,
                "connectivity": conn,
            }
        elif section == "nset" and name and name.lower() != "rp":
            for p in parts:
                try:
                    nsets[name].append(int(float(p)))
                except ValueError:
                    continue
        elif section == "elset" and name:
            try:
                vals = [int(float(p)) for p in parts]
            except ValueError:
                continue
            if generate and len(vals) >= 3:
                elsets[name].extend(range(vals[0], vals[1] + 1, vals[2]))
            else:
                elsets[name].extend(vals)
    u1 = {e: d for e, d in elements.items() if d["type"] == "U1"}
    u2 = {e: d for e, d in elements.items() if d["type"] == "U2"}
    cps4 = {e: d for e, d in elements.items() if d["type"] == "CPS4"}
    return {
        "nodes": nodes,
        "elements": elements,
        "u1": u1,
        "u2": u2,
        "cps4": cps4,
        "nsets": {k: sorted(set(v)) for k, v in nsets.items()},
        "elsets": {k: sorted(set(v)) for k, v in elsets.items()},
    }


def scientific_fields(text: str) -> dict[str, Any]:
    def amp(name: str):
        m = re.search(rf"\*Amplitude, name={re.escape(name)}\s*\n([^\n*]+)", text, re.I)
        if not m:
            return None
        return [float(x.strip()) for x in m.group(1).split(",") if x.strip()]

    def uel(elset: str):
        m = re.search(rf"\*Uel property, elset={re.escape(elset)}\s*\n([^\n*]+)", text, re.I)
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

    umat = re.search(r"\*User Material, constants=2\s*\n([^\n*]+)", text, re.I)
    return {
        "u1_props": uel("PLATE"),
        "u2_props": uel("PLATE_SS"),
        "umat_props": [float(x.strip()) for x in umat.group(1).split(",") if x.strip()] if umat else None,
        "amp1": amp("Amp-1"),
        "amp2": amp("Amp-2"),
        "step1_inc": step_inc("Step-1"),
        "step2_inc": step_inc("Step-2"),
        "step1_static": static_after("Step-1"),
        "step2_static": static_after("Step-2"),
        "has_equation": "*Equation" in text,
        "has_rp": bool(re.search(r"\*Nset, nset=RP", text, re.I)),
        "has_sdv": bool(re.search(r"\bSDV\b", text, re.I)),
        "has_miseseri": bool(re.search(r"MISESERI", text, re.I)),
    }


def almost_equal(a: Any, b: Any, tol: float = 1e-9) -> bool:
    if a is None or b is None:
        return a is b
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            return False
        return all(abs(float(x) - float(y)) <= tol for x, y in zip(a, b))
    return abs(float(a) - float(b)) <= tol


def compare_to_frozen_h0(generated_text: str, frozen_text: str) -> dict[str, Any]:
    g = parse_layered_deck(generated_text)
    f = parse_layered_deck(frozen_text)
    g_sci = scientific_fields(generated_text)
    f_sci = scientific_fields(frozen_text)

    # Node coordinate comparison (part nodes only).
    node_ok = True
    if set(g["nodes"]) != set(f["nodes"]):
        node_ok = False
    else:
        for nid, (x, y) in g["nodes"].items():
            fx, fy = f["nodes"][nid]
            if abs(x - fx) > 1e-8 or abs(y - fy) > 1e-8:
                node_ok = False
                break

    # Physical U1 connectivity equality by label.
    u1_ok = True
    if set(g["u1"]) != set(f["u1"]):
        u1_ok = False
    else:
        for eid in g["u1"]:
            if g["u1"][eid]["connectivity"] != f["u1"][eid]["connectivity"]:
                u1_ok = False
                break

    # Layered connectivity correspondence within generated deck.
    physical = len(g["u1"])
    layer_map_ok = True
    for i in range(1, physical + 1):
        c1 = g["u1"].get(i, {}).get("connectivity")
        c2 = g["u2"].get(i + physical, {}).get("connectivity")
        c3 = g["cps4"].get(i + 2 * physical, {}).get("connectivity")
        if not (c1 and c1 == c2 == c3):
            layer_map_ok = False
            break

    # Frozen layered connectivity correspondence for same physical map.
    frozen_layer_ok = True
    for i in range(1, len(f["u1"]) + 1):
        c1 = f["u1"].get(i, {}).get("connectivity")
        c2 = f["u2"].get(i + len(f["u1"]), {}).get("connectivity")
        c3 = f["cps4"].get(i + 2 * len(f["u1"]), {}).get("connectivity")
        if not (c1 and c1 == c2 == c3):
            frozen_layer_ok = False
            break

    set_checks = {}
    for sname in ("bottom", "top", "bottoml", "topl"):
        set_checks[sname] = sorted(g["nsets"].get(sname, [])) == sorted(f["nsets"].get(sname, []))

    checks = {
        "part_nodes_equal": node_ok,
        "physical_u1_connectivity_equal": u1_ok,
        "generated_layer_connectivity_equal": layer_map_ok,
        "frozen_layer_connectivity_equal": frozen_layer_ok,
        "physical_count_equal": len(g["u1"]) == len(f["u1"]) == 3930,
        "label_offsets_u1_1_to_n": set(g["u1"]) == set(range(1, physical + 1)),
        "label_offsets_u2_n_plus": set(g["u2"]) == set(range(physical + 1, 2 * physical + 1)),
        "label_offsets_cps4_2n_plus": set(g["cps4"]) == set(range(2 * physical + 1, 3 * physical + 1)),
        "nset_bottom": set_checks["bottom"],
        "nset_top": set_checks["top"],
        "nset_bottoml": set_checks["bottoml"],
        "nset_topl": set_checks["topl"],
        "u1_props": almost_equal(g_sci["u1_props"], f_sci["u1_props"]),
        "u2_props": almost_equal(g_sci["u2_props"], f_sci["u2_props"]),
        "umat_props": almost_equal(g_sci["umat_props"], f_sci["umat_props"]),
        "amp1": almost_equal(g_sci["amp1"], f_sci["amp1"]),
        "amp2": almost_equal(g_sci["amp2"], f_sci["amp2"]),
        "step1_inc": g_sci["step1_inc"] == f_sci["step1_inc"],
        "step2_inc": g_sci["step2_inc"] == f_sci["step2_inc"],
        "step1_static": almost_equal(g_sci["step1_static"], f_sci["step1_static"]),
        "step2_static": almost_equal(g_sci["step2_static"], f_sci["step2_static"]),
        "has_equation": g_sci["has_equation"] and f_sci["has_equation"],
        "has_rp": g_sci["has_rp"] and f_sci["has_rp"],
        "has_sdv": g_sci["has_sdv"] and f_sci["has_sdv"],
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "physical_elements_generated": physical,
        "physical_elements_frozen": len(f["u1"]),
    }


def corridor_h_stats(
    nodes: dict[int, tuple[float, float]],
    connectivity: list[tuple[int, int, int, int]],
    refined: dict[str, float],
) -> dict[str, Any]:
    corridor_edges: list[float] = []
    all_edges: list[float] = []
    for n1, n2, n3, n4 in connectivity:
        pts = [nodes[n1], nodes[n2], nodes[n3], nodes[n4]]
        lengths = [math.hypot(pts[i][0] - pts[(i + 1) % 4][0], pts[i][1] - pts[(i + 1) % 4][1]) for i in range(4)]
        all_edges.extend(lengths)
        xc = sum(p[0] for p in pts) / 4.0
        yc = sum(p[1] for p in pts) / 4.0
        if (
            float(refined["x_min"]) <= xc <= float(refined["x_max"])
            and float(refined["y_min"]) <= yc <= float(refined["y_max"])
        ):
            corridor_edges.extend(lengths)
    return {
        "corridor_edge_count": len(corridor_edges),
        "corridor_h_min": min(corridor_edges) if corridor_edges else None,
        "corridor_h_median": statistics.median(corridor_edges) if corridor_edges else None,
        "corridor_h_mean": statistics.mean(corridor_edges) if corridor_edges else None,
        "corridor_h_max": max(corridor_edges) if corridor_edges else None,
        "all_h_median": statistics.median(all_edges) if all_edges else None,
    }


# ---------------------------------------------------------------------------
# Generation orchestration
# ---------------------------------------------------------------------------


def load_physical_mesh_from_csv(nodes_csv: Path, elems_csv: Path) -> dict[str, Any]:
    nodes: dict[int, tuple[float, float]] = {}
    with nodes_csv.open(encoding="utf-8") as stream:
        header = stream.readline()
        for line in stream:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 3:
                nodes[int(float(parts[0]))] = (float(parts[1]), float(parts[2]))
    conn: list[tuple[int, int, int, int]] = []
    with elems_csv.open(encoding="utf-8") as stream:
        header = stream.readline()
        for line in stream:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 5:
                conn.append(
                    (
                        int(float(parts[1])),
                        int(float(parts[2])),
                        int(float(parts[3])),
                        int(float(parts[4])),
                    )
                )
    # Reconstruct BC nsets from coordinates (bottom/top edges)
    bottom = [nid for nid, (x, y) in nodes.items() if abs(y + 0.5) < 1e-8]
    top = [nid for nid, (x, y) in nodes.items() if abs(y - 0.5) < 1e-8]
    bottoml = [min(bottom, key=lambda n: nodes[n][0])] if bottom else []
    topl = [min(top, key=lambda n: nodes[n][0])] if top else []
    return {
        "nodes": nodes,
        "connectivity": conn,
        "nsets": {
            "bottom": sorted(bottom),
            "top": sorted(top),
            "bottoml": bottoml,
            "topl": topl,
        },
        "source": "external_csv_refined_physical",
        "source_nodes_csv": str(nodes_csv.as_posix()),
        "source_elems_csv": str(elems_csv.as_posix()),
    }


def generate_role(
    config: dict[str, Any],
    role: str,
    out_dir: Path,
    *,
    output_profile: str | None = None,
    dry_run: bool = False,
    physical_nodes_csv: Path | None = None,
    physical_elems_csv: Path | None = None,
) -> dict[str, Any]:
    if role not in ROLE_FOLDERS and role != "H0_refined":
        if role not in ("H0", "H1", "H2-PUB", "H0_refined"):
            raise ValueError(f"Unsupported role: {role}")
    role_key = "H0" if role in ("H0", "H0_refined") else role
    role_cfg = config["mesh"]["roles"][role_key]
    material = config["benchmark"]["material"]
    lc = float(material["length_scale_mm"])
    local_h = float(role_cfg["local_target_h_mm"])
    if role == "H0_refined":
        local_h = float(config.get("remeshing", {}).get("target_local_final_h_mm", 0.0025))
    profile = output_profile or config.get("outputs", {}).get("profile", "fracture_baseline")

    preserved_inp = ROOT / config["benchmark"]["preserved_inp"]
    preserved_for = ROOT / config["benchmark"]["preserved_for"]
    if sha256_file(preserved_inp) != config["benchmark"]["expected_preserved_inp_sha256"]:
        raise RuntimeError("Preserved SingleNotch.inp hash mismatch")
    if sha256_file(preserved_for) != config["benchmark"]["expected_preserved_for_sha256"]:
        raise RuntimeError("Preserved SingleNotch.for hash mismatch")

    study_path = ROOT / config.get("paths", {}).get("study_config", "configs/studies/molnar_lc015_h_convergence.yaml")
    study = yaml.safe_load(study_path.read_text(encoding="utf-8"))

    if physical_nodes_csv and physical_elems_csv:
        physical = load_physical_mesh_from_csv(physical_nodes_csv, physical_elems_csv)
    elif role_cfg["physical_mesh_source"] == "author_supplementary_parsed" and role != "H0_refined":
        physical = parse_author_physical_mesh(preserved_inp)
    else:
        physical = build_graded_physical_mesh(local_h, study)

    nodes = physical["nodes"]
    conn = physical["connectivity"]
    nsets = physical["nsets"]
    n_phys = len(conn)
    expected = role_cfg.get("physical_elements_expected")
    if (
        expected is not None
        and int(expected) != n_phys
        and physical.get("source") != "external_csv_refined_physical"
        and role not in ("H0_refined",)
    ):
        # H1/H2 expected counts are frozen study targets; fail hard if builder drifts.
        if role_key != "H0":
            raise RuntimeError(f"{role}: physical elements {n_phys} != expected {expected}")

    refined = config["mesh"]["refined_zone"]
    hstats = corridor_h_stats(nodes, conn, refined)
    deck_text = build_layered_deck_text(
        case_id=role,
        physical_nodes=nodes,
        connectivity=conn,
        nsets=nsets,
        config=config,
        local_target_h=local_h,
        output_profile=profile,
    )

    deck_name = f"{role.replace('-', '_')}_fullgen.inp"
    for_name = f"{role.replace('-', '_')}_fullgen.for"
    manifest: dict[str, Any] = {
        "case_id": role,
        "config_id": config.get("config_id"),
        "generation_mode": "full_layered_pipeline",
        "physical_mesh_source": physical["source"],
        "output_profile": profile,
        "local_target_h_mm": local_h,
        "length_scale_mm": lc,
        "target_h_over_lc": local_h / lc,
        "physical_elements": n_phys,
        "layered_elements": n_phys * 3,
        "node_count_part": len(nodes),
        "label_offsets": {
            "U1": f"1..{n_phys}",
            "U2": f"{n_phys + 1}..{2 * n_phys}",
            "CPS4": f"{2 * n_phys + 1}..{3 * n_phys}",
        },
        "phase_field_convention": config["benchmark"]["phase_field_convention"],
        "corridor_stats": hstats,
        "corridor_h_over_lc_median": (
            hstats["corridor_h_median"] / lc if hstats["corridor_h_median"] is not None else None
        ),
        "dry_run": dry_run,
        "hpc_submission_authorized": False,
    }

    if dry_run:
        manifest["deck_sha256_preview"] = sha256_bytes(deck_text.encode("utf-8"))
        return manifest

    out_dir.mkdir(parents=True, exist_ok=True)
    deck_path = out_dir / deck_name
    for_path = out_dir / for_name
    write_text_lf(deck_path, deck_text)
    for_info = write_fortran_source(preserved_for, n_phys, for_path)

    # Mesh dumps for hashing / Gate P1 semantic compare.
    node_lines = ["node_id,x,y"] + [f"{nid},{nodes[nid][0]},{nodes[nid][1]}" for nid in sorted(nodes)]
    write_text_lf(out_dir / "mesh_nodes.csv", "\n".join(node_lines) + "\n")
    elem_lines = ["element_id,n1,n2,n3,n4"] + [
        f"{i},{c[0]},{c[1]},{c[2]},{c[3]}" for i, c in enumerate(conn, start=1)
    ]
    write_text_lf(out_dir / "mesh_elements.csv", "\n".join(elem_lines) + "\n")
    mapping_lines = ["physical_id,u1_id,u2_id,cps4_id,n1,n2,n3,n4"]
    for i, c in enumerate(conn, start=1):
        mapping_lines.append(f"{i},{i},{i + n_phys},{i + 2 * n_phys},{c[0]},{c[1]},{c[2]},{c[3]}")
    write_text_lf(out_dir / "layer_mapping.csv", "\n".join(mapping_lines) + "\n")

    write_text_lf(
        out_dir / "input_hashes.sha256",
        f"{sha256_file(deck_path)}  {deck_name}\n{sha256_file(for_path)}  {for_name}\n",
    )
    write_text_lf(
        out_dir / "README.md",
        f"# {role} full generation\n\n"
        f"- Physical mesh source: `{physical['source']}`\n"
        f"- Physical elements: {n_phys}\n"
        f"- Layered elements: {n_phys * 3}\n"
        f"- Output profile: `{profile}`\n"
        f"- Local target h: {local_h} mm\n"
        f"- Corridor h median: {hstats['corridor_h_median']}\n"
        f"- h/lc median: {manifest['corridor_h_over_lc_median']}\n"
        "\nGenerated by `scripts/preprocessing/build_molnar_unified_deck.py`.\n"
        "No HPC submission is authorized by generation alone.\n",
    )

    equivalence = None
    # Full fracture-baseline H0 must match frozen scientific loading; elastic pre-analysis
    # intentionally changes amplitudes/steps and only requires mesh/layer equivalence.
    if role == "H0" and profile == "fracture_baseline":
        frozen_dir = ROOT / role_cfg["frozen_reference_dir"]
        frozen_inp = frozen_dir / "SingleNotch.inp"
        if frozen_inp.exists():
            equivalence = compare_to_frozen_h0(deck_text, frozen_inp.read_text(encoding="utf-8", errors="replace"))
            write_json(out_dir / "FROZEN_H0_EQUIVALENCE.json", equivalence)
    elif role == "H0" and profile != "fracture_baseline":
        frozen_dir = ROOT / role_cfg["frozen_reference_dir"]
        frozen_inp = frozen_dir / "SingleNotch.inp"
        if frozen_inp.exists():
            full = compare_to_frozen_h0(deck_text, frozen_inp.read_text(encoding="utf-8", errors="replace"))
            mesh_keys = [
                "part_nodes_equal",
                "physical_u1_connectivity_equal",
                "generated_layer_connectivity_equal",
                "physical_count_equal",
                "label_offsets_u1_1_to_n",
                "label_offsets_u2_n_plus",
                "label_offsets_cps4_2n_plus",
                "nset_bottom",
                "nset_top",
                "nset_bottoml",
                "nset_topl",
                "u1_props",
                "u2_props",
                "umat_props",
            ]
            mesh_checks = {k: full["checks"][k] for k in mesh_keys}
            equivalence = {
                "status": "pass" if all(mesh_checks.values()) else "fail",
                "scope": "mesh_layer_props_only_elastic_or_preanalysis_profile",
                "checks": mesh_checks,
                "loading_intentionally_different": True,
                "output_profile": profile,
            }
            write_json(out_dir / "FROZEN_H0_EQUIVALENCE.json", equivalence)

    manifest.update(
        {
            "deck_path": str(deck_path.relative_to(ROOT)).replace("\\", "/"),
            "fortran_path": str(for_path.relative_to(ROOT)).replace("\\", "/"),
            "deck_sha256": sha256_file(deck_path),
            "fortran_sha256": for_info["sha256"],
            "mesh_nodes_sha256": sha256_file(out_dir / "mesh_nodes.csv"),
            "mesh_elements_sha256": sha256_file(out_dir / "mesh_elements.csv"),
            "layer_mapping_sha256": sha256_file(out_dir / "layer_mapping.csv"),
            "fortran_n_elem": for_info,
            "frozen_h0_equivalence": equivalence,
        }
    )
    write_json(out_dir / "generation_manifest.json", manifest)
    return manifest


def gate_p1_full(config: dict[str, Any], out_root: Path, role: str = "H0") -> dict[str, Any]:
    a = out_root / "gate_p1_full" / f"{role}_a"
    b = out_root / "gate_p1_full" / f"{role}_b"
    if a.exists():
        shutil.rmtree(a)
    if b.exists():
        shutil.rmtree(b)
    ma = generate_role(config, role, a, dry_run=False)
    mb = generate_role(config, role, b, dry_run=False)
    same_deck = ma["deck_sha256"] == mb["deck_sha256"]
    same_for = ma["fortran_sha256"] == mb["fortran_sha256"]
    same_nodes = ma["mesh_nodes_sha256"] == mb["mesh_nodes_sha256"]
    same_elems = ma["mesh_elements_sha256"] == mb["mesh_elements_sha256"]
    same_map = ma["layer_mapping_sha256"] == mb["layer_mapping_sha256"]
    report = {
        "gate": "P1_full_generation",
        "mesh_role": role,
        "byte_identical_deck": same_deck,
        "byte_identical_fortran": same_for,
        "byte_identical_nodes_csv": same_nodes,
        "byte_identical_elements_csv": same_elems,
        "byte_identical_layer_mapping": same_map,
        "semantic_identity": same_deck and same_for and same_nodes and same_elems and same_map,
        "sha_a_deck": ma["deck_sha256"],
        "sha_b_deck": mb["deck_sha256"],
        "sha_a_for": ma["fortran_sha256"],
        "sha_b_for": mb["fortran_sha256"],
        "frozen_h0_equivalence_a": ma.get("frozen_h0_equivalence"),
        "status": "pass" if (same_deck and same_for and same_nodes and same_elems and same_map) else "fail",
    }
    if role == "H0" and ma.get("frozen_h0_equivalence"):
        report["frozen_equivalence_status"] = ma["frozen_h0_equivalence"]["status"]
        if ma["frozen_h0_equivalence"]["status"] != "pass":
            report["status"] = "fail"
            report["fail_reason"] = "frozen_h0_equivalence_failed"
    write_json(out_root / "gate_p1_full" / "GATE_P1_FULL_REPORT.json", report)
    return report


def compare_h0_h1_family(h0_manifest: dict, h1_manifest: dict) -> dict[str, Any]:
    """H1 may only differ from H0 by mesh size, counts, and graded topology dimensions."""
    shared_ok = {
        "same_lc": h0_manifest["length_scale_mm"] == h1_manifest["length_scale_mm"],
        "same_phase_convention": h0_manifest["phase_field_convention"] == h1_manifest["phase_field_convention"],
        "same_output_profile": h0_manifest["output_profile"] == h1_manifest["output_profile"],
        "same_generation_mode": h0_manifest["generation_mode"] == h1_manifest["generation_mode"],
        "h1_finer_target": h1_manifest["local_target_h_mm"] < h0_manifest["local_target_h_mm"],
        "h1_more_elements": h1_manifest["physical_elements"] > h0_manifest["physical_elements"],
    }
    return {
        "status": "pass" if all(shared_ok.values()) else "fail",
        "checks": shared_ok,
        "h0_physical": h0_manifest["physical_elements"],
        "h1_physical": h1_manifest["physical_elements"],
        "h0_h": h0_manifest["local_target_h_mm"],
        "h1_h": h1_manifest["local_target_h_mm"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--mesh-role", choices=sorted(ROLE_FOLDERS), help="Override mesh.mesh_role")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument(
        "--output-profile",
        choices=[
            "fracture_baseline",
            "miseseri_preanalysis",
            "elastic_preanalysis",
            "elastic_preanalysis_smoke",
        ],
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--gate-p1", action="store_true", help="Full-generation Gate P1 for selected role")
    parser.add_argument("--generate-h1", action="store_true", help="Also generate H1 and family compare")
    parser.add_argument("--all-default-roles", action="store_true", help="Generate H0 and H1")
    parser.add_argument("--from-nodes-csv", type=Path, help="External refined physical nodes CSV")
    parser.add_argument("--from-elems-csv", type=Path, help="External refined physical elements CSV")
    parser.add_argument(
        "--role-name",
        default=None,
        help="Override case/role name for external mesh rebuild (e.g. H0_refined)",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    out_root = args.out or ROOT / config.get("paths", {}).get("output_root", DEFAULT_OUT)
    if isinstance(out_root, str):
        out_root = ROOT / out_root if not Path(out_root).is_absolute() else Path(out_root)

    role = args.mesh_role or config.get("mesh", {}).get("mesh_role", "H0")
    if args.role_name:
        role = args.role_name

    if args.gate_p1:
        report = gate_p1_full(config, out_root, role=role if role in ROLE_FOLDERS else "H0")
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "pass" else 1

    roles = [role]
    if args.all_default_roles or args.generate_h1:
        roles = ["H0", "H1"]

    results = {}
    profile = args.output_profile or config.get("outputs", {}).get("profile", "fracture_baseline")
    for r in roles:
        if args.from_nodes_csv and args.from_elems_csv:
            dest = out_root if out_root.name.endswith("fullgen") or "refined" in out_root.name else out_root / "H0_refined_layered"
            if len(roles) > 1:
                dest = out_root / f"{r}_refined_layered"
            results[r] = generate_role(
                config,
                r if r in ("H0", "H1", "H2-PUB") else "H0_refined",
                dest,
                output_profile=args.output_profile or "fracture_baseline",
                dry_run=args.dry_run,
                physical_nodes_csv=args.from_nodes_csv,
                physical_elems_csv=args.from_elems_csv,
            )
        else:
            dest = out_root / role_folder(r if r in ROLE_FOLDERS else "H0", profile)
            results[r] = generate_role(
                config,
                r if r in ROLE_FOLDERS else "H0",
                dest,
                output_profile=args.output_profile,
                dry_run=args.dry_run,
            )
        print(json.dumps({r: results[r]}, indent=2, sort_keys=True))

    if "H0" in results and "H1" in results and not args.dry_run:
        family = compare_h0_h1_family(results["H0"], results["H1"])
        write_json(out_root / "H0_H1_FAMILY_COMPARE.json", family)
        print(json.dumps({"h0_h1_family_compare": family}, indent=2, sort_keys=True))
        if family["status"] != "pass":
            return 1
        if results["H0"].get("frozen_h0_equivalence", {}).get("status") == "fail":
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
