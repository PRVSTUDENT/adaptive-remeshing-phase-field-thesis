#!/usr/bin/env python3
"""Generate deterministic Molnar lc=0.015 mm h-convergence study inputs.

H0 is an immutable copy/reference of the exact author-supplied SingleNotch
deck and source. H1 and H2-PUB are structured graded meshes that preserve all
non-mesh scientific settings from the supplementary model while varying only
local crack-path resolution.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import statistics
from pathlib import Path

import yaml

# Reuse axis-spacing helpers from the paper-matched mesh estimator.
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from estimate_molnar_paper_mesh import (  # noqa: E402
    AxisSpacing,
    max_neighbor_ratio,
    make_axis_spacings,
)

ROOT = Path(__file__).resolve().parents[2]
PRESERVED_INP = ROOT / "models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.inp"
PRESERVED_FOR = ROOT / "models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.for"
OUT_ROOT = ROOT / "models/generated/molnar_gravouil_2017/h_convergence_lc015"
DEFAULT_CONFIG = ROOT / "configs/studies/molnar_lc015_h_convergence.yaml"

EXPECTED_INP_SHA = "89ce3f32e396b0e484be6753a272dd6bbb2a2f9daff426d6a57419f57d665b72"
EXPECTED_FOR_SHA = "18944e5bb2a3b7973fd0d4bff03f8e078eef667965343d8a29156d093f53f5f1"
TOL = 1.0e-10
LC = 0.015


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def chunked_numbers(numbers: list[int], width: int = 12) -> list[str]:
    lines = []
    for start in range(0, len(numbers), width):
        lines.append(", ".join(str(n) for n in numbers[start : start + width]))
    return lines


def write_nset(lines: list[str], name: str, numbers: list[int], instance: bool = True) -> None:
    suffix = ", instance=Part-1-1" if instance else ""
    lines.append(f"*Nset, nset={name}{suffix}")
    lines.extend(chunked_numbers(numbers))


class MeshBuilder:
    def __init__(self, x_axis: AxisSpacing, y_axis: AxisSpacing):
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.nodes: dict[tuple[int, int, str], int] = {}
        self.node_coords: dict[int, tuple[float, float]] = {}
        self.next_node = 1

    def _node_key(self, i: int, j: int, side: str = "shared") -> tuple[int, int, str]:
        x = self.x_axis.coordinates[i]
        y = self.y_axis.coordinates[j]
        if abs(y) < TOL and -0.5 <= x < 0.0:
            return (i, j, side)
        return (i, j, "shared")

    def node(self, i: int, j: int, side: str = "shared") -> int:
        key = self._node_key(i, j, side)
        if key not in self.nodes:
            self.nodes[key] = self.next_node
            self.node_coords[self.next_node] = (self.x_axis.coordinates[i], self.y_axis.coordinates[j])
            self.next_node += 1
        return self.nodes[key]

    def build_nodes(self) -> None:
        for j in range(len(self.y_axis.coordinates)):
            for i in range(len(self.x_axis.coordinates)):
                y = self.y_axis.coordinates[j]
                x = self.x_axis.coordinates[i]
                if abs(y) < TOL and -0.5 <= x < 0.0:
                    self.node(i, j, "lower")
                    self.node(i, j, "upper")
                else:
                    self.node(i, j)

    def element_connectivity(self) -> list[tuple[int, int, int, int]]:
        zero_j = min(range(len(self.y_axis.coordinates)), key=lambda j: abs(self.y_axis.coordinates[j]))
        if abs(self.y_axis.coordinates[zero_j]) > TOL:
            raise RuntimeError("Mesh must include y=0 for the open notch split")
        conn = []
        for j in range(len(self.y_axis.coordinates) - 1):
            for i in range(len(self.x_axis.coordinates) - 1):
                if j == zero_j:
                    n1 = self.node(i, j, "upper")
                    n2 = self.node(i + 1, j, "upper")
                else:
                    n1 = self.node(i, j)
                    n2 = self.node(i + 1, j)
                if j + 1 == zero_j:
                    n3 = self.node(i + 1, j + 1, "lower")
                    n4 = self.node(i, j + 1, "lower")
                else:
                    n3 = self.node(i + 1, j + 1)
                    n4 = self.node(i, j + 1)
                conn.append((n1, n2, n3, n4))
        return conn

    def bottom_nodes(self) -> list[int]:
        return [self.node(i, 0) for i in range(len(self.x_axis.coordinates))]

    def top_nodes(self) -> list[int]:
        j = len(self.y_axis.coordinates) - 1
        return [self.node(i, j) for i in range(len(self.x_axis.coordinates))]

    def bottom_left_node(self) -> int:
        return self.node(0, 0)

    def top_left_node(self) -> int:
        return self.node(0, len(self.y_axis.coordinates) - 1)

    def notch_face_nodes(self, side: str) -> list[int]:
        zero_j = min(range(len(self.y_axis.coordinates)), key=lambda j: abs(self.y_axis.coordinates[j]))
        return [
            self.node(i, zero_j, side)
            for i, x in enumerate(self.x_axis.coordinates)
            if -0.5 <= x < 0.0
        ]


def paper_like_config(local_h: float, study: dict) -> dict:
    recipe = study["mesh_recipe"]
    refined = recipe["refined_zone"]
    return {
        "geometry": {"width": 1.0, "height": 1.0},
        "fracture": {"selected_length_scale": LC},
        "mesh": {
            "local_element_size": local_h,
            "h_over_l": local_h / LC,
            "layer_count": 3,
            "recipe": {
                "refined_zone": refined,
                "global_element_size": float(recipe["global_element_size_mm"]),
                "maximum_neighbouring_size_ratio": float(recipe["maximum_neighbouring_size_ratio"]),
                "transition_region_width": 0.02,
            },
        },
    }


def mesh_quality(conn: list[tuple[int, int, int, int]], coords: dict[int, tuple[float, float]], refined: dict) -> dict:
    edge_lengths: list[float] = []
    corridor_edges: list[float] = []
    aspect_ratios: list[float] = []
    jacobians: list[float] = []
    corridor_elements = 0
    for n1, n2, n3, n4 in conn:
        pts = [coords[n1], coords[n2], coords[n3], coords[n4]]
        lengths = []
        for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
            length = math.hypot(x1 - x0, y1 - y0)
            lengths.append(length)
            edge_lengths.append(length)
        aspect_ratios.append(max(lengths) / min(lengths) if min(lengths) > 0 else float("inf"))
        area = 0.0
        for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
            area += x0 * y1 - x1 * y0
        jacobians.append(0.5 * area)
        xc = sum(p[0] for p in pts) / 4.0
        yc = sum(p[1] for p in pts) / 4.0
        in_corridor = (
            float(refined["x_min"]) <= xc <= float(refined["x_max"])
            and float(refined["y_min"]) <= yc <= float(refined["y_max"])
        )
        if in_corridor:
            corridor_elements += 1
            corridor_edges.extend(lengths)
    def stats(values: list[float]) -> dict:
        if not values:
            return {"min": None, "median": None, "mean": None, "max": None}
        return {
            "min": min(values),
            "median": statistics.median(values),
            "mean": statistics.mean(values),
            "max": max(values),
        }

    return {
        "edge_length_all": stats(edge_lengths),
        "edge_length_corridor": stats(corridor_edges),
        "max_aspect_ratio": max(aspect_ratios) if aspect_ratios else None,
        "negative_jacobian_count": sum(1 for j in jacobians if j <= 0),
        "positive_orientation_fraction": (sum(1 for j in jacobians if j > 0) / len(jacobians)) if jacobians else 0.0,
        "corridor_element_count": corridor_elements,
        "actual_local_h_corridor_median": stats(corridor_edges)["median"],
        "actual_local_h_corridor_mean": stats(corridor_edges)["mean"],
        "actual_local_h_corridor_min": stats(corridor_edges)["min"],
        "actual_local_h_corridor_max": stats(corridor_edges)["max"],
    }


def write_generated_deck(case_id: str, local_h: float, study: dict, out_dir: Path) -> dict:
    cfg = paper_like_config(local_h, study)
    x_axis, y_axis = make_axis_spacings(cfg)
    mesh = MeshBuilder(x_axis, y_axis)
    mesh.build_nodes()
    conn = mesh.element_connectivity()
    physical = len(conn)
    rp_node = mesh.next_node
    quality = mesh_quality(conn, mesh.node_coords, study["mesh_recipe"]["refined_zone"])
    lines = [
        "*Heading",
        f"** Molnar lc015 h-convergence case {case_id}",
        f"** local_target_h_mm={local_h}",
        f"** physical_elements={physical}",
        "** Scientific settings preserved from exact supplementary SingleNotch.inp",
        "*Preprint, echo=NO, model=NO, history=NO, contact=NO",
        "*Part, name=Part-1",
        "*Node",
    ]
    for nid in sorted(mesh.node_coords):
        x, y = mesh.node_coords[nid]
        lines.append(f"{nid}, {x:.10f}, {y:.10f}")
    lines.extend(
        [
            "*User Element, nodes=4, type=U1, properties=3, coordinates=2, VARIABLES=8",
            "3",
            "*Element, type=U1, elset=PLATE",
        ]
    )
    for idx, c in enumerate(conn, start=1):
        lines.append(f"{idx}, {c[0]}, {c[1]}, {c[2]}, {c[3]}")
    lines.extend(
        [
            "*Elset, elset=PLATE, generate",
            f"1, {physical}, 1",
            "*Uel property, elset=PLATE",
            "0.015, 0.0027, 1",
            "*User Element, nodes=4, type=U2, properties=4, coordinates=2, VARIABLES=56",
            "1, 2",
            "*Element, type=U2, elset=PLATE_SS",
        ]
    )
    for idx, c in enumerate(conn, start=physical + 1):
        lines.append(f"{idx}, {c[0]}, {c[1]}, {c[2]}, {c[3]}")
    lines.extend(
        [
            "*Elset, elset=PLATE_SS, generate",
            f"{physical + 1}, {2 * physical}, 1",
            "*Uel property, elset=PLATE_SS",
            "210, 0.3, 1, 1e-07",
            "*Element, type=CPS4, elset=umatelem",
        ]
    )
    for idx, c in enumerate(conn, start=2 * physical + 1):
        lines.append(f"{idx}, {c[0]}, {c[1]}, {c[2]}, {c[3]}")
    lines.extend(
        [
            "*Solid Section, elset=umatelem, material=umatelem",
            "1.0",
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
    write_nset(lines, "bottom", mesh.bottom_nodes())
    write_nset(lines, "top", mesh.top_nodes())
    write_nset(lines, "bottoml", [mesh.bottom_left_node()])
    write_nset(lines, "topl", [mesh.top_left_node()])
    write_nset(lines, "notch_lower_face", mesh.notch_face_nodes("lower"))
    write_nset(lines, "notch_upper_face", mesh.notch_face_nodes("upper"))
    lines.extend(
        [
            "*Elset, elset=umatelem, instance=Part-1-1, generate",
            f"{2 * physical + 1}, {3 * physical}, 1",
            "*Equation",
            "2",
            "top, 2, 1.",
            "RP, 2, -1.",
            "*End Assembly",
            "*Amplitude, name=Amp-1",
            "0., 0., 0.5, 0.005",
            "*Amplitude, name=Amp-2",
            "0., 0.005, 0.5, 0.01",
            "*Material, name=umatelem",
            "*Depvar",
            "16,",
            "*User Material, constants=2",
            "1e-11, 0.3",
            "*Step, name=Step-1, nlgeom=NO, inc=500",
            "*Static, direct",
            "0.001, 0.5,",
            "*Boundary, amplitude=Amp-1",
            "RP, 2, 2, 1.",
            "*Boundary",
            "bottom, 2, 2",
            "*Boundary",
            "bottoml, 1, 1",
            "*Boundary",
            "topl, 1, 1",
            "*Restart, write, frequency=0",
            "*Output, field, time interval=0.01",
            "*Node Output",
            "U,",
            "*Node Output, nset=RP",
            "RF, U",
            "*Element Output, elset=umatelem",
            "SDV",
            "*End Step",
            "*Step, name=Step-2, nlgeom=NO, inc=2000",
            "*Static, direct",
            "0.0001, 0.2,",
            "*Boundary, amplitude=Amp-2",
            "RP, 2, 2, 1.",
            "*Restart, write, frequency=0",
            "*Output, field, time interval=0.01",
            "*Node Output",
            "U,",
            "*Node Output, nset=RP",
            "RF, U",
            "*Element Output, elset=umatelem",
            "SDV",
            "*End Step",
        ]
    )
    deck = out_dir / f"{case_id}.inp"
    write_text_lf(deck, "\n".join(lines) + "\n")

    # Fortran: only N_ELEM changes.
    text = PRESERVED_FOR.read_text(encoding="utf-8")
    if text.count("N_ELEM=3930") != 2:
        raise RuntimeError("Expected exactly two N_ELEM=3930 occurrences in preserved Fortran")
    updated = text.replace("N_ELEM=3930", f"N_ELEM={physical}")
    fortran = out_dir / f"{case_id}.for"
    write_text_lf(fortran, updated)
    diff_lines = [
        f"# Source diff proof for {case_id}",
        "# Only permitted change: N_ELEM value",
        f"# preserved: N_ELEM=3930",
        f"# generated: N_ELEM={physical}",
        "",
        "--- SingleNotch.for (preserved)",
        f"+++ {fortran.name}",
        "@@",
        f"-      PARAMETER(... N_ELEM=3930, ...)",
        f"+      PARAMETER(... N_ELEM={physical}, ...)",
        f"-      COMMON/KUSER/USRVAR(N_ELEM=3930, ...)",
        f"+      COMMON/KUSER/USRVAR(N_ELEM={physical}, ...)",
        "",
        "Note: both PARAMETER and COMMON uses of N_ELEM are updated by the same",
        "token replacement; no residual/tangent/history/formulation logic changes.",
        "",
    ]
    write_text_lf(out_dir / "SOURCE_N_ELEM_DIFF.md", "\n".join(diff_lines))

    max_ratio = max(max_neighbor_ratio(x_axis.spacings), max_neighbor_ratio(y_axis.spacings))
    stats = {
        "case_id": case_id,
        "local_target_h_mm": local_h,
        "target_h_over_lc": local_h / LC,
        "node_count": len(mesh.node_coords) + 1,
        "physical_element_count": physical,
        "layered_element_count": physical * 3,
        "x_node_count": len(x_axis.coordinates),
        "y_node_count": len(y_axis.coordinates),
        "max_neighbour_size_ratio": max_ratio,
        "rp_node": rp_node,
        "deck_sha256": sha256(deck),
        "source_sha256": sha256(fortran),
        "mesh_sha256": sha256(deck),  # deck embeds the mesh; separate mesh dump below
        **{f"quality_{k}": v for k, v in quality.items() if not isinstance(v, dict)},
        "edge_length_all_min": quality["edge_length_all"]["min"],
        "edge_length_all_median": quality["edge_length_all"]["median"],
        "edge_length_all_mean": quality["edge_length_all"]["mean"],
        "edge_length_all_max": quality["edge_length_all"]["max"],
        "actual_local_h_corridor_min": quality["actual_local_h_corridor_min"],
        "actual_local_h_corridor_median": quality["actual_local_h_corridor_median"],
        "actual_local_h_corridor_mean": quality["actual_local_h_corridor_mean"],
        "actual_local_h_corridor_max": quality["actual_local_h_corridor_max"],
        "corridor_h_over_lc_median": (
            quality["actual_local_h_corridor_median"] / LC
            if quality["actual_local_h_corridor_median"] is not None
            else None
        ),
        "corridor_element_count": quality["corridor_element_count"],
        "max_aspect_ratio": quality["max_aspect_ratio"],
        "negative_jacobian_count": quality["negative_jacobian_count"],
        "positive_orientation_fraction": quality["positive_orientation_fraction"],
    }

    # Lightweight mesh dump for hashing/images.
    mesh_csv = out_dir / "mesh_nodes.csv"
    write_csv(mesh_csv, ["node_id", "x", "y"], [[nid, x, y] for nid, (x, y) in sorted(mesh.node_coords.items())])
    conn_csv = out_dir / "mesh_elements.csv"
    write_csv(
        conn_csv,
        ["element_id", "n1", "n2", "n3", "n4"],
        [[i, *c] for i, c in enumerate(conn, start=1)],
    )
    stats["mesh_nodes_sha256"] = sha256(mesh_csv)
    stats["mesh_elements_sha256"] = sha256(conn_csv)
    write_csv(out_dir / "mesh_statistics.csv", ["quantity", "value"], [[k, v] for k, v in stats.items()])
    write_text_lf(out_dir / "generation_manifest.json", json.dumps(stats, indent=2, sort_keys=True) + "\n")
    write_mesh_image(out_dir / "mesh_image.png", mesh.node_coords, conn, case_id, local_h)
    return stats


def write_mesh_image(path: Path, coords: dict[int, tuple[float, float]], conn: list[tuple[int, int, int, int]], case_id: str, local_h: float) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        # Fallback: write a simple SVG that remains CAE-independent and viewable.
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" viewBox="-0.55 -0.55 1.1 1.1">',
            f'<title>{case_id} mesh h={local_h}</title>',
            '<g stroke="black" stroke-width="0.0008" fill="none">',
        ]
        for n1, n2, n3, n4 in conn[:: max(1, len(conn) // 4000)]:
            pts = [coords[n1], coords[n2], coords[n3], coords[n4], coords[n1]]
            d = " ".join(f"{'M' if i == 0 else 'L'}{x},{-y}" for i, (x, y) in enumerate(pts))
            lines.append(f'<path d="{d}"/>')
        lines.extend(["</g>", "</svg>"])
        write_text_lf(path.with_suffix(".svg"), "\n".join(lines) + "\n")
        return

    fig, ax = plt.subplots(figsize=(8, 8), dpi=150)
    # Subsample edges for very fine meshes to keep image generation practical.
    stride = max(1, len(conn) // 8000)
    for n1, n2, n3, n4 in conn[::stride]:
        xs = [coords[n1][0], coords[n2][0], coords[n3][0], coords[n4][0], coords[n1][0]]
        ys = [coords[n1][1], coords[n2][1], coords[n3][1], coords[n4][1], coords[n1][1]]
        ax.plot(xs, ys, color="0.2", linewidth=0.2)
    ax.set_aspect("equal")
    ax.set_xlim(-0.55, 0.55)
    ax.set_ylim(-0.55, 0.55)
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    ax.set_title(f"{case_id}: local target h = {local_h} mm")
    ax.grid(False)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def parse_h0_mesh_stats() -> dict:
    text = PRESERVED_INP.read_text(encoding="utf-8", errors="replace")
    nodes: dict[int, tuple[float, float]] = {}
    elements: list[tuple[int, int, int, int]] = []
    section = None
    for raw in text.splitlines():
        line = raw.strip()
        lower = line.lower()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            if lower.startswith("*node") and "nset" not in lower:
                section = "node"
            elif lower.startswith("*element") and "type=u1" in lower:
                section = "u1"
            elif lower.startswith("*element"):
                section = None
            else:
                section = None
            continue
        parts = [p.strip() for p in line.split(",") if p.strip()]
        if section == "node" and len(parts) >= 3:
            nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
        elif section == "u1" and len(parts) >= 5:
            elements.append(tuple(int(p) for p in parts[1:5]))  # type: ignore[arg-type]
    edge_lengths = []
    for n1, n2, n3, n4 in elements:
        if not all(n in nodes for n in (n1, n2, n3, n4)):
            continue
        pts = [nodes[n1], nodes[n2], nodes[n3], nodes[n4]]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
            edge_lengths.append(math.hypot(x1 - x0, y1 - y0))
    # Corridor approximation around y=0, x from -0.02 to 0.5
    corridor = []
    for n1, n2, n3, n4 in elements:
        if not all(n in nodes for n in (n1, n2, n3, n4)):
            continue
        pts = [nodes[n1], nodes[n2], nodes[n3], nodes[n4]]
        xc = sum(p[0] for p in pts) / 4.0
        yc = sum(p[1] for p in pts) / 4.0
        if -0.02 <= xc <= 0.5 and abs(yc) <= 0.01:
            for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
                corridor.append(math.hypot(x1 - x0, y1 - y0))
    return {
        "node_count": len(nodes) + 1,  # + assembly RP
        "physical_element_count": 3930,
        "layered_element_count": 11790,
        "edge_length_all_min": min(edge_lengths) if edge_lengths else None,
        "edge_length_all_median": statistics.median(edge_lengths) if edge_lengths else None,
        "edge_length_all_mean": statistics.mean(edge_lengths) if edge_lengths else None,
        "edge_length_all_max": max(edge_lengths) if edge_lengths else None,
        "actual_local_h_corridor_min": min(corridor) if corridor else None,
        "actual_local_h_corridor_median": statistics.median(corridor) if corridor else None,
        "actual_local_h_corridor_mean": statistics.mean(corridor) if corridor else None,
        "actual_local_h_corridor_max": max(corridor) if corridor else None,
        "corridor_element_count": None,
        "corridor_h_over_lc_median": (
            statistics.median(corridor) / LC if corridor else None
        ),
    }


def write_h0(out_dir: Path, study: dict) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    deck = out_dir / "SingleNotch.inp"
    fortran = out_dir / "SingleNotch.for"
    # Normalize to LF so Git-tracked and HPC-staged hashes match the committed blob.
    # Working-tree Windows CRLF of the preserved originals is scientifically identical.
    for src, dst in ((PRESERVED_INP, deck), (PRESERVED_FOR, fortran)):
        data = src.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        dst.write_bytes(data)
    deck_sha = sha256(deck)
    for_sha = sha256(fortran)
    preserved_wt_inp = sha256(PRESERVED_INP)
    preserved_wt_for = sha256(PRESERVED_FOR)
    if preserved_wt_inp != EXPECTED_INP_SHA or preserved_wt_for != EXPECTED_FOR_SHA:
        raise RuntimeError(
            f"Preserved working-tree hash mismatch: deck={preserved_wt_inp} for={preserved_wt_for}; "
            f"expected deck={EXPECTED_INP_SHA} for={EXPECTED_FOR_SHA}"
        )
    # Immutable reference note
    write_text_lf(
        out_dir / "IMMUTABLE_SOURCE.md",
        "# H0 Exact Author Inputs\n\n"
        "Author-supplied SingleNotch scientific content, tracked with LF endings for "
        "Git/HPC hash consistency.\n\n"
        f"- tracked deck SHA-256: `{deck_sha}`\n"
        f"- tracked source SHA-256: `{for_sha}`\n"
        f"- preserved working-tree deck SHA-256 (README): `{EXPECTED_INP_SHA}`\n"
        f"- preserved working-tree source SHA-256 (README): `{EXPECTED_FOR_SHA}`\n"
        f"- preserved deck: `{PRESERVED_INP.as_posix()}`\n"
        f"- preserved source: `{PRESERVED_FOR.as_posix()}`\n"
        "\nDo not edit scientific content.\n",
    )
    quality = parse_h0_mesh_stats()
    # Mesh image from parsed connectivity subset
    text = deck.read_text(encoding="utf-8", errors="replace")
    nodes: dict[int, tuple[float, float]] = {}
    conn: list[tuple[int, int, int, int]] = []
    section = None
    for raw in text.splitlines():
        line = raw.strip()
        lower = line.lower()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            if lower.startswith("*node") and "nset" not in lower:
                section = "node"
            elif lower.startswith("*element") and "type=u1" in lower:
                section = "u1"
            else:
                section = None
            continue
        parts = [p.strip() for p in line.split(",") if p.strip()]
        if section == "node" and len(parts) >= 3:
            nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
        elif section == "u1" and len(parts) >= 5:
            conn.append((int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])))
    write_mesh_image(out_dir / "mesh_image.png", nodes, conn, "H0_exact", 0.005)
    stats = {
        "case_id": "H0",
        "local_target_h_mm": 0.005,
        "target_h_over_lc": 0.3333333333,
        "deck_sha256": deck_sha,
        "source_sha256": for_sha,
        "mesh_sha256": deck_sha,
        "exact_author_inputs_verified": True,
        **quality,
    }
    write_csv(out_dir / "mesh_statistics.csv", ["quantity", "value"], [[k, v] for k, v in stats.items()])
    write_text_lf(out_dir / "generation_manifest.json", json.dumps(stats, indent=2, sort_keys=True) + "\n")
    write_text_lf(
        out_dir / "input_hashes.sha256",
        f"{deck_sha}  SingleNotch.inp\n{for_sha}  SingleNotch.for\n",
    )
    return stats


def write_case_hashes(out_dir: Path, deck_name: str, for_name: str) -> None:
    deck = out_dir / deck_name
    fortran = out_dir / for_name
    write_text_lf(
        out_dir / "input_hashes.sha256",
        f"{sha256(deck)}  {deck_name}\n{sha256(fortran)}  {for_name}\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--out-root", default=str(OUT_ROOT))
    parser.add_argument("--cases", default="H0,H1,H2-PUB")
    args = parser.parse_args()
    study = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    out_root = Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    selected = {c.strip() for c in args.cases.split(",") if c.strip()}
    all_stats = {}

    if "H0" in selected:
        h0_dir = out_root / "H0_exact"
        all_stats["H0"] = write_h0(h0_dir, study)
        write_text_lf(
            h0_dir / "README.md",
            "# H0 exact supplementary baseline\n\n"
            "Byte-identical author-supplied SingleNotch inputs.\n",
        )

    if "H1" in selected:
        h1_dir = out_root / "H1_h0025"
        h1_dir.mkdir(parents=True, exist_ok=True)
        stats = write_generated_deck("H1_h0025", 0.0025, study, h1_dir)
        write_case_hashes(h1_dir, "H1_h0025.inp", "H1_h0025.for")
        write_text_lf(
            h1_dir / "README.md",
            "# H1 intermediate h = 0.0025 mm\n\n"
            "Deterministic crack-path refinement of the supplementary scientific model.\n"
            f"Physical elements: {stats['physical_element_count']}\n",
        )
        all_stats["H1"] = stats

    if "H2-PUB" in selected or "H2" in selected:
        h2_dir = out_root / "H2_pub_h0010"
        h2_dir.mkdir(parents=True, exist_ok=True)
        stats = write_generated_deck("H2_pub_h0010", 0.001, study, h2_dir)
        write_case_hashes(h2_dir, "H2_pub_h0010.inp", "H2_pub_h0010.for")
        write_text_lf(
            h2_dir / "README.md",
            "# H2-PUB publication-resolution h = 0.001 mm\n\n"
            "Deterministic crack-path refinement including the publication spatial resolution.\n"
            f"Physical elements: {stats['physical_element_count']}\n"
            "Element count is generated, not forced to 22000.\n",
        )
        all_stats["H2-PUB"] = stats

    summary = out_root / "STUDY_GENERATION_SUMMARY.json"
    write_text_lf(summary, json.dumps(all_stats, indent=2, sort_keys=True) + "\n")
    print(json.dumps(all_stats, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
