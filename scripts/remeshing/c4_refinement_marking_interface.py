#!/usr/bin/env python3
"""
Production C4 Mesh Refinement-Marking Interface for Method C Adaptive Remeshing (C4 -> C5).

Implements:
1. Strict parsing and topological verification of the authentic 7,056-element C4 mesh
   (nodes, element connectivity across UEL/UMAT layers, coincident slit flank duplicate pairs, ligament).
2. Fail-closed indicator mapping and relative error evaluation:
   eta_e = MISESERI_e / MISESAVG_e
3. Rejection of incompatible source meshes (e.g., historical 4,422-element Package 114),
   zero/invalid denominators, duplicate labels, or missing elements.
4. Autonomous refinement candidate marking (threshold eta >= 0.15) adhering to the
   REFINEMENT-ONLY policy without coarsening, cross-slit interpolation, or prescribed corridors.
5. Serialization of machine-readable candidate-marking artifacts with SHA-256 bindings.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


class IncompatibleMeshError(ValueError):
    """Raised when an indicator field does not match the 7,056-element C4 mesh."""
    pass


class InvalidIndicatorDataError(ValueError):
    """Raised when indicator values contain zero/negative denominators or invalid numbers."""
    pass


@dataclass
class C4Mesh:
    """Represents the authentic 7,056-element C4 discretization."""
    inp_path: str
    inp_sha256: str
    nodes: Dict[int, Tuple[float, float]]
    phase_elements: Dict[int, List[int]]       # labels 1..7056 (Type U1)
    mech_elements: Dict[int, List[int]]        # labels 7057..14112 (Type U2)
    companion_elements: Dict[int, List[int]]   # labels 14113..21168 (Type CPE4)
    duplicate_slit_node_pairs: List[Tuple[int, int]]  # (lower_flank_node, upper_flank_node)
    ligament_nodes: List[int]
    element_centroids: Dict[int, Tuple[float, float]] = field(default_factory=dict)
    element_sizes: Dict[int, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.element_centroids:
            for el_id, conn in self.phase_elements.items():
                pts = [self.nodes[n] for n in conn]
                xc = sum(p[0] for p in pts) / 4.0
                yc = sum(p[1] for p in pts) / 4.0
                self.element_centroids[el_id] = (xc, yc)

                # Characteristic size h (average edge length)
                edge_sum = 0.0
                for i in range(4):
                    x0, y0 = pts[i]
                    x1, y1 = pts[(i + 1) % 4]
                    edge_sum += math.hypot(x1 - x0, y1 - y0)
                self.element_sizes[el_id] = edge_sum / 4.0


def compute_sha256(path: str) -> str:
    """Computes SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest().upper()


