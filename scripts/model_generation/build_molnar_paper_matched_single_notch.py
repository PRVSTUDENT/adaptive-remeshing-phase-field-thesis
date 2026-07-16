#!/usr/bin/env python3
"""Generate deterministic Molnar paper-matched single-notch candidate decks."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import yaml

from estimate_molnar_paper_mesh import estimate, load_config, make_axis_spacings, max_neighbor_ratio


DEFAULT_VERSION = "v2"
OUT_ROOT = Path("models/generated/molnar_gravouil_2017")
SOURCE_FILES = [
    Path("Literature review/1-s2.0-S0168874X16304954-main.pdf"),
    Path("models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.inp"),
    Path("models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.for"),
]
PRESERVED_FORTRAN = Path("models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.for")
TOL = 1.0e-10


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_text_lf(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def rows_to_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


class MeshBuilder:
    def __init__(self, config: dict):
        self.config = config
        self.x_axis, self.y_axis = make_axis_spacings(config)
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
        for j, y in enumerate(self.y_axis.coordinates):
            for i, x in enumerate(self.x_axis.coordinates):
                if abs(y) < TOL and -0.5 <= x < 0.0:
                    self.node(i, j, "lower")
                    self.node(i, j, "upper")
                else:
                    self.node(i, j)

    def element_connectivity(self) -> list[tuple[int, int, int, int]]:
        zero_j = self.y_axis.coordinates.index(0.0)
        conn = []
        for j in range(len(self.y_axis.coordinates) - 1):
            for i in range(len(self.x_axis.coordinates) - 1):
                lower_side = "lower" if j + 1 == zero_j else "shared"
                upper_side = "upper" if j == zero_j else "shared"
                n1 = self.node(i, j, upper_side if j == zero_j else "shared")
                n2 = self.node(i + 1, j, upper_side if j == zero_j else "shared")
                n3 = self.node(i + 1, j + 1, lower_side if j + 1 == zero_j else "shared")
                n4 = self.node(i, j + 1, lower_side if j + 1 == zero_j else "shared")
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
        zero_j = self.y_axis.coordinates.index(0.0)
        return [
            self.node(i, zero_j, side)
            for i, x in enumerate(self.x_axis.coordinates)
            if -0.5 <= x < 0.0
        ]


def chunked_numbers(numbers: list[int], width: int = 12) -> list[str]:
    lines = []
    for start in range(0, len(numbers), width):
        lines.append(", ".join(str(n) for n in numbers[start : start + width]))
    return lines


def write_nset(lines: list[str], name: str, numbers: list[int], instance: bool = True) -> None:
    suffix = ", instance=Part-1-1" if instance else ""
    lines.append(f"*Nset, nset={name}{suffix}")
    lines.extend(chunked_numbers(numbers))


def write_deck(config: dict, version: str, path: Path) -> dict:
    mesh = MeshBuilder(config)
    mesh.build_nodes()
    conn = mesh.element_connectivity()
    physical = len(conn)
    mat = config["material"]
    frac = config["fracture"]
    thickness = float(config["model"]["thickness"])
    loading = config["loading"]
    rp_node = mesh.next_node
    lines = [
        "*Heading",
        "** Molnar paper-matched single-notch reconstruction candidate.",
        "** No Abaqus/PBS execution is authorized by this generated file.",
        f"** reconstruction_version: paper_matched_candidate_{version}",
        "** notch_implementation: split duplicated nodes on open left-edge crack segment x=-0.5..0, y=0",
        "*Preprint, echo=NO, model=NO, history=NO, contact=NO",
        "*Part, name=Part-1",
        "*Node",
    ]
    for nid in sorted(mesh.node_coords):
        x, y = mesh.node_coords[nid]
        lines.append(f"{nid}, {x:.10f}, {y:.10f}")
    lines.extend(
        [
            "** U1 phase-field layer mapped from preserved SingleNotch.inp/for",
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
            f"{float(frac['selected_length_scale']):.10g}, {float(frac['critical_energy_release_rate']):.10g}, {thickness:.10g}",
            "** PROPS(U1): lc, Gc, thickness",
            "** U2 displacement layer mapped from preserved SingleNotch.inp/for",
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
            f"{float(mat['youngs_modulus']):.10g}, {float(mat['poissons_ratio']):.10g}, {thickness:.10g}, {float(frac['residual_stiffness']['displacement_uel_k']):.10g}",
            "** PROPS(U2): E, nu, thickness, residual stiffness k",
            "*Element, type=CPS4, elset=umatelem",
        ]
    )
    for idx, c in enumerate(conn, start=2 * physical + 1):
        lines.append(f"{idx}, {c[0]}, {c[1]}, {c[2]}, {c[3]}")
    lines.extend(
        [
            "*Solid Section, elset=umatelem, material=umatelem",
            f"{thickness:.10g}",
            "*End Part",
            "*Assembly, name=Assembly",
            "*Instance, name=Part-1-1, part=Part-1",
            "*End Instance",
            "*Node",
            f"{rp_node}, 0.0, 0.5, 0.0",
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
            f"0., {float(loading['step1_initial_displacement']):.10g}, 1., {float(loading['step1_final_displacement']):.10g}",
            "*Amplitude, name=Amp-2",
            f"0., {float(loading['step2_initial_displacement']):.10g}, 1., {float(loading['step2_final_displacement']):.10g}",
            "*Material, name=umatelem",
            "*Depvar",
            "16,",
            "*User Material, constants=2",
            f"{float(frac['residual_stiffness']['umat_visualization_constant']):.10g}, {float(mat['poissons_ratio']):.10g}",
            f"*Step, name=Step-1, nlgeom=NO, inc={int(loading['step1_increment_count'])}",
            "*Static, direct",
            f"{1 / int(loading['step1_increment_count']):.15g}, 1.",
            "*Boundary, amplitude=Amp-1",
            "RP, 2, 2, 1.",
            "*Boundary",
            "bottom, 2, 2",
            "*Boundary",
            "bottoml, 1, 1",
            "*Boundary",
            "topl, 1, 1",
            "*Output, field, time interval=0.01",
            "*Node Output",
            "U,",
            "*Node Output, nset=RP",
            "RF, U",
            "*Element Output, elset=umatelem",
            "SDV",
            "*End Step",
            f"*Step, name=Step-2, nlgeom=NO, inc={int(loading['step2_increment_count'])}",
            "*Static, direct",
            f"{1 / int(loading['step2_increment_count']):.15g}, 1.",
            "*Boundary, amplitude=Amp-2",
            "RP, 2, 2, 1.",
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
    write_text_lf(path, "\n".join(lines) + "\n")
    return {
        "nodes": len(mesh.node_coords) + 1,
        "physical_elements": physical,
        "layered_elements": physical * 3,
        "rp_node": rp_node,
        "notch_lower_face_nodes": len(mesh.notch_face_nodes("lower")),
        "notch_upper_face_nodes": len(mesh.notch_face_nodes("upper")),
        "x_element_count": len(mesh.x_axis.coordinates) - 1,
        "y_element_count": len(mesh.y_axis.coordinates) - 1,
        "max_neighbor_size_ratio_x": max_neighbor_ratio(mesh.x_axis.spacings),
        "max_neighbor_size_ratio_y": max_neighbor_ratio(mesh.y_axis.spacings),
    }


def write_diagnostics(config: dict, version: str, out: Path, stats: dict) -> None:
    x_axis, y_axis = make_axis_spacings(config)
    estimate_stats = estimate(config)
    rows_to_csv(out / "mesh_spacing_x.csv", ["index", "x0_mm", "x1_mm", "dx_mm"], [[i + 1, x_axis.coordinates[i], x_axis.coordinates[i + 1], dx] for i, dx in enumerate(x_axis.spacings)])
    rows_to_csv(out / "mesh_spacing_y.csv", ["index", "y0_mm", "y1_mm", "dy_mm"], [[i + 1, y_axis.coordinates[i], y_axis.coordinates[i + 1], dy] for i, dy in enumerate(y_axis.spacings)])
    rows_to_csv(
        out / "layer_mapping.csv",
        ["layer", "role", "element_type", "id_start", "id_end", "properties", "state_variables", "output_role"],
        [
            ["U1", "phase_field", "U1", 1, stats["physical_elements"], "lc,Gc,thickness", 8, "phase/history UEL state"],
            ["U2", "displacement", "U2", stats["physical_elements"] + 1, 2 * stats["physical_elements"], "E,nu,thickness,k", 56, "mechanical UEL state"],
            ["CPS4", "visualization", "CPS4", 2 * stats["physical_elements"] + 1, 3 * stats["physical_elements"], "UMAT k,nu", 16, "ODB SDV visualization"],
        ],
    )
    loading = config["loading"]
    rows_to_csv(
        out / "loading_schedule.csv",
        ["step", "initial_displacement_mm", "final_displacement_mm", "displacement_change_mm", "nominal_increment_mm", "increment_count", "provenance_status"],
        [
            ["Step-1", loading["step1_initial_displacement"], loading["step1_final_displacement"], loading["step1_displacement_change"], loading["step1_displacement_increment"], loading["step1_increment_count"], loading["step1_provenance_status"]],
            ["Step-2", loading["step2_initial_displacement"], loading["step2_final_displacement"], loading["step2_displacement_change"], loading["step2_displacement_increment"], loading["step2_increment_count"], loading["step2_provenance_status"]],
        ],
    )
    rows_to_csv(
        out / "boundary_condition_summary.csv",
        ["set_or_command", "role", "constraint_or_output"],
        [
            ["bottom", "lower loaded-edge counterpart", "U2 fixed"],
            ["top", "loaded edge", "equation coupled to RP U2"],
            ["bottoml", "horizontal rigid-body removal", "U1 fixed"],
            ["topl", "source-faithful supplementary constraint", "U1 fixed"],
            ["RP", "reaction/displacement extraction", "RF,U output"],
            ["notch_lower_face/notch_upper_face", "open notch faces", "split nodes; no tie/equation"],
        ],
    )
    rows_to_csv(
        out / "mesh_statistics.csv",
        ["quantity", "value"],
        [[key, value] for key, value in {**estimate_stats, **stats}.items() if key != "checks"],
    )
    write_text_lf(
        out / "README.md",
        f"# Molnar Paper-Matched Single-Notch Candidate {version}\n\n"
        "Generated deterministic no-run reconstruction candidate. Static validation is required before any Abaqus/PBS execution.\n\n"
        f"Generated user subroutine: `SingleNotch_{version}.for`, copied from the preserved Molnar source with only `N_ELEM` updated to `{stats['physical_elements']}` for the candidate mesh.\n\n"
        "Candidate v1 remains preserved separately as failed static evidence.\n",
    )


def write_fortran_source(version: str, out: Path, physical_elements: int) -> Path:
    text = PRESERVED_FORTRAN.read_text(encoding="utf-8")
    original_count = text.count("N_ELEM=3930")
    if original_count != 2:
        raise RuntimeError(f"Expected exactly two N_ELEM=3930 constants in {PRESERVED_FORTRAN}, found {original_count}")
    updated = text.replace("N_ELEM=3930", f"N_ELEM={physical_elements}")
    lines = [line.rstrip() for line in updated.splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    updated = "\n".join(lines) + "\n"
    source = out / f"SingleNotch_{version}.for"
    write_text_lf(source, updated)
    return source


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/molnar_paper_matched_single_notch.yaml")
    parser.add_argument("--version", default=DEFAULT_VERSION, choices=["v1", "v2"])
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()
    config_path = Path(args.config)
    config = load_config(config_path)
    if args.version == "v2":
        config["reconstruction_version"] = "paper_matched_candidate_v2"
    out = Path(args.out_dir) if args.out_dir else OUT_ROOT / f"paper_matched_single_notch_{args.version}"
    out.mkdir(parents=True, exist_ok=True)
    deck = out / f"paper_matched_single_notch_{args.version}.inp"
    stats = write_deck(config, args.version, deck)
    user_subroutine = write_fortran_source(args.version, out, stats["physical_elements"])
    write_text_lf(out / "parameter_snapshot.yaml", yaml.safe_dump(config, sort_keys=False))
    write_diagnostics(config, args.version, out, stats)
    sources = [config_path, *SOURCE_FILES, user_subroutine]
    write_text_lf(
        out / "source_hashes.txt",
        "\n".join(f"{path.as_posix()}  {sha256(path)}" for path in sources if path.exists()) + "\n",
    )
    manifest = {
        "candidate": f"paper_matched_candidate_{args.version}",
        "config": config_path.as_posix(),
        "deck": deck.as_posix(),
        "deck_sha256": sha256(deck),
        "preserved_user_subroutine_source": PRESERVED_FORTRAN.as_posix(),
        "reconstruction_version": config["reconstruction_version"],
        "statistics": stats,
        "user_subroutine": user_subroutine.as_posix(),
        "user_subroutine_sha256": sha256(user_subroutine),
    }
    write_text_lf(out / "generation_manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
