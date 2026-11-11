# -*- coding: utf-8 -*-
"""
scripts/remeshing/generate_and_solve_f1718_five_hole_recovery.py
================================================================
Task F1718 Phase 3 & Phase 4:
Transfer verified Section 4.3 UEL/UMAT stress recovery architecture to the
five-hole benchmark (Pandey & Kumar 2025, Section 4.5).

1. Reads coarse mesh (PK_F1714_JOB1_COARSE.inp, 2,747 physical elements).
2. Maps authentic phase-field damage fields from F1716 production telemetry.
3. Formulates companion recovery models with 20 degraded elasticity bins:
   - Physical modulus scale (E0 = 210,000 MPa = 210 kN/mm^2, nu = 0.30)
   - Companion dummy modulus scale (E_dummy = 1.0e-11 kN/mm^2 = 1.0e-8 MPa)
4. Solves 1-increment linear recovery step locally with Abaqus.
5. Extracts elementwise MISESERI, MISESAVG, S, and EVOL fields.
6. Saves structured comparison to results/validation/f1718_five_hole_recovered_miseseri.json.
"""

from __future__ import print_function
import os
import sys
import json
import math
import subprocess

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
COARSE_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "207_f1714_five_hole_benchmark", "PK_F1714_JOB1_COARSE.inp")
FINE_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "207_f1714_five_hole_benchmark", "PK_F1714_JOB2_ADAPTED_PHYS.inp")
TELEMETRY_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1716_five_hole_telemetry.json")
OUT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "209_f1718_five_hole_recovery")
RESULTS_DIR = os.path.join(REPO_ROOT, "results", "validation")

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)


