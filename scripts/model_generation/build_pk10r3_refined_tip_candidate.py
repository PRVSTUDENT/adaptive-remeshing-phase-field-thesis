#!/usr/bin/env python3
"""
Generator and Quality Auditor for Refined-Tip Mode-II Diagnostic Candidate:
`M2CORR_PK10R3_REFINED_TIP`

Refines the local crack-band/tip region from h = 0.0050 mm to h = 0.0020 mm (h/l0 = 0.1333 <= 0.15)
to serve as the smallest controlled diagnostic test of the PK10R2 localization discrepancy.

Preserves:
- True physical open slit along y = 0, x in [-0.5, 0.0] with split flank nodes.
- Rigid top-edge individual *Equation constraints (u1_i = u1_RP for every node in N_TOP).
- 3-Layer UEL structure (Layer 1 Phase U1, Layer 2 Disp U2, Layer 3 Vis CPE4).
- Material properties: E=210.0 kN/mm^2, nu=0.3, Gc=0.0027 kN/mm, l0=0.015 mm, k=1e-7.
- Monotonic shear loading to U1 = 0.050000 mm.
"""

import os
import sys
import json
import math
import hashlib
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP"
AUTH_FOR = ROOT / "models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/f42_mixed_uel.for"
NOTIF_SH = ROOT / "scripts/hpc/notifications/job_notifications.sh"

TOL = 1.0e-10

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def _round_coord(val):
    r = round(val, 10)
    return 0.0 if abs(r) < 5.0e-9 else r

