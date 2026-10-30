# -*- coding: utf-8 -*-
"""
build_package146_147_transfer_deck.py
Mode-I Method C: Source-Independent Package 146 -> Package 147 State-Transfer Deck Generator.
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Generates the complete, physically admissible Package 148 continuation deck from
Package 146 donor (5,112 quads, 5,290 nodes, 20,448 GPs) to Package 147 receiver (7,056 quads, 7,265 nodes, 28,224 GPs):
  - Ingests authentic Package 146 Step-1 endpoint outputs (u1, u2, u3=d at nodes, SDV2=H at Gauss points).
  - Isolates crack slit along y = 0.05 mm, x <= 0.04 mm, ensuring strict upper/lower flank independence.
  - Projects nodal displacements (u1, u2) and nodal damage (d0) using inverse isoparametric bilinear quad mapping.
  - Projects Gauss-point history H0 using conservative host-nearest GP mapping.
  - Generates:
      1. nodal_displacements_initial.csv (7,265 rows: node_id, u1, u2)
      2. nodal_phase_field_initial.csv (7,265 rows: node_id, d0)
      3. d_lower_bounds.csv (7,056 rows: eid, d0_1..4, h0_1..4)
      4. initial_conditions_solution.inc (*INITIAL CONDITIONS, TYPE=SOLUTION for 7,056 phase quads, populating SVARS 9..12)
      5. active_set_boundary_cards.inc (Dirichlet boundary cards for active nodes: node_id, 3, 3, d_value)
      6. M1_C4_PACKAGE148_STATE_TRANSFER.inp (Master executable continuation deck)
      7. PACKAGE_MANIFEST.json (Full provenance and SHA-256 bindings)
"""

from __future__ import print_function, division
import os
import sys
import math
import json
import gzip
import shutil
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.c3_int_to_c4_spatial_mapping import (
    Mesh2D, SpatialTransferMapper
)

# Reference parameters for Pandey-Kumar Mode-I Step-1 endpoint
TARGET_DISP_STEP1_MM = 0.0018003125442191958
DISP_TOLERANCE_MM = 1e-6
SEAM_Y = 0.050
SEAM_X_MAX = 0.040

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
DONOR_INP_DEFAULT = REPO_ROOT / "models/pandey_kumar_mode1/146_c3_fine_donor/M1_C3_FINE_PACKAGE146_DONOR.inp"
RECEIVER_INP_DEFAULT = REPO_ROOT / "models/pandey_kumar_mode1/147_c4_corrected_reference/M1_C4_CORRECTED_PACKAGE147_REF.inp"
DONOR_DAT_DEFAULT = REPO_ROOT / "tests/fixtures/package146147/146_step1_dat.txt.gz"
EVALUATION_JSON_DEFAULT = REPO_ROOT / "results/validation/package146147/evaluation.json"
FROZEN_UEL_DEFAULT = REPO_ROOT / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"


