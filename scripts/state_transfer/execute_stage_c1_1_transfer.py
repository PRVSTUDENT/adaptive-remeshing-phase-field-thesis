import sys
sys.stdout.write("STEP 1: SCRIPT STARTED\n")
sys.stdout.flush()

import os
import json
import math
from pathlib import Path

sys.stdout.write("STEP 2: BASIC IMPORTS OK\n")
sys.stdout.flush()

REPO_ROOT = Path(r"D:\Master thesis\Adaptive remeshing")
sys.path.insert(0, str(REPO_ROOT))

sys.stdout.write("STEP 3: IMPORTING ENGINE...\n")
sys.stdout.flush()

from scripts.state_transfer.mode1_state_transfer_engine import (
    Mode1Mesh,
    Mode1State,
    Mode1SpatialIndex,
    Mode1StateTransferEngine,
    parse_mode1_input_deck,
    compute_quad_gauss_points,
    compute_tri_gauss_points
)

sys.stdout.write("STEP 4: ENGINE IMPORTED OK\n")
sys.stdout.flush()

donor_inp = REPO_ROOT / "models" / "pandey_kumar_mode1" / "48_method_c_stage_c1_0_restart_positive_control" / "M1_MB_DONOR_WITH_RESTART.inp"
donor_json = REPO_ROOT / "models" / "pandey_kumar_mode1" / "48_method_c_stage_c1_0_restart_positive_control" / "evidence_1413814" / "donor_field_state.json"
target_inp = REPO_ROOT / "models" / "pandey_kumar_mode1" / "40_method_b_corrected_propagation_14k" / "M1_MB_CORRECTED_PROPAGATION_14K.inp"

pkg49_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "49_method_c_stage_c1_1_nonmatching_transfer"
pkg49_dir.mkdir(parents=True, exist_ok=True)
out_deck_path = pkg49_dir / "M1_MC_STAGE_C1_1_FORWARD_14K.inp"
out_metrics_path = pkg49_dir / "STAGE_C1_1_TRANSFER_METRICS.json"

sys.stdout.write(f"STEP 5: Parsing donor mesh from {donor_inp.name}...\n")
sys.stdout.flush()
donor_mesh = parse_mode1_input_deck(str(donor_inp))
sys.stdout.write(f"   Donor mesh: {donor_mesh.num_elements} elements, {donor_mesh.num_nodes} nodes.\n")
sys.stdout.flush()

sys.stdout.write(f"STEP 6: Loading donor state from {donor_json.name}...\n")
sys.stdout.flush()
with open(donor_json, "r", encoding="utf-8") as f:
    donor_raw = json.load(f)

donor_state = Mode1State()
donor_state.u_rp = tuple(donor_raw["u_rp"])

for nid_str, u_coords in donor_raw["u_nodal"].items():
    nid = int(nid_str)
    donor_state.u_nodal[nid] = (float(u_coords[0]), float(u_coords[1]))

elem_d_dict = {}
for eid_str, svals in donor_raw["elem_sdv"].items():
    eid = int(eid_str)
    d_vals = svals.get("SDV14", [0.0])
    avg_d = sum(d_vals) / float(len(d_vals))
    elem_d_dict[eid] = avg_d
    h_vals = svals.get("SDV2", [0.0])
    donor_state.H_gp[eid] = [max(0.0, float(h)) for h in h_vals]

node_d_accum = {nid: 0.0 for nid in donor_mesh.nodes}
node_w_accum = {nid: 0.0 for nid in donor_mesh.nodes}
for eid, conn in donor_mesh.elements_u1.items():
    d_elem = elem_d_dict.get(eid, 0.0)
    area = donor_mesh.compute_element_area(eid)
    for nid in conn:
        node_d_accum[nid] += d_elem * area
        node_w_accum[nid] += area

for nid in donor_mesh.nodes:
    if node_w_accum[nid] > 0.0:
        donor_state.d_nodal[nid] = max(0.0, min(1.0, node_d_accum[nid] / node_w_accum[nid]))
    else:
        donor_state.d_nodal[nid] = 0.0

sys.stdout.write(f"   Peak donor damage: {max(donor_state.d_nodal.values()):.6f}\n")
sys.stdout.flush()

sys.stdout.write(f"STEP 7: Parsing target mesh from {target_inp.name}...\n")
sys.stdout.flush()
target_mesh = parse_mode1_input_deck(str(target_inp))
sys.stdout.write(f"   Target mesh: {target_mesh.num_elements} elements, {target_mesh.num_nodes} nodes.\n")
sys.stdout.flush()

sys.stdout.write("STEP 8: Building spatial index and projecting state...\n")
sys.stdout.flush()
engine = Mode1StateTransferEngine(donor_mesh)
target_state = engine.project_state(target_mesh, donor_state, enforce_bc=True)
sys.stdout.write("   Projection complete!\n")
sys.stdout.flush()

sys.stdout.write(f"   Peak target damage: {max(target_state.d_nodal.values()):.6f}\n")
sys.stdout.write(f"   Peak target history H: {max(max(hl) for hl in target_state.H_gp.values()):.6f} kN/mm^2\n")
sys.stdout.write(f"   Min target history H: {min(min(hl) for hl in target_state.H_gp.values()):.8e} kN/mm^2\n")
sys.stdout.flush()

sys.stdout.write("STEP 9: Computing projection metrics...\n")
sys.stdout.flush()
metrics = engine.compute_projection_metrics(target_mesh, donor_state, target_state)
for k, v in sorted(metrics.items()):
    if isinstance(v, dict):
        sys.stdout.write(f"   {k}: {v.get('value')} {v.get('unit', '')} -> {v.get('verdict')}\n")
    else:
        sys.stdout.write(f"   {k}: {v}\n")
sys.stdout.flush()

sys.stdout.write(f"STEP 10: Assembling continuation deck at {out_deck_path.name}...\n")
sys.stdout.flush()
engine.assemble_continuation_deck(
    recipient_mesh=target_mesh,
    target_state=target_state,
    output_inp_path=str(out_deck_path),
    u_handoff=0.0050,
    u_final=0.0100,
    num_increments=5000,
    continuation_mode="equilibrate"
)
deck_size = os.path.getsize(out_deck_path)
sys.stdout.write(f"   Continuation deck size: {deck_size:,} bytes.\n")
sys.stdout.flush()

with open(out_metrics_path, "w", encoding="utf-8") as fp:
    json.dump(metrics, fp, indent=2)
sys.stdout.write(f"STEP 11: Metrics saved to {out_metrics_path.name}!\n")
sys.stdout.write("ALL STAGES COMPLETED SUCCESSFULLY.\n")
sys.stdout.flush()
