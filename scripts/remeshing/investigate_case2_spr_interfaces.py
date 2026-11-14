# -*- coding: utf-8 -*-
"""
investigate_case2_spr_interfaces.py
===================================
Targeted Investigation for Finding F1730-R01:
Evaluates whether Abaqus Superconvergent Patch Recovery (SPR) error indicator (MISESERI)
exhibits artificial peaks/discontinuities correlated with the 13 material-section interfaces,
or reflects authentic physical strain/damage localization.

Analyzes:
1. Element topology, material assignments, and elastic moduli from PK_HOLE_COMPANION_RECOVERY.inp.
2. Dual-element edge adjacency graph across all 2,906 elements.
3. Identification of all inter-bin interface boundaries and modulus jump ratios E1 / E2.
4. Spatial correlation between MISESERI and material interface proximity vs damage d.
5. Partitioned statistics for:
   - 37-element primary damage component
   - 48 actively softening elements (d >= 0.10)
   - 6 hole-boundary-touching elements
   - Inter-bin interface elements (within damage zone and at bulk boundary)
   - Homogeneous intact bulk elements
6. Assessment of Abaqus SPR section homogeneity requirements and minimal corrective implementation.

Outputs:
  results/validation/f1730_case2_spr_interface_investigation.json
"""

import os
import sys
import json
import math
import collections

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INP_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "221_f1730_case2_recovery_solve", "PK_HOLE_COMPANION_RECOVERY.inp")
TELEMETRY_PATH = os.path.join(REPO_ROOT, "results", "validation", "f1730_case2_recovery_evidence", "f1730_case2_recovery_telemetry.json")
DAMAGE_CONN_PATH = os.path.join(REPO_ROOT, "results", "validation", "f1728_case2_damage_connectivity.json")
OUTPUT_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1730_case2_spr_interface_investigation.json")