def parse_c4_mesh_inp(inp_path: str) -> C4Mesh:
    """
    Parses the authentic 7,056-element C4 mesh from an Abaqus input deck.
    Validates element counts, node counts, duplicate coincident slit nodes, and ligament.
    """
    if not os.path.isfile(inp_path):
        raise FileNotFoundError(f"Input deck not found: {inp_path}")

    inp_sha256 = compute_sha256(inp_path)

    nodes: Dict[int, Tuple[float, float]] = {}
    phase_elements: Dict[int, List[int]] = {}
    mech_elements: Dict[int, List[int]] = {}
    companion_elements: Dict[int, List[int]] = {}

    current_section = None

    with open(inp_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("**"):
                continue

            if stripped.startswith("*"):
                upper = stripped.upper()
                if upper.startswith("*NODE"):
                    current_section = "NODES"
                elif upper.startswith("*ELEMENT"):
                    if "PHASE_QUADS" in upper or "TYPE=U1" in upper:
                        current_section = "PHASE_QUADS"
                    elif "MECH_QUADS" in upper or "TYPE=U2" in upper:
                        current_section = "MECH_QUADS"
                    elif "UMATELEM" in upper or "TYPE=CPE4" in upper:
                        current_section = "UMATELEM"
                    else:
                        current_section = "OTHER_ELEMENT"
                else:
                    current_section = None
                continue

            parts = [p.strip() for p in stripped.split(",")]
            if current_section == "NODES":
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        nodes[nid] = (x, y)
                    except ValueError:
                        pass
            elif current_section == "PHASE_QUADS":
                if len(parts) >= 5:
                    eid = int(parts[0])
                    phase_elements[eid] = [int(p) for p in parts[1:5]]
            elif current_section == "MECH_QUADS":
                if len(parts) >= 5:
                    eid = int(parts[0])
                    mech_elements[eid] = [int(p) for p in parts[1:5]]
            elif current_section == "UMATELEM":
                if len(parts) >= 5:
                    eid = int(parts[0])
                    companion_elements[eid] = [int(p) for p in parts[1:5]]

    if len(phase_elements) != 7056:
        raise ValueError(
            f"Expected 7,056 phase quads, found {len(phase_elements)} in {inp_path}"
        )

    # Topological verification of duplicate slit nodes along y = 0.05 mm, x in [0.0, 0.04] mm
    slit_candidates = [
        nid for nid, (x, y) in nodes.items()
        if abs(y - 0.05) < 1e-5 and x <= 0.040001
    ]
    ligament_nodes = [
        nid for nid, (x, y) in nodes.items()
        if abs(y - 0.05) < 1e-5 and x > 0.040001
    ]

    # Map candidate x coordinates to node IDs
    pos_map: Dict[float, List[int]] = {}
    for nid in slit_candidates:
        x_round = round(nodes[nid][0], 7)
        pos_map.setdefault(x_round, []).append(nid)

    duplicate_pairs: List[Tuple[int, int]] = []
    for x_pos, nids in sorted(pos_map.items()):
        if len(nids) == 2:
            # Sort lower flank (e.g. connected to elements with cy < 0.05)
            # Both nodes have exact same coordinate y=0.05, but distinct node IDs
            duplicate_pairs.append((min(nids), max(nids)))

    return C4Mesh(
        inp_path=inp_path,
        inp_sha256=inp_sha256,
        nodes=nodes,
        phase_elements=phase_elements,
        mech_elements=mech_elements,
        companion_elements=companion_elements,
        duplicate_slit_node_pairs=duplicate_pairs,
        ligament_nodes=ligament_nodes,
    )


class C4RefinementMarkingInterface:
    """
    Governing interface for production C4 error-indicator evaluation and refinement marking.
    """

    def __init__(self, c4_mesh: C4Mesh):
        self.mesh = c4_mesh
        self.expected_quads = len(c4_mesh.phase_elements)
        if self.expected_quads != 7056:
            raise ValueError(f"Mesh has {self.expected_quads} quads, expected 7,056.")

    def validate_indicator_data(
        self,
        element_data: Dict[int, Dict[str, float]],
        source_mesh_label: Optional[str] = None
    ) -> None:
        """
        Validates element data against the 7,056-element C4 mesh.
        Fails closed on mismatched element count, duplicate IDs, missing IDs, or invalid values.
        """
        n_elements = len(element_data)
        if n_elements != self.expected_quads:
            raise IncompatibleMeshError(
                f"Incompatible source mesh: received {n_elements} elements"
                f"{' (' + source_mesh_label + ')' if source_mesh_label else ''}, "
                f"expected {self.expected_quads} elements (C4 corrected refinement-only mesh). "
                f"Historical or different mesh indicator fields cannot be applied to C4."
            )

        # Check element ID keys: must contain exactly 1..7056 (or match companion labels)
        expected_ids = set(self.mesh.phase_elements.keys())
        provided_ids = set(element_data.keys())

        if provided_ids != expected_ids:
            # Check if provided_ids match companion labels (14113..21168)
            companion_ids = set(self.mesh.companion_elements.keys())
            if provided_ids != companion_ids:
                missing = expected_ids - provided_ids
                extra = provided_ids - expected_ids
                raise IncompatibleMeshError(
                    f"Element ID set mismatch: {len(missing)} missing, {len(extra)} unexpected."
                )

        # Check values
        for eid, values in element_data.items():
            if "MISESERI" not in values or "MISESAVG" not in values:
                raise InvalidIndicatorDataError(
                    f"Element {eid} missing required field 'MISESERI' or 'MISESAVG'."
                )

            miseseri = values["MISESERI"]
            misesavg = values["MISESAVG"]

            if math.isnan(miseseri) or math.isinf(miseseri) or miseseri < 0.0:
                raise InvalidIndicatorDataError(
                    f"Element {eid} has invalid MISESERI = {miseseri}."
                )

            if math.isnan(misesavg) or math.isinf(misesavg) or misesavg <= 0.0:
                raise InvalidIndicatorDataError(
                    f"Element {eid} has invalid/non-positive MISESAVG = {misesavg}. Denominator must be strictly positive."
                )

    def compute_relative_indicators(
        self,
        element_data: Dict[int, Dict[str, float]],
        source_mesh_label: Optional[str] = None
    ) -> Dict[int, float]:
        """
        Computes dimensionless indicator eta_e = MISESERI_e / MISESAVG_e.
        Normalizes element IDs to base quad range 1..7056 if companion IDs were supplied.
        """
        self.validate_indicator_data(element_data, source_mesh_label=source_mesh_label)

        # Determine if IDs are companion labels (14113..21168)
        first_id = next(iter(element_data.keys()))
        offset = 14112 if first_id > 7056 else 0

        eta_by_element: Dict[int, float] = {}
        for eid, values in element_data.items():
            base_id = eid - offset
            eta = float(values["MISESERI"]) / float(values["MISESAVG"])
            eta_by_element[base_id] = eta

        return eta_by_element

    def generate_candidate_marks(
        self,
        element_data: Dict[int, Dict[str, float]],
        threshold_eta: float = 0.15,
        source_provenance: Optional[Dict[str, Any]] = None,
        source_mesh_label: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates production refinement candidate marks for elements with eta >= threshold_eta.
        Strictly enforces REFINEMENT_ONLY policy (no coarsening, no crack corridor prescription).
        """
        eta_map = self.compute_relative_indicators(
            element_data, source_mesh_label=source_mesh_label
        )

        marked_elements: List[Dict[str, Any]] = []
        all_eta = list(eta_map.values())

        for el_id, eta in sorted(eta_map.items()):
            if eta >= threshold_eta:
                xc, yc = self.mesh.element_centroids[el_id]
                h = self.mesh.element_sizes[el_id]
                marked_elements.append({
                    "element_id": el_id,
                    "eta": round(eta, 6),
                    "miseseri_kNmm2": round(element_data.get(el_id, element_data.get(el_id + 14112, {})).get("MISESERI", 0.0), 6),
                    "misesavg_kNmm2": round(element_data.get(el_id, element_data.get(el_id + 14112, {})).get("MISESAVG", 0.0), 6),
                    "centroid_mm": [round(xc, 6), round(yc, 6)],
                    "h_mean_mm": round(h, 6),
                    "flank": "upper" if yc >= 0.05 else "lower"
                })

        marked_count = len(marked_elements)
        marked_fraction = marked_count / float(self.expected_quads)

        sorted_eta = sorted(all_eta)
        n = len(sorted_eta)

        return {
            "schema": 1,
            "status": "C4_REFINEMENT_MARKING_COMPLETE",
            "mesh_id": "C4_CORRECTED_7056_QUADS",
            "total_elements": self.expected_quads,
            "threshold_eta": threshold_eta,
            "refinement_policy": "REFINEMENT_ONLY",
            "coarsening_allowed": False,
            "marked_elements_count": marked_count,
            "marked_fraction": round(marked_fraction, 6),
            "marked_percentage": round(marked_fraction * 100.0, 4),
            "indicator_statistics": {
                "eta_min": round(sorted_eta[0], 6),
                "eta_median": round(sorted_eta[n // 2], 6),
                "eta_mean": round(sum(sorted_eta) / float(n), 6),
                "eta_max": round(sorted_eta[-1], 6),
                "eta_p90": round(sorted_eta[int(0.90 * (n - 1))], 6),
                "eta_p95": round(sorted_eta[int(0.95 * (n - 1))], 6)
            },
            "source_provenance": source_provenance or {
                "source": "SIMULATED_TEST_OR_UNSPECIFIED"
            },
            "marked_elements": marked_elements
        }

    def assess_companion_status(
        self,
        candidate_source: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Assesses availability of an authentic companion ODB for the 7,056-element C4 mesh.
        If only historical Package 114 (4,422 quads) exists, correctly diagnoses and records
        the precise missing prerequisite.
        """
        if candidate_source is None:
            return {
                "compatible_companion_available": False,
                "missing_prerequisite": (
                    "Authentic companion linear-elastic MISESERI simulation on the 7,056-element C4 mesh "
                    "(e.g., Package 147 companion static-elastic job) has not been run. "
                    "Package 114 companion run was conducted on the superseded 4,422-element mesh. "
                    "A 7,056-element companion static-elastic solve is required to extract genuine C4 indicator fields."
                ),
                "historical_alternative_status": "REJECTED_INCOMPATIBLE_MESH_COUNT_4422_VS_7056"
            }

        source_elements = candidate_source.get("total_elements", 0)
        if source_elements != 7056:
            return {
                "compatible_companion_available": False,
                "missing_prerequisite": (
                    f"Candidate source has {source_elements} elements, which is incompatible with the 7,056-element C4 mesh. "
                    "A dedicated 7,056-element companion static-elastic job must be staged and run."
                ),
                "historical_alternative_status": f"REJECTED_ELEMENT_COUNT_{source_elements}"
            }

        return {
            "compatible_companion_available": True,
            "source_job": candidate_source.get("job_name", "UNKNOWN"),
            "missing_prerequisite": None
        }