def sha256_file(p):
    """Computes SHA-256 digest in uppercase."""
    h = hashlib.sha256()
    with open(str(p), "rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest().upper()


def parse_donor_dat_file(dat_path):
    """
    Parses node table from Abaqus DAT file (plain or gzip).
    Returns dict: nid -> (u1, u2, u3, rf1, rf2, rf3).
    """
    nodes = {}
    p = Path(dat_path)
    opener = gzip.open if p.suffix == ".gz" or str(p).endswith(".gz") else open
    with opener(str(p), "rt") as f:
        in_table = False
        for line in f:
            if "NODE FOOT-" in line and "U1" in line and "U2" in line and "U3" in line:
                in_table = True
                continue
            if in_table:
                line_s = line.strip()
                if not line_s or "NOTE" in line_s or line_s.startswith("-"):
                    continue
                if line_s.startswith("MAXIMUM") or line_s.startswith("MINIMUM") or "THE FOLLOWING" in line_s:
                    in_table = False
                    continue
                parts = line_s.split()
                if len(parts) >= 4 and parts[0].isdigit():
                    nid = int(parts[0])
                    u1 = float(parts[1])
                    u2 = float(parts[2])
                    u3 = float(parts[3])
                    rf1 = float(parts[4]) if len(parts) > 4 else 0.0
                    rf2 = float(parts[5]) if len(parts) > 5 else 0.0
                    rf3 = float(parts[6]) if len(parts) > 6 else 0.0
                    nodes[nid] = (u1, u2, u3, rf1, rf2, rf3)
    return nodes


def parse_donor_history_from_evaluation(eval_path):
    """
    Parses Gauss-point history SDV2 for donor package 146 from evaluation.json.
    Returns dict: (physical_eid, gp_idx) -> history_value.
    In Package 146, overlay CPE4 elements are 10225..15336.
    Physical eid = overlay_eid - 10224 (i.e. 1..5112).
    """
    with open(str(eval_path), "r") as f:
        data = json.load(f)
    p146 = data["packages"]["146"]
    history_keys = p146["history_keys"]
    history_endpoint = p146["history_endpoint"]

    gp_history = {}
    for key, val in zip(history_keys, history_endpoint):
        # Format: 'PART-1-1:<overlay_eid>:<gp_idx>'
        parts = key.split(":")
        overlay_eid = int(parts[1])
        gp_idx = int(parts[2])
        # UMAT SDV2 uses the UEL perimeter numbering. The spatial mapper uses
        # row numbering, so both coordinates and values must be permuted.
        gp_idx = {1: 1, 2: 2, 3: 4, 4: 3}[gp_idx]
        # Physical quad element index
        phys_eid = overlay_eid - 10224
        if 1 <= phys_eid <= 5112:
            index = (phys_eid, gp_idx)
        else:
            raise ValueError('FAIL_CLOSED: invalid donor overlay element')
        if index in gp_history or not math.isfinite(float(val)) or float(val) < 0:
            raise ValueError('FAIL_CLOSED: duplicate/invalid donor history')
        gp_history[index] = float(val)
    if len(history_keys) != len(history_endpoint):
        raise ValueError('FAIL_CLOSED: truncated donor history')
    return gp_history


class Package146To147DeckGenerator(object):
    """
    Assembles complete, physically admissible Package 146 -> Package 147 state-transfer continuation decks.
    Strictly verifies authentic donor outputs, crack-flank topology, and bitwise frozen UEL.
    """

    def __init__(self, output_dir, donor_inp=None, receiver_inp=None,
                 donor_dat=None, eval_json=None, frozen_uel=None):
        self.output_dir = Path(output_dir)
        self.donor_inp_path = Path(donor_inp) if donor_inp else DONOR_INP_DEFAULT
        self.receiver_inp_path = Path(receiver_inp) if receiver_inp else RECEIVER_INP_DEFAULT
        self.donor_dat_path = Path(donor_dat) if donor_dat else DONOR_DAT_DEFAULT
        self.eval_json_path = Path(eval_json) if eval_json else EVALUATION_JSON_DEFAULT
        self.frozen_uel_path = Path(frozen_uel) if frozen_uel else FROZEN_UEL_DEFAULT

        self.donor_nodes_data = {}      # nid -> (u1, u2, u3, rf1, rf2, rf3)
        self.donor_gp_history = {}      # (eid, gp_idx) -> H0
        self.donor_mesh = None
        self.receiver_mesh = None
        self.spatial_mapper = None

    def verify_prerequisites(self):
        """Verifies that all required authentic files exist and hashes match where bound."""
        for name, p in [
            ("Donor input deck", self.donor_inp_path),
            ("Receiver input deck", self.receiver_inp_path),
            ("Donor DAT output", self.donor_dat_path),
            ("Evaluation JSON", self.eval_json_path),
            ("Frozen UEL", self.frozen_uel_path),
        ]:
            if not p.exists():
                raise RuntimeError("FAIL_CLOSED: Missing prerequisite file [%s]: %s" % (name, p))

        # Bitwise verify frozen UEL
        uel_hash = sha256_file(self.frozen_uel_path)
        if uel_hash != FROZEN_UEL_SHA256:
            raise ValueError("FAIL_CLOSED: Bitwise frozen UEL SHA-256 mismatch: %s != %s" %
                             (uel_hash, FROZEN_UEL_SHA256))
        return True

    def load_donor_data(self):
        """Loads donor nodal displacement/damage from DAT and GP history from evaluation.json."""
        self.donor_nodes_data = parse_donor_dat_file(self.donor_dat_path)
        if len(self.donor_nodes_data) != 5290:
            raise ValueError("FAIL_CLOSED: Expected 5290 donor nodes from DAT, parsed %d" %
                             len(self.donor_nodes_data))
        for values in self.donor_nodes_data.values():
            if not all(math.isfinite(v) for v in values) or not 0.0 <= values[2] <= 1.0:
                raise ValueError('FAIL_CLOSED: invalid authentic donor nodal state')

        self.donor_gp_history = parse_donor_history_from_evaluation(self.eval_json_path)
        if len(self.donor_gp_history) != 20448:
            raise ValueError("FAIL_CLOSED: Expected 20448 donor GP history values, parsed %d" %
                             len(self.donor_gp_history))
        return True

    def initialize_meshes_and_mapper(self):
        """Initializes Mesh2D instances for Package 146 and Package 147 and builds SpatialTransferMapper."""
        self.donor_mesh = Mesh2D.from_inp(
            str(self.donor_inp_path), name="Package146_Donor", max_physical_node=5290
        )
        self.receiver_mesh = Mesh2D.from_inp(
            str(self.receiver_inp_path), name="Package147_Receiver", max_physical_node=7265
        )

        if len(self.donor_mesh.nodes) != 5290 or len(self.donor_mesh.elements) != 5112:
            raise ValueError("FAIL_CLOSED: Unexpected donor mesh counts: %d nodes, %d elements" %
                             (len(self.donor_mesh.nodes), len(self.donor_mesh.elements)))

        if len(self.receiver_mesh.nodes) != 7265 or len(self.receiver_mesh.elements) != 7056:
            raise ValueError("FAIL_CLOSED: Unexpected receiver mesh counts: %d nodes, %d elements" %
                             (len(self.receiver_mesh.nodes), len(self.receiver_mesh.elements)))

        self.donor_mesh.classify_topology(seam_y=SEAM_Y, seam_x_max=SEAM_X_MAX)
        self.receiver_mesh.classify_topology(seam_y=SEAM_Y, seam_x_max=SEAM_X_MAX)

        self.donor_mesh.compute_gauss_points()
        self.receiver_mesh.compute_gauss_points()

        self.spatial_mapper = SpatialTransferMapper(self.donor_mesh, self.receiver_mesh, tol_geom=1e-5)
        return True

    def execute_state_projection(self):
        """
        Projects nodal displacements (u1, u2), nodal damage (d0), and Gauss-point history H0.
        Returns dictionary of mapped fields and stats.
        """
        node_map, node_stats, _ = self.spatial_mapper.build_node_transfer_map()
        gp_map, gp_stats, _ = self.spatial_mapper.build_gauss_point_transfer_map()

        # 1. Project nodal displacements (u1, u2)
        target_disp = {}
        for nid, mapping in node_map.items():
            host_eid = mapping["host_eid"]
            conn = self.donor_mesh.elements[host_eid]
            weights = mapping["weights"]

            u1_vals = [self.donor_nodes_data[n][0] for n in conn]
            u2_vals = [self.donor_nodes_data[n][1] for n in conn]

            tx = sum(w * u for w, u in zip(weights, u1_vals))
            ty = sum(w * u for w, u in zip(weights, u2_vals))
            target_disp[nid] = (tx, ty)

        # 2. Project nodal phase-field damage (d0)
        target_phase = {}
        for nid, mapping in node_map.items():
            host_eid = mapping["host_eid"]
            conn = self.donor_mesh.elements[host_eid]
            weights = mapping["weights"]

            d_vals = [self.donor_nodes_data[n][2] for n in conn]
            td = sum(w * d for w, d in zip(weights, d_vals))
            target_phase[nid] = max(0.0, min(1.0, td))

        # 3. Project Gauss point history H0 using HOST_NEAREST_GP operator
        target_gp_h = self.spatial_mapper.transfer_history_host_nearest(self.donor_gp_history, gp_map)

        # 4. Compute element-level GP damage lower bounds d0_gp via shape function interpolation
        target_gp_d0 = {}
        for (eid, gp_idx), (x_gp, y_gp, flank) in self.receiver_mesh.gauss_points.items():
            conn = self.receiver_mesh.elements[eid]
            pts = [self.receiver_mesh.nodes[n] for n in conn]
            d_nodal = [target_phase[n] for n in conn]
            xi, eta = self.spatial_mapper.receiver.gauss_points.get((eid, gp_idx), (None, None))[:2]
            # If not cached, get from standard local quad coordinates
            from scripts.state_transfer.c3_int_to_c4_spatial_mapping import QUAD_GP_LOCAL, quad_shape_functions
            xi_l, eta_l = QUAD_GP_LOCAL[gp_idx - 1]
            w_gp = quad_shape_functions(xi_l, eta_l)
            d_val = sum(w * d for w, d in zip(w_gp, d_nodal))
            target_gp_d0[(eid, gp_idx)] = max(0.0, min(1.0, d_val))

        return {
            "node_map": node_map,
            "gp_map": gp_map,
            "target_disp": target_disp,
            "target_phase": target_phase,
            "target_gp_h": target_gp_h,
            "target_gp_d0": target_gp_d0,
            "node_stats": node_stats,
            "gp_stats": gp_stats,
        }

    def generate_all_artifacts(self, projection=None):
        """Generates all CSV files, include files, master input deck, and manifest."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if (self.output_dir/'PACKAGE_MANIFEST.json').exists():
            raise RuntimeError('Preserve existing package; use a distinct candidate revision')
        if projection is None:
            projection = self.execute_state_projection()

        target_disp = projection["target_disp"]
        target_phase = projection["target_phase"]
        target_gp_h = projection["target_gp_h"]
        target_gp_d0 = projection["target_gp_d0"]

        # 1. nodal_displacements_initial.csv
        disp_csv = self.output_dir / "nodal_displacements_initial.csv"
        with open(str(disp_csv), "w") as f:
            f.write("node_id,u1,u2\n")
            for nid in sorted(target_disp.keys()):
                u1, u2 = target_disp[nid]
                f.write("%d,%.15e,%.15e\n" % (nid, u1, u2))

        # 2. nodal_phase_field_initial.csv
        phase_csv = self.output_dir / "nodal_phase_field_initial.csv"
        with open(str(phase_csv), "w") as f:
            f.write("node_id,d0\n")
            for nid in sorted(target_phase.keys()):
                f.write("%d,%.15e\n" % (nid, target_phase[nid]))

        # 3. d_lower_bounds.csv
        bounds_csv = self.output_dir / "d_lower_bounds.csv"
        with open(str(bounds_csv), "w") as f:
            f.write("element_id,d0_1,d0_2,d0_3,d0_4,h0_1,h0_2,h0_3,h0_4\n")
            for eid in sorted(self.receiver_mesh.elements.keys()):
                d_vals = [target_gp_d0.get((eid, k), 0.0) for k in (1, 2, 3, 4)]
                h_vals = [target_gp_h[(eid, k)] for k in (1, 2, 3, 4)]
                f.write("%d,%.15e,%.15e,%.15e,%.15e,%.15e,%.15e,%.15e,%.15e\n" %
                        (eid, d_vals[0], d_vals[1], d_vals[2], d_vals[3],
                         h_vals[0], h_vals[1], h_vals[2], h_vals[3]))

        # 4. initial_conditions_solution.inc
        # Format: *INITIAL CONDITIONS, TYPE=SOLUTION
        # 18 variables per element across 3 lines:
        # Line 1: eid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        # Line 2:   h1, h2, h3, h4, 0.0, 0.0, 0.0, 0.0
        # Line 3:   0.0, 0.0
        sol_inc = self.output_dir / "initial_conditions_solution.inc"
        with open(str(sol_inc), "w") as f:
            f.write("** ==========================================================\n")
            f.write("** INITIAL CONDITIONS: 4-Gauss-Point History Field Ingestion\n")
            f.write("** Populates SVARS(9..12) via frozen UEL lines 248-262\n")
            f.write("** Elements: 7056 Phase-Field Quads (1..7056)\n")
            f.write("** ==========================================================\n")
            f.write("*INITIAL CONDITIONS, TYPE=SOLUTION\n")
            for eid in sorted(self.receiver_mesh.elements.keys()):
                # Convert mapper row order to the frozen UEL SVARS perimeter order.
                h_vals = [target_gp_h[(eid, k)] for k in (1, 2, 4, 3)]
                f.write("%8d, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0\n" % eid)
                f.write("  0.0, %.8e, %.8e, %.8e, %.8e, 0.0, 0.0, 0.0\n" %
                        (h_vals[0], h_vals[1], h_vals[2], h_vals[3]))
                f.write("  0.0, 0.0, 0.0\n")

        # 5. active_set_boundary_cards.inc (Initial Stage A re-equilibration clamps all d0)
        active_inc = self.output_dir / "active_set_boundary_cards.inc"
        self.write_active_set_cards(target_phase, active_mask=None, out_path=active_inc)

        # 6. Copy frozen UEL into output directory
        out_uel = self.output_dir / "f42_mixed_uel.for"
        shutil.copyfile(str(self.frozen_uel_path), str(out_uel))

        # 7. Master continuation input deck: M1_C4_PACKAGE148_STATE_TRANSFER.inp
        master_inp = self.output_dir / "M1_C4_PACKAGE148_STATE_TRANSFER.inp"
        self.generate_master_input_deck(out_path=master_inp)

        # 8. PACKAGE_MANIFEST.json
        manifest = {
            "schema": 1,
            "history_gp_order": "MAPPER_ROW_FROM_UEL_PERIMETER",
            "runtime_source_hashes": {p.relative_to(REPO_ROOT).as_posix(): sha256_file(p) for p in
                                      (Path(__file__).resolve(),
                                       REPO_ROOT/'scripts/state_transfer/driver_package146_147_pdas_continuation.py',
                                       REPO_ROOT/'scripts/state_transfer/c3_int_to_c4_spatial_mapping.py',
                                       REPO_ROOT/'scripts/validation/extract_package148_iteration.py')},
            "execution_status": "OFFLINE_CANDIDATE_REQUIRES_INDEPENDENT_RUNTIME_REVIEW",
            "derived_from": "models/pandey_kumar_mode1/148_c4_package148_state_transfer/PACKAGE_MANIFEST.json",
            "source_hashes": {p.relative_to(REPO_ROOT).as_posix(): sha256_file(p) for p in
                              (self.donor_inp_path, self.receiver_inp_path,
                               self.donor_dat_path, self.eval_json_path)},
            "package": 148,
            "model_name": "M1_C4_PACKAGE148_STATE_TRANSFER",
            "donor": {
                "package": 146,
                "model_name": "M1_C3_FINE_PACKAGE146_DONOR",
                "physical_quads": len(self.donor_mesh.elements),
                "nodes": len(self.donor_mesh.nodes),
                "gauss_points": len(self.donor_mesh.gauss_points),
                "target_u_rp_mm": TARGET_DISP_STEP1_MM,
            },
            "receiver": {
                "package": 147,
                "model_name": "M1_C4_CORRECTED_PACKAGE147_REF",
                "physical_quads": len(self.receiver_mesh.elements),
                "nodes": len(self.receiver_mesh.nodes),
                "gauss_points": len(self.receiver_mesh.gauss_points),
            },
            "files": {
                "nodal_displacements_initial.csv": sha256_file(disp_csv),
                "nodal_phase_field_initial.csv": sha256_file(phase_csv),
                "d_lower_bounds.csv": sha256_file(bounds_csv),
                "initial_conditions_solution.inc": sha256_file(sol_inc),
                "active_set_boundary_cards.inc": sha256_file(active_inc),
                "f42_mixed_uel.for": sha256_file(out_uel),
                "M1_C4_PACKAGE148_STATE_TRANSFER.inp": sha256_file(master_inp),
            },
            "frozen_uel_sha256": FROZEN_UEL_SHA256,
            "active_set_strategy": "ALTERNATING_PDAS_ACTIVE_SET_DECOUPLING",
        }
        manifest_path = self.output_dir / "PACKAGE_MANIFEST.json"
        with open(str(manifest_path), "w") as f:
            json.dump(manifest, f, indent=2)

        return {
            "manifest_path": manifest_path,
            "master_inp": master_inp,
            "sol_inc": sol_inc,
            "active_inc": active_inc,
            "disp_csv": disp_csv,
            "phase_csv": phase_csv,
            "bounds_csv": bounds_csv,
        }

    def write_active_set_cards(self, target_phase, active_mask=None, out_path=None):
        """
        Writes phase DOF 3 boundary cards: node_id, 3, 3, d_value.
        If active_mask is None, clamps all receiver nodes to target_phase[nid].
        If active_mask is provided, clamps ONLY active nodes (active_mask[nid] == True).
        """
        if out_path is None:
            out_path = self.output_dir / "active_set_boundary_cards.inc"
        out_path = Path(out_path)
        with open(str(out_path), "w") as f:
            f.write("** Active Set boundary cards for PDAS Re-Equilibration\n")
            f.write("** Format: node_id, 3, 3, d_value\n")
            for nid in sorted(target_phase.keys()):
                if active_mask is None or active_mask.get(nid, True):
                    f.write("%d, 3, 3, %.8f\n" % (nid, target_phase[nid]))
        return out_path

    def generate_master_input_deck(self, out_path=None):
        """
        Assembles M1_C4_PACKAGE148_STATE_TRANSFER.inp by extracting base mesh definitions
        from Package 147 reference deck and appending solution initial conditions and Step 1.
        """
        if out_path is None:
            out_path = self.output_dir / "M1_C4_PACKAGE148_STATE_TRANSFER.inp"
        out_path = Path(out_path)

        # Read base mesh lines up to *STEP from Package 147 deck
        base_lines = []
        with open(str(self.receiver_inp_path), "r") as f:
            for idx, line in enumerate(f):
                if line.startswith("*Step"):
                    break
                # Skip original heading to provide custom one
                if idx < 7:
                    continue
                base_lines.append(line)

        with open(str(out_path), "w") as f:
            f.write("*Heading\n")
            f.write("** Package 148 Mode-I Nonmatching State Transfer & Re-Equilibration\n")
            f.write("** TEMPLATE ONLY: execute through the bounded coupled Python runtime, not a standalone solve\n")
            f.write("** Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER\n")
            f.write("** Donor Model: M1_C3_FINE_PACKAGE146_DONOR (5112 quads, 5290 nodes)\n")
            f.write("** Receiver Model: M1_C4_PACKAGE148_STATE_TRANSFER (7056 quads, 7265 nodes)\n")
            f.write("** Target Load: u_RP = %.15e mm\n" % TARGET_DISP_STEP1_MM)
            f.write("*Preprint, echo=NO, model=NO, history=NO, contact=NO\n")

            for line in base_lines:
                f.write(line)

            # Insert *INITIAL CONDITIONS, TYPE=SOLUTION
            f.write("** ==========================================================\n")
            f.write("** INITIAL CONDITIONS: 4-Gauss-Point History Field Ingestion\n")
            f.write("** Populates SVARS(9..12) via frozen UEL lines 248-262\n")
            f.write("** ==========================================================\n")
            f.write("*Include, input=initial_conditions_solution.inc\n")

            # Step 1: Same-Load Re-Equilibration
            f.write("** ==========================================================\n")
            f.write("** STEP 1: Same-Load Re-Equilibration at u = %.8f mm\n" % TARGET_DISP_STEP1_MM)
            f.write("** ==========================================================\n")
            f.write("*Step, name=C1-1-ReEquil, nlgeom=NO, inc=200\n")
            f.write("*Static\n")
            f.write("1.0, 1.0, 1.0E-8, 1.0\n")
            f.write("*Boundary\n")
            f.write("N_BOTTOM, 2, 2, 0.0\n")
            f.write("N_PIN, 1, 1, 0.0\n")
            f.write("N_RP, 1, 1, 0.0\n")
            f.write("N_RP, 2, 2, %.15e\n" % TARGET_DISP_STEP1_MM)
            f.write("*Include, input=active_set_boundary_cards.inc\n")
            f.write("** Output requests\n")
            f.write("*Output, field, frequency=1\n")
            f.write("*Node Output\n")
            f.write("U, RF\n")
            f.write("*Element Output, elset=umatelem\n")
            f.write("SDV, S, E\n")
            f.write("*Node Print, frequency=1\n")
            f.write("U, RF\n")
            f.write("*Output, history, frequency=1\n")
            f.write("*Node Output, nset=N_RP\n")
            f.write("U2, RF2\n")
            f.write("*Energy Output\n")
            f.write("ALLSE, ALLWK\n")
            f.write("*End Step\n")

        return out_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Package 146 -> Package 147 State Transfer Deck Generator")
    parser.add_argument("--output-dir", required=True, help='Distinct reviewed candidate revision; existing packages are preserved')
    parser.add_argument("--donor-inp", default=str(DONOR_INP_DEFAULT))
    parser.add_argument("--receiver-inp", default=str(RECEIVER_INP_DEFAULT))
    parser.add_argument("--donor-dat", default=str(DONOR_DAT_DEFAULT))
    parser.add_argument("--eval-json", default=str(EVALUATION_JSON_DEFAULT))
    args = parser.parse_args()

    gen = Package146To147DeckGenerator(
        output_dir=args.output_dir,
        donor_inp=args.donor_inp,
        receiver_inp=args.receiver_inp,
        donor_dat=args.donor_dat,
        eval_json=args.eval_json,
    )
    print("Verifying prerequisites...")
    gen.verify_prerequisites()
    print("Loading authentic donor outputs...")
    gen.load_donor_data()
    print("Initializing meshes and spatial mapper...")
    gen.initialize_meshes_and_mapper()
    print("Projecting fields (nodal displacement, phase damage, GP history)...")
    proj = gen.execute_state_projection()
    print("Generating transfer deck artifacts...")
    res = gen.generate_all_artifacts(proj)
    print("Completed! Manifest written to %s" % res["manifest_path"])


if __name__ == "__main__":
    main()