def parse_inp_sections(inp_path):
    elements = {} # eid -> list of node IDs
    nodes = {} # nid -> (x, y)
    elsets = collections.defaultdict(list) # elset_name -> list of eids
    materials = {} # mat_name -> E
    section_materials = {} # elset_name -> mat_name
    
    current_section = None
    current_elset = None
    
    with open(inp_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
        
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("**"):
            i += 1
            continue
            
        if line.startswith("*NODE"):
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("*"):
                parts = [p.strip() for p in lines[i].strip().split(",")]
                if len(parts) >= 3:
                    nid = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    nodes[nid] = (x, y)
                i += 1
            continue
            
        elif line.startswith("*ELEMENT,") or line.startswith("*ELEMENT\n"):
            # e.g. *ELEMENT, TYPE=CPE4, ELSET=QUADS
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("*"):
                parts = [p.strip() for p in lines[i].strip().split(",")]
                if len(parts) >= 4:
                    eid = int(parts[0])
                    nids = [int(p) for p in parts[1:] if p]
                    elements[eid] = nids
                i += 1
            continue
            
        elif line.startswith("*ELSET"):
            # e.g. *ELSET, ELSET=ELSET_BIN_INTACT
            elset_name = None
            for p in line.split(","):
                if "ELSET=" in p.upper():
                    elset_name = p.split("=")[1].strip()
            i += 1
            if elset_name:
                while i < len(lines) and not lines[i].strip().startswith("*"):
                    raw = lines[i].strip()
                    if raw:
                        parts = [int(p.strip()) for p in raw.split(",") if p.strip().isdigit()]
                        elsets[elset_name].extend(parts)
                    i += 1
            continue
            
        elif line.startswith("*SOLID SECTION"):
            # e.g. *SOLID SECTION, ELSET=ELSET_BIN_INTACT, MATERIAL=MAT_BIN_INTACT
            elset_n = None
            mat_n = None
            for p in line.split(","):
                if "ELSET=" in p.upper():
                    elset_n = p.split("=")[1].strip()
                elif "MATERIAL=" in p.upper():
                    mat_n = p.split("=")[1].strip()
            if elset_n and mat_n:
                section_materials[elset_n] = mat_n
            i += 1
            continue
            
        elif line.startswith("*MATERIAL"):
            mat_name = None
            for p in line.split(","):
                if "NAME=" in p.upper():
                    mat_name = p.split("=")[1].strip()
            i += 1
            # Next line might be *ELASTIC
            while i < len(lines) and lines[i].strip().startswith("*"):
                if lines[i].strip().startswith("*ELASTIC"):
                    i += 1
                    parts = [p.strip() for p in lines[i].strip().split(",")]
                    if len(parts) >= 2 and mat_name:
                        materials[mat_name] = float(parts[0])
                    i += 1
                    break
                else:
                    i += 1
            continue
        else:
            i += 1
            
    # Map element -> (elset, material, E)
    elem_mat = {}
    for elset_n, eids in elsets.items():
        if elset_n in section_materials:
            mat_n = section_materials[elset_n]
            modulus = materials.get(mat_n, 210000.0)
            for eid in eids:
                elem_mat[eid] = {
                    "elset": elset_n,
                    "material": mat_n,
                    "E": modulus
                }
                
    return elements, nodes, elem_mat

def build_mesh_topology(elements):
    # Map edge (sorted pair of node IDs) -> list of element IDs
    edge_to_elems = collections.defaultdict(list)
    for eid, nids in elements.items():
        n = len(nids)
        for j in range(n):
            n1 = nids[j]
            n2 = nids[(j + 1) % n]
            edge = tuple(sorted([n1, n2]))
            edge_to_elems[edge].append(eid)
            
    # Build element adjacency: eid -> set of neighbour eids sharing an edge
    elem_neighbors = collections.defaultdict(set)
    for edge, eids in edge_to_elems.items():
        if len(eids) == 2:
            e1, e2 = eids
            elem_neighbors[e1].add(e2)
            elem_neighbors[e2].add(e1)
            
    return edge_to_elems, elem_neighbors

def main():
    print("=== TASK F1730: INVESTIGATION OF SPR RECOVERY DOMAIN & MATERIAL INTERFACES ===")
    
    if not os.path.isfile(INP_PATH):
        print("ERROR: INP not found: %s" % INP_PATH)
        sys.exit(1)
    if not os.path.isfile(TELEMETRY_PATH):
        print("ERROR: Telemetry JSON not found: %s" % TELEMETRY_PATH)
        sys.exit(1)
        
    elements, nodes, elem_mat = parse_inp_sections(INP_PATH)
    print("Parsed %d elements, %d nodes, %d material assignments." % (len(elements), len(nodes), len(elem_mat)))
    
    edge_to_elems, elem_neighbors = build_mesh_topology(elements)
    print("Constructed mesh topology: %d internal/boundary edges." % len(edge_to_elems))
    
    # Load Telemetry
    with open(TELEMETRY_PATH, "r", encoding="utf-8-sig") as f:
        telemetry = json.load(f)
        
    elem_miseseri = {int(k): float(v) for k, v in telemetry["elementwise_data"]["elem_miseseri"].items()}
    elem_misesavg = {int(k): float(v) for k, v in telemetry["elementwise_data"]["elem_misesavg"].items()}
    
    # Load Damage Connectivity
    with open(DAMAGE_CONN_PATH, "r", encoding="utf-8-sig") as f:
        dmg_data = json.load(f)
        
    el_summary = dmg_data["elements_summary"]
    dmg_dict = {e["element_id"]: e for e in el_summary}
    
    # Specific Subsets
    damaged_eids = set([e["element_id"] for e in el_summary]) # 48 elements
    primary_comp_eids = set(dmg_data["edge_components"][0]["elements"]) # 37 elements
    boundary_ligament_eids = set([151, 152, 153, 687, 734, 1088]) # 6 boundary elements
    
    # Identify inter-bin interface elements
    interface_elements = {}
    interior_elements = {}
    
    for eid, e_info in elem_mat.items():
        mat_e = e_info["material"]
        E_e = e_info["E"]
        nbrs = elem_neighbors[eid]
        
        diff_mat_nbrs = []
        max_jump_ratio = 1.0
        
        for nbr in nbrs:
            if nbr in elem_mat:
                mat_nbr = elem_mat[nbr]["material"]
                E_nbr = elem_mat[nbr]["E"]
                if mat_nbr != mat_e:
                    ratio = max(E_e, E_nbr) / min(E_e, E_nbr)
                    diff_mat_nbrs.append({
                        "neighbor_id": nbr,
                        "neighbor_mat": mat_nbr,
                        "neighbor_E": E_nbr,
                        "modulus_ratio": ratio
                    })
                    if ratio > max_jump_ratio:
                        max_jump_ratio = ratio
                        
        if diff_mat_nbrs:
            interface_elements[eid] = {
                "element_id": eid,
                "material": mat_e,
                "E": E_e,
                "is_damaged": eid in damaged_eids,
                "damage_d": dmg_dict.get(eid, {}).get("d", 0.0),
                "neighbors_count": len(nbrs),
                "diff_mat_neighbors": diff_mat_nbrs,
                "max_jump_ratio": max_jump_ratio,
                "miseseri": elem_miseseri.get(eid, 0.0),
                "misesavg": elem_misesavg.get(eid, 0.0)
            }
        else:
            interior_elements[eid] = {
                "element_id": eid,
                "material": mat_e,
                "E": E_e,
                "is_damaged": eid in damaged_eids,
                "damage_d": dmg_dict.get(eid, {}).get("d", 0.0),
                "miseseri": elem_miseseri.get(eid, 0.0),
                "misesavg": elem_misesavg.get(eid, 0.0)
            }
            
    print("Identified %d interface elements touching a different material bin." % len(interface_elements))
    print("Identified %d interior elements whose edge-neighbors all share identical section." % len(interior_elements))
    
    # Partition Analysis
    # 1. Interface elements inside the damage zone (damaged elements touching a different bin)
    dmg_interface_eids = set([eid for eid in interface_elements if eid in damaged_eids])
    dmg_interior_eids = set([eid for eid in interior_elements if eid in damaged_eids])
    
    # 2. Interface elements in the bulk (undamaged bulk elements touching an interface)
    bulk_interface_eids = set([eid for eid in interface_elements if eid not in damaged_eids])
    
    # 3. Pure homogeneous bulk (undamaged elements whose neighbors all share MAT_BIN_INTACT)
    pure_bulk_intact_eids = set([eid for eid, info in interior_elements.items() if info["material"] == "MAT_BIN_INTACT"])
    
    def compute_stats(vals):
        if not vals:
            return {"count": 0, "mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "median": 0.0}
        n = len(vals)
        mean = sum(vals) / n
        var = sum((x - mean)**2 for x in vals) / n
        std = math.sqrt(var)
        s_vals = sorted(vals)
        median = s_vals[n // 2] if n % 2 != 0 else (s_vals[n // 2 - 1] + s_vals[n // 2]) / 2.0
        return {
            "count": n,
            "mean": mean,
            "std": std,
            "min": min(vals),
            "max": max(vals),
            "median": median
        }
        
    stats_primary_comp = compute_stats([elem_miseseri[eid] for eid in primary_comp_eids])
    stats_damaged = compute_stats([elem_miseseri[eid] for eid in damaged_eids])
    stats_boundary_lig = compute_stats([elem_miseseri[eid] for eid in boundary_ligament_eids])
    stats_dmg_interface = compute_stats([elem_miseseri[eid] for eid in dmg_interface_eids])
    stats_dmg_interior = compute_stats([elem_miseseri[eid] for eid in dmg_interior_eids])
    stats_bulk_interface = compute_stats([elem_miseseri[eid] for eid in bulk_interface_eids])
    stats_pure_intact_bulk = compute_stats([elem_miseseri[eid] for eid in pure_bulk_intact_eids])
    stats_all_bulk = compute_stats([elem_miseseri[eid] for eid in elem_miseseri if eid not in damaged_eids])
    
    print("\n=== Partitioned MISESERI Statistics (MPa) ===")
    print("1. Primary Damage Component (N=%d):       mean=%.2f, max=%.2f, median=%.2f" % 
          (stats_primary_comp["count"], stats_primary_comp["mean"], stats_primary_comp["max"], stats_primary_comp["median"]))
    print("2. All 48 Damaged Elements (N=%d):        mean=%.2f, max=%.2f, median=%.2f" % 
          (stats_damaged["count"], stats_damaged["mean"], stats_damaged["max"], stats_damaged["median"]))
    print("3. Hole Boundary Ligament (N=%d):         mean=%.2f, max=%.2f, median=%.2f" % 
          (stats_boundary_lig["count"], stats_boundary_lig["mean"], stats_boundary_lig["max"], stats_boundary_lig["median"]))
    print("4. Damaged Zone Inter-Bin Elements (N=%d): mean=%.2f, max=%.2f, median=%.2f" % 
          (stats_dmg_interface["count"], stats_dmg_interface["mean"], stats_dmg_interface["max"], stats_dmg_interface["median"]))
    print("5. Damaged Zone Interior Elements (N=%d):  mean=%.2f, max=%.2f, median=%.2f" % 
          (stats_dmg_interior["count"], stats_dmg_interior["mean"], stats_dmg_interior["max"], stats_dmg_interior["median"]))
    print("6. Bulk Interface Elements (N=%d):         mean=%.2f, max=%.2f, median=%.2f" % 
          (stats_bulk_interface["count"], stats_bulk_interface["mean"], stats_bulk_interface["max"], stats_bulk_interface["median"]))
    print("7. Pure Homogeneous Intact Bulk (N=%d):   mean=%.2f, max=%.2f, median=%.2f" % 
          (stats_pure_intact_bulk["count"], stats_pure_intact_bulk["mean"], stats_pure_intact_bulk["max"], stats_pure_intact_bulk["median"]))
    print("8. Entire Undamaged Bulk (N=%d):           mean=%.2f, max=%.2f, median=%.2f" % 
          (stats_all_bulk["count"], stats_all_bulk["mean"], stats_all_bulk["max"], stats_all_bulk["median"]))
          
    # Correlation Analysis:
    # Does MISESERI correlate with modulus jump ratio, or does it correlate with damage d?
    # For damaged elements:
    dmg_jump_ratios = [interface_elements[eid]["max_jump_ratio"] for eid in dmg_interface_eids]
    dmg_miseseri_vals = [interface_elements[eid]["miseseri"] for eid in dmg_interface_eids]
    dmg_d_vals = [interface_elements[eid]["damage_d"] for eid in dmg_interface_eids]
    
    # For bulk interface elements:
    bulk_jump_ratios = [interface_elements[eid]["max_jump_ratio"] for eid in bulk_interface_eids]
    bulk_miseseri_vals = [interface_elements[eid]["miseseri"] for eid in bulk_interface_eids]
    
    def pearson_r(x, y):
        if len(x) < 2: return 0.0
        mx = sum(x) / len(x)
        my = sum(y) / len(y)
        cov = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
        varx = sum((xi - mx)**2 for xi in x)
        vary = sum((yi - my)**2 for yi in y)
        if varx == 0.0 or vary == 0.0: return 0.0
        return cov / math.sqrt(varx * vary)
        
    r_miseseri_vs_d = pearson_r([elem_miseseri[eid] for eid in damaged_eids], [dmg_dict[eid]["d"] for eid in damaged_eids])
    r_miseseri_vs_jump = pearson_r(dmg_jump_ratios, dmg_miseseri_vals) if dmg_jump_ratios else 0.0
    r_bulk_miseseri_vs_jump = pearson_r(bulk_jump_ratios, bulk_miseseri_vals) if bulk_jump_ratios else 0.0
    
    print("\n=== Correlation Coefficients ===")
    print("Pearson r(MISESERI, damage d) across damaged elements:      %.4f" % r_miseseri_vs_d)
    print("Pearson r(MISESERI, modulus jump) across damaged interfaces: %.4f" % r_miseseri_vs_jump)
    print("Pearson r(MISESERI, modulus jump) across bulk interfaces:    %.4f" % r_bulk_miseseri_vs_jump)
    
    # Physical vs Artifact Analysis
    # Does the bulk interface experience an artificial error spike?
    # Bulk interface mean vs pure intact bulk mean:
    bulk_interface_ratio = stats_bulk_interface["mean"] / max(stats_pure_intact_bulk["mean"], 1e-12)
    print("\n=== Interface Artifact Assessment ===")
    print("Bulk Interface Mean (%.2f MPa) vs Pure Intact Bulk Mean (%.2f MPa): Ratio = %.2fx" % 
          (stats_bulk_interface["mean"], stats_pure_intact_bulk["mean"], bulk_interface_ratio))
    print("Damaged Zone Mean (%.2f MPa) vs Bulk Interface Mean (%.2f MPa):      Ratio = %.2fx" % 
          (stats_damaged["mean"], stats_bulk_interface["mean"], stats_damaged["mean"] / max(stats_bulk_interface["mean"], 1e-12)))
          
    # 4. Prospective crack-to-hole ligament elements (geometric corridor between (0.5, 0.5) and (0.65, 0.65))
    # Distance from centroid to line connecting (0.5, 0.5) to (0.5793, 0.5793) or (0.55, 0.65)
    # Check elements in bounding box [0.50, 0.65] x [0.50, 0.65] with d < 0.10
    ligament_uncracked_eids = set()
    for eid, nids in elements.items():
        if eid not in damaged_eids:
            xs = [nodes[n][0] for n in nids]
            ys = [nodes[n][1] for n in nids]
            cx = sum(xs) / len(xs)
            cy = sum(ys) / len(ys)
            if 0.48 <= cx <= 0.66 and 0.48 <= cy <= 0.66:
                dist_to_center = math.sqrt((cx - 0.65)**2 + (cy - 0.65)**2)
                if dist_to_center > 0.095: # outside hole
                    ligament_uncracked_eids.add(eid)
                    
    stats_ligament_uncracked = compute_stats([elem_miseseri[eid] for eid in ligament_uncracked_eids])
    print("9. Uncracked Ligament Corridor (N=%d):     mean=%.2f, max=%.2f, median=%.2f" % 
          (stats_ligament_uncracked["count"], stats_ligament_uncracked["mean"], stats_ligament_uncracked["max"], stats_ligament_uncracked["median"]))
    investigation_summary = {
        "task_id": "F1730-CASE2-SPR-DOMAIN-INVESTIGATION",
        "benchmark": "Case 2 (Single Off-Axis Hole Plate)",
        "finding_addressed": "F1730-R01",
        "mesh_inventory": {
            "total_elements": len(elements),
            "total_nodes": len(nodes),
            "interface_elements_count": len(interface_elements),
            "interior_elements_count": len(interior_elements),
            "total_material_sections": 13
        },
        "statistics": {
            "primary_damage_component": stats_primary_comp,
            "all_damaged_elements": stats_damaged,
            "hole_boundary_ligament": stats_boundary_lig,
            "damaged_zone_interface_elements": stats_dmg_interface,
            "damaged_zone_interior_elements": stats_dmg_interior,
            "bulk_interface_elements": stats_bulk_interface,
            "pure_homogeneous_intact_bulk": stats_pure_intact_bulk,
            "uncracked_ligament_corridor": stats_ligament_uncracked,
            "all_bulk_elements": stats_all_bulk
        },
        "correlations": {
            "r_miseseri_vs_damage_d": r_miseseri_vs_d,
            "r_miseseri_vs_modulus_jump_damaged": r_miseseri_vs_jump,
            "r_miseseri_vs_modulus_jump_bulk": r_bulk_miseseri_vs_jump
        },
        "assessment": {
            "physical_localization_confirmed": (stats_damaged["mean"] > 10.0 * stats_pure_intact_bulk["mean"]),
            "bulk_interface_artifact_negligible": (stats_bulk_interface["mean"] < 2.0 * stats_pure_intact_bulk["mean"]),
            "spr_section_homogeneity_finding": "Detailed in investigation report"
        }
    }
    
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(investigation_summary, f, indent=2)
    print("\nSaved investigation summary to: %s" % OUTPUT_JSON)

if __name__ == "__main__":
    main()