def _graded_sizes(length, local_h, global_h, ratio):
    transition = []
    size = local_h
    while size < global_h:
        transition.append(size)
        size *= ratio
    if transition[-1] < global_h:
        transition.append(global_h)
    transition_sum = sum(transition)
    if transition_sum >= length:
        n = max(1, round(length / local_h))
        return [length / n] * n
    remaining = length - transition_sum
    coarse_count = max(1, int((remaining + global_h - TOL) // global_h))
    coarse = [remaining / coarse_count] * coarse_count
    return coarse + list(reversed(transition))

def make_axis_spacings():
    local_h = 0.0020
    global_h = 0.0250
    ratio = 1.35

    
    # X-axis: -0.5 to 0.5 with refined zone [-0.02, 0.5]
    x_start = -0.5
    x_refined_min = -0.02
    x_end = 0.5
    
    left_x_sizes = _graded_sizes(x_refined_min - x_start, local_h, global_h, ratio)
    refined_x_count = round((x_end - x_refined_min) / local_h)
    x_sizes = left_x_sizes + [local_h] * refined_x_count
    
    x_coords = [x_start]
    for s in x_sizes:
        x_coords.append(_round_coord(x_coords[-1] + s))
    x_coords[-1] = 0.5
    
    # Y-axis: -0.5 to 0.5 with refined corridor [-0.01, 0.01] around y=0
    y_start = -0.5
    y_refined_min = -0.01
    y_refined_max = 0.01
    y_end = 0.5
    
    bot_y_sizes = _graded_sizes(y_refined_min - y_start, local_h, global_h, ratio)
    refined_y_count = round((y_refined_max - y_refined_min) / local_h)
    top_y_sizes = list(reversed(_graded_sizes(y_end - y_refined_max, local_h, global_h, ratio)))
    y_sizes = bot_y_sizes + [local_h] * refined_y_count + top_y_sizes
    
    y_coords = [y_start]
    for s in y_sizes:
        y_coords.append(_round_coord(y_coords[-1] + s))
    y_coords[-1] = 0.5
    
    return x_coords, y_coords

class MeshGenerator:
    def __init__(self, x_coords, y_coords):
        self.x_coords = x_coords
        self.y_coords = y_coords
        self.nodes = {}       # key: (i, j, side) -> nid
        self.node_coords = {} # nid -> (x, y)
        self.next_node = 1
        
    def _key(self, i, j, side="shared"):
        x = self.x_coords[i]
        y = self.y_coords[j]
        # Open notch slit along y = 0 for -0.5 <= x < 0.0
        if abs(y) < TOL and -0.5 <= x < 0.0:
            return (i, j, side)
        return (i, j, "shared")
        
    def node(self, i, j, side="shared"):
        k = self._key(i, j, side)
        if k not in self.nodes:
            self.nodes[k] = self.next_node
            self.node_coords[self.next_node] = (self.x_coords[i], self.y_coords[j])
            self.next_node += 1
        return self.nodes[k]
        
    def build(self):
        # 1. Build nodes
        for j in range(len(self.y_coords)):
            for i in range(len(self.x_coords)):
                y = self.y_coords[j]
                x = self.x_coords[i]
                if abs(y) < TOL and -0.5 <= x < 0.0:
                    self.node(i, j, "lower")
                    self.node(i, j, "upper")
                else:
                    self.node(i, j)
                    
        # 2. Build quad elements
        zero_j = min(range(len(self.y_coords)), key=lambda j: abs(self.y_coords[j]))
        quads = []
        for j in range(len(self.y_coords) - 1):
            for i in range(len(self.x_coords) - 1):
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
                    
                quads.append((n1, n2, n3, n4))
        return quads

def generate_candidate_package():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    job_name = "M2CORR_PK10R3_REFINED_TIP"
    
    x_coords, y_coords = make_axis_spacings()
    gen = MeshGenerator(x_coords, y_coords)
    quads = gen.build()
    nodes = gen.node_coords
    n_phys = len(quads)
    
    print("================================================================================")
    print(f"GENERATING REFINED-TIP CANDIDATE PACKAGE: {job_name}")
    print("================================================================================")
    print(f"Physical Node Count: {len(nodes)}")
    print(f"Physical Quad Count: {n_phys}")
    print(f"Grid X-stations: {len(x_coords)}, Y-stations: {len(y_coords)}")
    
    # 1. Quality & Topology Audit Checks
    areas = []
    aspect_ratios = []
    for (n1, n2, n3, n4) in quads:
        p1, p2, p3, p4 = nodes[n1], nodes[n2], nodes[n3], nodes[n4]
        area = 0.5 * (p1[0]*p2[1] + p2[0]*p3[1] + p3[0]*p4[1] + p4[0]*p1[1] - (p1[1]*p2[0] + p2[1]*p3[0] + p3[1]*p4[0] + p4[1]*p1[0]))
        if area <= 0.0:
            raise ValueError(f"Negative or zero Jacobian area {area} in quad ({n1},{n2},{n3},{n4})")
        areas.append(area)
        dx1 = math.hypot(p2[0]-p1[0], p2[1]-p1[1])
        dx2 = math.hypot(p3[0]-p2[0], p3[1]-p2[1])
        dx3 = math.hypot(p4[0]-p3[0], p4[1]-p3[1])
        dx4 = math.hypot(p1[0]-p4[0], p1[1]-p4[1])
        aspect_ratios.append(max(dx1,dx2,dx3,dx4) / max(min(dx1,dx2,dx3,dx4), 1e-9))
        
    total_area = sum(areas)
    min_h = math.sqrt(min(areas))
    max_h = math.sqrt(max(areas))
    print(f"Total Specimen Area: {total_area:.8f} mm^2 (Exact: 1.00000000)")
    print(f"Element Area min: {min(areas):.6e} (h_min = {min_h:.6f} mm, h/l0 = {min_h/0.015:.4f})")
    print(f"Element Area max: {max(areas):.6e} (h_max = {max_h:.6f} mm)")
    print(f"Aspect Ratio min: {min(aspect_ratios):.3f}, max: {max(aspect_ratios):.3f}, median: {statistics.median(aspect_ratios):.3f}")
    
    # Sets
    top_nodes = sorted([nid for nid, (x, y) in nodes.items() if abs(y - 0.5) < TOL])
    bot_nodes = sorted([nid for nid, (x, y) in nodes.items() if abs(y - (-0.5)) < TOL])
    rp_nid = 99999
    
    # Check crack slit
    slit_nodes = [(nid, nodes[nid]) for nid in nodes if abs(nodes[nid][1]) < 1e-5 and -0.5 <= nodes[nid][0] < 0.0]
    print(f"Crack slit duplicate node count: {len(slit_nodes)} ({len(slit_nodes)//2} split flank pairs)")
    
    # 2. Build INP Deck
    inp_lines = []
    inp_lines.append("*Heading")
    inp_lines.append(f"** Mode-II Refined-Tip Diagnostic Candidate: {job_name}")
    inp_lines.append(f"** Lineage: Staggered Phase-Mechanical Mixed UEL ({n_phys} physical quads)")
    inp_lines.append(f"** Formulation: l0=0.015 mm, Gc=0.0027 kN/mm, E=210.0 kN/mm^2, nu=0.3, k=1e-07, NPHYS={n_phys}")
    inp_lines.append("** Monotonic Shear Loading to U1 = 0.050000 mm")
    inp_lines.append("*Preprint, echo=NO, model=NO, history=NO, contact=NO")
    inp_lines.append("** ==========================================================")
    inp_lines.append("** USER ELEMENTS (Clean 6-slot ABI: Layer 1 Phase U1, Layer 2 Mech U2)")
    inp_lines.append("** ==========================================================")
    inp_lines.append("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM")
    inp_lines.append("3")
    inp_lines.append("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM")
    inp_lines.append("1, 2")
    inp_lines.append("** ==========================================================")
    inp_lines.append("** NODES")
    inp_lines.append("** ==========================================================")
    inp_lines.append("*Node")
    for nid in sorted(nodes.keys()):
        x, y = nodes[nid]
        inp_lines.append(f"{nid}, {x:.10f}, {y:.10f}")
    inp_lines.append(f"{rp_nid}, 0.0000000000, 0.5000000000")
    
    inp_lines.append("** ==========================================================")
    inp_lines.append(f"** LAYER 1: Phase UEL (Elements 1..{n_phys})")
    inp_lines.append("** ==========================================================")
    inp_lines.append("*Element, type=U1, elset=PHASE_QUAD")
    for eid, (n1, n2, n3, n4) in enumerate(quads, start=1):
        inp_lines.append(f"{eid}, {n1}, {n2}, {n3}, {n4}")
        
    inp_lines.append("** ==========================================================")
    inp_lines.append(f"** LAYER 2: Displacement UEL (Elements {n_phys+1}..{2*n_phys})")
    inp_lines.append("** ==========================================================")
    inp_lines.append("*Element, type=U2, elset=DISP_QUAD")
    for eid, (n1, n2, n3, n4) in enumerate(quads, start=n_phys+1):
        inp_lines.append(f"{eid}, {n1}, {n2}, {n3}, {n4}")
        
    inp_lines.append("** ==========================================================")
    inp_lines.append(f"** LAYER 3: Visualization CPE4 (Elements {2*n_phys+1}..{3*n_phys})")
    inp_lines.append("** ==========================================================")
    inp_lines.append("*Element, type=CPE4, elset=VIS_QUAD")
    for eid, (n1, n2, n3, n4) in enumerate(quads, start=2*n_phys+1):
        inp_lines.append(f"{eid}, {n1}, {n2}, {n3}, {n4}")
        
    inp_lines.append("** ==========================================================")
    inp_lines.append("** NODE SETS")
    inp_lines.append("** ==========================================================")
    inp_lines.append("*Nset, nset=N_RP")
    inp_lines.append(f"{rp_nid}")
    
    inp_lines.append("*Nset, nset=N_TOP")
    for i in range(0, len(top_nodes), 12):
        inp_lines.append(", ".join(str(n) for n in top_nodes[i:i+12]))
        
    inp_lines.append("*Nset, nset=N_BOTTOM")
    for i in range(0, len(bot_nodes), 12):
        inp_lines.append(", ".join(str(n) for n in bot_nodes[i:i+12]))
        
    inp_lines.append("** ==========================================================")
    inp_lines.append("** UEL PROPERTIES (Clean 6-slot ABI)")
    inp_lines.append("** ==========================================================")
    inp_lines.append("*UEL Property, elset=PHASE_QUAD")
    inp_lines.append(f" 0.015, 0.0027, 210.0, 0.3, 1.0e-7, {n_phys}.0")
    inp_lines.append("*UEL Property, elset=DISP_QUAD")
    inp_lines.append(f" 0.015, 0.0027, 210.0, 0.3, 1.0e-7, {n_phys}.0")
    
    inp_lines.append("** ==========================================================")
    inp_lines.append("** PASSIVE MATERIAL FOR VISUALIZATION LAYER")
    inp_lines.append("** ==========================================================")
    inp_lines.append("*Solid Section, elset=VIS_QUAD, material=MAT_PASSIVE")
    inp_lines.append(" 1.0,")
    inp_lines.append("*Material, name=MAT_PASSIVE")
    inp_lines.append("*Elastic")
    inp_lines.append(" 1.0e-11, 0.3")
    inp_lines.append("*User Defined Field")
    inp_lines.append("*Depvar")
    inp_lines.append(" 18")
    
    inp_lines.append("** ==========================================================")
    inp_lines.append("** EQUATIONS (Mode-II pure shear constraint: individual top ties)")
    inp_lines.append("** ==========================================================")
    for nid in top_nodes:
        inp_lines.append("*Equation")
        inp_lines.append("2")
        inp_lines.append(f"{nid}, 1, 1.0, {rp_nid}, 1, -1.0")
    
    inp_lines.append("** ==========================================================")
    inp_lines.append("** STEP: Monotonic Shear Loading to U1 = 0.050000 mm")
    inp_lines.append("** ==========================================================")
    inp_lines.append("*Step, name=ShearStep, nlgeom=NO, inc=20000")
    inp_lines.append("*Static")
    inp_lines.append(" 1.0E-5, 0.050000, 1.0E-9, 0.0005")
    inp_lines.append("*Boundary")
    inp_lines.append(" N_BOTTOM, 1, 2, 0.0")
    inp_lines.append(" N_RP, 1, 1, 0.050000")
    inp_lines.append(" N_RP, 2, 2, 0.0")
    inp_lines.append("*Restart, write, frequency=0")
    inp_lines.append("*Output, field, frequency=1")
    inp_lines.append("*Node Output, nset=N_RP")
    inp_lines.append(" U, RF")
    inp_lines.append("*Node Output, nset=N_TOP")
    inp_lines.append(" U, RF")
    inp_lines.append("*Node Output, nset=N_BOTTOM")
    inp_lines.append(" U, RF")
    inp_lines.append("*Element Output, elset=DISP_QUAD")
    inp_lines.append(" SDV")
    inp_lines.append("*Node Print, freq=1, nset=N_RP")
    inp_lines.append(" U1, U2, RF1, RF2")
    inp_lines.append("*Node Print, freq=1, nset=N_BOTTOM")
    inp_lines.append(" RF1, RF2")
    inp_lines.append("*El Print, freq=1, elset=DISP_QUAD")
    inp_lines.append(" SDV13, SDV14, SDV15, SDV16")
    inp_lines.append("*End Step")
    
    inp_path = OUT_DIR / f"{job_name}.inp"
    with open(inp_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(inp_lines) + "\n")
    print(f"Generated INP deck: {inp_path.name} ({inp_path.stat().st_size / 1e6:.2f} MB)")
    
    # 3. UEL Subroutine
    uel_text = AUTH_FOR.read_text(encoding="utf-8")
    uel_path = OUT_DIR / "f42_mixed_uel.for"
    with open(uel_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(uel_text)
        
    # 4. Notifications & PBS Launcher
    notif_path = OUT_DIR / "job_notifications.sh"
    with open(notif_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(NOTIF_SH.read_text(encoding="utf-8").replace("\r\n", "\n"))
        
    pbs_content = f"""#PBS -N M2PK10R3_REFTIP
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

cd $PBS_O_WORKDIR
source $HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh
notification_install_terminal_trap

module load intel/2024.2.0
module load abaqus/2023

abaqus job={job_name} user=f42_mixed_uel.for
"""
    pbs_path = OUT_DIR / "submit_job.pbs"
    with open(pbs_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(pbs_content)
        
    # 5. Manifest
    inp_sha = sha256_file(inp_path)
    uel_sha = sha256_file(uel_path)
    pbs_sha = sha256_file(pbs_path)
    notif_sha = sha256_file(notif_path)
    
    manifest = {
        "candidate": job_name,
        "classification": "stage_f_mode_ii_pk10r3_refined_tip_candidate",
        "nphys_elements": n_phys,
        "physical_nodes": len(nodes),
        "min_h": min_h,
        "max_h": max_h,
        "h_over_l0_min": min_h / 0.015,
        "has_physical_slit": True,
        "slit_duplicate_node_pairs": len(slit_nodes) // 2,
        "resources": "1 CPU / 16 GB / 24:00:00 / entry_imfdfkmq / Abaqus 2023",
        "inp_sha256": inp_sha,
        "uel_sha256": uel_sha,
        "pbs_sha256": pbs_sha,
        "notif_sha256": notif_sha
    }
    
    manifest_path = OUT_DIR / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=2)
    manifest_sha = sha256_file(manifest_path)
    print(f"Manifest SHA256: {manifest_sha}")
    
    return {
        "job_name": job_name,
        "n_phys": n_phys,
        "n_nodes": len(nodes),
        "min_h": min_h,
        "max_h": max_h,
        "h_over_l0_min": min_h / 0.015,
        "inp_sha256": inp_sha,
        "uel_sha256": uel_sha,
        "pbs_sha256": pbs_sha,
        "manifest_sha256": manifest_sha,
        "total_area": total_area,
        "aspect_ratio_max": max(aspect_ratios),
        "aspect_ratio_median": statistics.median(aspect_ratios)
    }

if __name__ == "__main__":
    res = generate_candidate_package()
    print("\nCandidate package generation complete:")
    print(json.dumps(res, indent=2))