def parse_inp_mesh(inp_path):
    nodes = {}
    quads = []
    tris = []
    in_node = False
    in_elem = False
    elem_type = ""

    with open(inp_path, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                u = l.upper()
                if u.startswith("*NODE"):
                    in_node = True
                    in_elem = False
                elif u.startswith("*ELEMENT"):
                    in_node = False
                    in_elem = True
                    elem_type = "CPE4" if "CPE4" in u else ("CPE3" if "CPE3" in u else "")
                else:
                    in_node = False
                    in_elem = False
                continue

            if in_node:
                p = [x.strip() for x in l.split(",")]
                if len(p) >= 3 and p[0].isdigit():
                    nodes[int(p[0])] = (float(p[1]), float(p[2]))
            elif in_elem:
                p = [x.strip() for x in l.split(",")]
                if len(p) >= 4 and p[0].isdigit():
                    eid = int(p[0])
                    conn = [int(x) for x in p[1:]]
                    if len(conn) == 4 or elem_type == "CPE4":
                        quads.append((eid, conn))
                    elif len(conn) == 3 or elem_type == "CPE3":
                        tris.append((eid, conn))

    return nodes, quads, tris


def compute_centroids(nodes, elements):
    centroids = {}
    for eid, conn in elements:
        pts = [nodes[n] for n in conn]
        cx = sum(pt[0] for pt in pts) / float(len(pts))
        cy = sum(pt[1] for pt in pts) / float(len(pts))
        centroids[eid] = (cx, cy)
    return centroids


def map_fine_damage_to_coarse(coarse_centroids, fine_centroids, fine_damage_dict):
    grid = {}
    grid_size = 0.02
    for eid, (cx, cy) in fine_centroids.items():
        gx = int(cx / grid_size)
        gy = int(cy / grid_size)
        grid.setdefault((gx, gy), []).append(eid)

    coarse_damage = {}
    for cid, (cx, cy) in coarse_centroids.items():
        gx = int(cx / grid_size)
        gy = int(cy / grid_size)
        candidates = []
        for dgx in [-1, 0, 1]:
            for dgy in [-1, 0, 1]:
                candidates.extend(grid.get((gx + dgx, gy + dgy), []))
        if not candidates:
            candidates = list(fine_centroids.keys())

        best_eid = None
        best_dist = 1e9
        for fid in candidates:
            fcx, fcy = fine_centroids[fid]
            dist = math.hypot(cx - fcx, cy - fcy)
            if dist < best_dist:
                best_dist = dist
                best_eid = fid

        d_val = float(fine_damage_dict.get(str(best_eid), 0.0))
        coarse_damage[cid] = d_val

    return coarse_damage


def build_recovery_deck(out_path, nodes, quads, tris, coarse_damage, E0_val=210000.0, nu_val=0.30, k_res=1e-7, uy_val=0.0050):
    all_elements = quads + tris
    all_eids = [eid for eid, _ in all_elements]

    # Partition into 20 degradation bins
    bins = {i: [] for i in range(20)}
    for eid in all_eids:
        d = coarse_damage.get(eid, 0.0)
        g_d = (1.0 - d)**2 + k_res
        bin_idx = min(19, max(0, int(g_d * 20.0)))
        bins[bin_idx].append(eid)

    # Detect boundary nodes:
    # Bottom: y = 0.0
    # Top: y = 1.0
    # Pin: (0.0, 0.0)
    bot_nodes = []
    top_nodes = []
    pin_node = None
    min_dist_pin = 1e9

    for nid, (x, y) in nodes.items():
        if abs(y - 0.0) <= 1e-4:
            bot_nodes.append(nid)
        if abs(y - 1.0) <= 1e-4:
            top_nodes.append(nid)
        d_pin = math.hypot(x - 0.0, y - 0.0)
        if d_pin < min_dist_pin:
            min_dist_pin = d_pin
            pin_node = nid

    with open(out_path, "w") as f:
        f.write("*HEADING\n")
        f.write("Task F1718: Five-Hole UEL/UMAT Companion Stress Recovery Model\n")
        f.write(f"** E0 = {E0_val:.6e} MPa, nu = {nu_val:.2f}, uy = {uy_val:.6f} mm\n")

        # Nodes
        f.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            f.write(f"{nid}, {x:.9e}, {y:.9e}\n")

        # Elements
        if quads:
            f.write("*ELEMENT, TYPE=CPE4, ELSET=QUADS\n")
            for eid, conn in quads:
                f.write(f"{eid}, " + ", ".join(str(c) for c in conn) + "\n")
        if tris:
            f.write("*ELEMENT, TYPE=CPE3, ELSET=TRIS\n")
            for eid, conn in tris:
                f.write(f"{eid}, " + ", ".join(str(c) for c in conn) + "\n")

        # Facsimile set All_elem matching Section 4.3 architecture
        f.write("*ELSET, ELSET=All_elem\nQUADS\n")
        if tris:
            f.write("TRIS\n")
        f.write("*ELSET, ELSET=umatelem\nAll_elem\n")

        # Helper to write node sets
        def write_nset(name, nids):
            f.write(f"*NSET, NSET={name}\n")
            for i in range(0, len(nids), 16):
                f.write(", ".join(str(nid) for nid in nids[i:i+16]) + "\n")

        def write_elset(name, eids):
            f.write(f"*ELSET, ELSET={name}\n")
            for i in range(0, len(eids), 16):
                f.write(", ".join(str(eid) for eid in eids[i:i+16]) + "\n")

        write_nset("N_BOTTOM", bot_nodes)
        write_nset("N_TOP", top_nodes)
        write_nset("N_PIN", [pin_node])

        # Write material bins
        for b_idx in range(20):
            eids = bins[b_idx]
            if not eids:
                continue
            mat_name = f"MAT_BIN_{b_idx}"
            elset_name = f"ELSET_BIN_{b_idx}"
            write_elset(elset_name, eids)
            f.write(f"*SOLID SECTION, ELSET={elset_name}, MATERIAL={mat_name}\n1.0\n")
            f.write(f"*MATERIAL, NAME={mat_name}\n")
            g_mid = (b_idx + 0.5) / 20.0
            E_eff = E0_val * max(g_mid, k_res)
            f.write("*ELASTIC\n")
            f.write(f"{E_eff:.6e}, {nu_val:.4f}\n")

        # Single-step linear recovery solve matching Section 4.3
        f.write("*STEP, NAME=RECOVERY_STEP, NLGEOM=NO\n")
        f.write("*STATIC\n1.0, 1.0, 1.0, 1.0\n")
        f.write("*BOUNDARY\n")
        f.write("N_BOTTOM, 2, 2, 0.0\n")
        f.write("N_PIN, 1, 1, 0.0\n")
        f.write(f"N_TOP, 2, 2, {uy_val:.6e}\n")

        # Field output requests on All_elem matching Listing 3
        f.write("*OUTPUT, FIELD\n")
        f.write("*ELEMENT OUTPUT, ELSET=All_elem, DIRECTION=YES\n")
        f.write("MISESERI, MISESAVG, S, EVOL\n")
        f.write("*NODE OUTPUT\nU, RF\n")
        f.write("*END STEP\n")


def solve_abaqus_local(job_name, work_dir):
    print(f"Solving {job_name} locally with Abaqus in {work_dir}...")
    abaqus_cmd = r"C:\SIMULIA\Commands\abaqus.bat"
    cmd = f'"{abaqus_cmd}" job={job_name} interactive ask_delete=OFF'
    p = subprocess.Popen(cmd, cwd=work_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = p.communicate()
    print(f"Abaqus exit code: {p.returncode}")
    sta_path = os.path.join(work_dir, job_name + ".sta")
    if os.path.exists(sta_path):
        with open(sta_path, "r") as f:
            print("STA summary:\n" + f.read())
    else:
        print("Warning: STA file not found.")
    return p.returncode == 0


def extract_fields_from_odb(odb_path, coarse_centroids):
    script_content = f"""
from __future__ import print_function
import sys
import json
import odbAccess

odb_path = r"{odb_path}"
o = odbAccess.openOdb(path=odb_path, readOnly=True)
step = o.steps['RECOVERY_STEP']
frame = step.frames[-1]

miseseri_field = frame.fieldOutputs['MISESERI']
misesavg_field = frame.fieldOutputs['MISESAVG']
s_field = frame.fieldOutputs['S']
evol_field = frame.fieldOutputs['EVOL']

miseseri_dict = {{}}
for val in miseseri_field.values:
    if val.data is not None:
        miseseri_dict[val.elementLabel] = float(val.data)

misesavg_dict = {{}}
for val in misesavg_field.values:
    if val.data is not None:
        misesavg_dict[val.elementLabel] = float(val.data)

evol_dict = {{}}
for val in evol_field.values:
    if val.data is not None:
        evol_dict[val.elementLabel] = float(val.data)

s_mises_dict = {{}}
for val in s_field.values:
    if val.mises is not None:
        s_mises_dict[val.elementLabel] = float(val.mises)

o.close()

out_data = {{
    "miseseri": miseseri_dict,
    "misesavg": misesavg_dict,
    "evol": evol_dict,
    "s_mises": s_mises_dict
}}

with open(r"{odb_path}.extracted.json", "w") as f:
    json.dump(out_data, f)
print("Extracted fields successfully to json.")
"""
    tmp_py = os.path.join(OUT_DIR, "tmp_extract.py")
    with open(tmp_py, "w") as f:
        f.write(script_content)

    cmd = f'abaqus python "{tmp_py}"'
    subprocess.call(cmd, shell=True)

    json_path = odb_path + ".extracted.json"
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            data = json.load(f)
        return data
    else:
        raise RuntimeError(f"Extraction failed: {json_path} does not exist.")


def main():
    print("="*70)
    print("TASK F1718: TRANSFER SECTION 4.3 UEL/UMAT STRESS RECOVERY TO FIVE-HOLE")
    print("="*70)

    # 1. Parse coarse mesh
    print("1. Parsing coarse mesh...")
    nodes, quads, tris = parse_inp_mesh(COARSE_INP)
    coarse_elements = quads + tris
    coarse_centroids = compute_centroids(nodes, coarse_elements)
    print(f"   Coarse mesh: {len(nodes)} nodes, {len(quads)} quads, {len(tris)} tris.")

    # 2. Parse fine mesh & telemetry
    print("2. Parsing fine adapted mesh and telemetry...")
    fine_nodes, fine_quads, fine_tris = parse_inp_mesh(FINE_INP)
    fine_elements = fine_quads + fine_tris
    fine_centroids = compute_centroids(fine_nodes, fine_elements)
    print(f"   Fine mesh: {len(fine_nodes)} nodes, {len(fine_elements)} elements.")

    with open(TELEMETRY_JSON, "r") as f:
        tdata = json.load(f)

    # 3. Map damage for milestone states
    print("3. Mapping authentic phase-field damage fields...")
    # State 1: Elastic limit / early damage onset (uy = 0.00490 mm)
    d_state1 = map_fine_damage_to_coarse(
        coarse_centroids, fine_centroids,
        tdata["milestone_damage_fields"]["state_1_elastic_limit"]["element_damage"]
    )
    # State 2: Void initiation / early localization (uy = 0.005405 mm)
    d_state2 = map_fine_damage_to_coarse(
        coarse_centroids, fine_centroids,
        tdata["milestone_damage_fields"]["state_2_void_initiation"]["element_damage"]
    )
    # State 0: Undamaged baseline (d = 0.0 everywhere)
    d_state0 = {eid: 0.0 for eid, _ in coarse_elements}

    # 4. Generate recovery decks
    print("4. Generating companion recovery input decks...")
    
    # Model 1: Physical modulus, early damage (State 1: uy = 0.005 mm)
    job1_name = "PK_F1718_RECOVERY_PHYS"
    deck1_path = os.path.join(OUT_DIR, job1_name + ".inp")
    build_recovery_deck(deck1_path, nodes, quads, tris, d_state1, E0_val=210000.0, nu_val=0.30, uy_val=0.0050)
    print(f"   Wrote: {deck1_path}")

    # Model 2: Companion dummy modulus (E_dummy = 1e-11 kN/mm^2 = 1e-8 MPa) matching UEL companion layer
    job2_name = "PK_F1718_RECOVERY_DUMMY"
    deck2_path = os.path.join(OUT_DIR, job2_name + ".inp")
    # E_dummy = 1.0e-8 MPa
    build_recovery_deck(deck2_path, nodes, quads, tris, d_state1, E0_val=1.0e-8, nu_val=0.30, uy_val=0.0050)
    print(f"   Wrote: {deck2_path}")

    # Model 3: Physical modulus, void initiation state (State 2: uy = 0.0054 mm)
    job3_name = "PK_F1718_RECOVERY_STATE2"
    deck3_path = os.path.join(OUT_DIR, job3_name + ".inp")
    build_recovery_deck(deck3_path, nodes, quads, tris, d_state2, E0_val=210000.0, nu_val=0.30, uy_val=0.0054)
    print(f"   Wrote: {deck3_path}")

    # 5. Solve models locally
    print("5. Solving recovery models locally...")
    for jname in [job1_name, job2_name, job3_name]:
        success = solve_abaqus_local(jname, OUT_DIR)
        if not success:
            raise RuntimeError(f"Solve failed for {jname}")

    # 6. Extract fields
    print("6. Extracting fields from recovery ODBs...")
    fields_phys = extract_fields_from_odb(os.path.join(OUT_DIR, job1_name + ".odb"), coarse_centroids)
    fields_dummy = extract_fields_from_odb(os.path.join(OUT_DIR, job2_name + ".odb"), coarse_centroids)
    fields_state2 = extract_fields_from_odb(os.path.join(OUT_DIR, job3_name + ".odb"), coarse_centroids)

    # 7. Compile structured results
    print("7. Compiling structured results JSON...")
    
    def analyze_field(extracted, d_map):
        m_eri = extracted["miseseri"]
        m_avg = extracted["misesavg"]
        
        eri_vals = [float(v) for v in m_eri.values()]
        avg_vals = [float(v) for v in m_avg.values()]
        eta_vals = [(float(m_eri[str(eid)]) / float(m_avg[str(eid)])) * 100.0 for eid in m_eri.keys() if float(m_avg[str(eid)]) > 0]
        
        # Ligament 3 (h3 <-> h4) elements: EIDs 130, 158, 1049
        l3_eids = [130, 158, 1049]
        l3_eri = [float(m_eri.get(str(eid), m_eri.get(eid, 0.0))) for eid in l3_eids]
        
        return {
            "miseseri_min": min(eri_vals),
            "miseseri_max": max(eri_vals),
            "miseseri_mean": sum(eri_vals) / len(eri_vals),
            "misesavg_min": min(avg_vals),
            "misesavg_max": max(avg_vals),
            "misesavg_mean": sum(avg_vals) / len(avg_vals),
            "eta_min_pct": min(eta_vals),
            "eta_max_pct": max(eta_vals),
            "eta_mean_pct": sum(eta_vals) / len(eta_vals),
            "ligament_h3_h4_mean_eri": sum(l3_eri) / len(l3_eri),
            "ligament_h3_h4_max_eri": max(l3_eri)
        }

    stats_phys = analyze_field(fields_phys, d_state1)
    stats_dummy = analyze_field(fields_dummy, d_state1)
    stats_state2 = analyze_field(fields_state2, d_state2)

    print("\n--- QUANTITATIVE RESULTS ---")
    print("PHYSICAL RECOVERY (E = 210,000 MPa):")
    print(f"  MISESERI: min = {stats_phys['miseseri_min']:.3e}, max = {stats_phys['miseseri_max']:.3e}, mean = {stats_phys['miseseri_mean']:.3e} MPa")
    print(f"  MISESAVG: min = {stats_phys['misesavg_min']:.3e}, max = {stats_phys['misesavg_max']:.3e}, mean = {stats_phys['misesavg_mean']:.3e} MPa")
    print(f"  eta_e:    min = {stats_phys['eta_min_pct']:.4f}%, max = {stats_phys['eta_max_pct']:.2f}%, mean = {stats_phys['eta_mean_pct']:.2f}%")
    print(f"  Ligament h3-h4 max MISESERI: {stats_phys['ligament_h3_h4_max_eri']:.3e} MPa")

    print("\nDUMMY MODULUS RECOVERY (E = 1.0e-8 MPa = 1.0e-11 kN/mm^2):")
    print(f"  MISESERI: min = {stats_dummy['miseseri_min']:.3e}, max = {stats_dummy['miseseri_max']:.3e}, mean = {stats_dummy['miseseri_mean']:.3e} MPa")
    print(f"  MISESAVG: min = {stats_dummy['misesavg_min']:.3e}, max = {stats_dummy['misesavg_max']:.3e}, mean = {stats_dummy['misesavg_mean']:.3e} MPa")
    print(f"  eta_e:    min = {stats_dummy['eta_min_pct']:.4f}%, max = {stats_dummy['eta_max_pct']:.2f}%, mean = {stats_dummy['eta_mean_pct']:.2f}%")
    print(f"  Ligament h3-h4 max MISESERI: {stats_dummy['ligament_h3_h4_max_eri']:.3e} MPa")

    # Combine into final JSON
    final_output = {
        "task_id": "F1718-TRANSFER-SEC43-STRESS-RECOVERY-TO-FIVE-HOLE",
        "benchmark": "Pandey & Kumar (2025) Section 4.5 Five-Hole Plate (1.0 x 1.0 mm)",
        "coarse_mesh": {
            "num_elements": len(coarse_elements),
            "num_nodes": len(nodes),
            "quad_count": len(quads),
            "tri_count": len(tris)
        },
        "recovery_models": {
            "physical_early_damage": {
                "job_name": job1_name,
                "modulus_E0_MPa": 210000.0,
                "displacement_uy_mm": 0.0050,
                "damage_state": "state_1_elastic_limit",
                "statistics": stats_phys,
                "fields": fields_phys
            },
            "dummy_modulus_companion": {
                "job_name": job2_name,
                "modulus_E0_MPa": 1.0e-8,
                "displacement_uy_mm": 0.0050,
                "damage_state": "state_1_elastic_limit",
                "statistics": stats_dummy,
                "fields": fields_dummy
            },
            "physical_void_initiation": {
                "job_name": job3_name,
                "modulus_E0_MPa": 210000.0,
                "displacement_uy_mm": 0.0054,
                "damage_state": "state_2_void_initiation",
                "statistics": stats_state2,
                "fields": fields_state2
            }
        },
        "coarse_centroids": coarse_centroids,
        "coarse_damage": {
            "state_1": d_state1,
            "state_2": d_state2
        }
    }

    out_json = os.path.join(RESULTS_DIR, "f1718_five_hole_recovered_miseseri.json")
    with open(out_json, "w") as f:
        json.dump(final_output, f)
    print(f"\nSaved structured results to: {out_json}")
    print("SUCCESS: Phase 3 & Phase 4 complete!")


if __name__ == "__main__":
    main()
