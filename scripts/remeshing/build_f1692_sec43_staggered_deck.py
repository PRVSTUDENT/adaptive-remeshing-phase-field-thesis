import os
from pathlib import Path

repo_root = Path(r"D:\Master thesis\Adaptive remeshing")
pkg_dir = repo_root / "models/pandey_kumar_mode1/192_pk_sec43_staggered_job1"
pkg_dir.mkdir(parents=True, exist_ok=True)

phys_inp = pkg_dir / "PK_SEC43_STAGGERED_PHYS.inp"
uel_inp = pkg_dir / "PK_SEC43_STAGGERED_JOB1.inp"

# Parse physical mesh
nodes = {}
quad_elems = {}
tri_elems = {}
lower_nodes = []
upper_nodes = []
central_nodes = []

reading = None
with open(phys_inp, "r") as f:
    for line in f:
        line_clean = line.strip()
        if not line_clean or line_clean.startswith("**"):
            continue
        if line_clean.startswith("*"):
            u = line_clean.upper()
            if u.startswith("*NODE") and not any(u.startswith(k) for k in ["*NODE OUTPUT", "*NODE PRINT", "*NODE FILE"]):
                reading = "NODE"
            elif u.startswith("*ELEMENT"):
                if "CPS4" in u or "CPE4" in u or "TYPE=CPE4" in u or "TYPE=CPS4" in u:
                    reading = "ELEM_QUAD"
                elif "CPS3" in u or "CPE3" in u or "TYPE=CPE3" in u or "TYPE=CPS3" in u:
                    reading = "ELEM_TRI"
                else:
                    reading = None
            elif u.startswith("*NSET"):
                if "N_LOWER_HOLE" in u:
                    reading = "NSET_LOWER"
                elif "N_UPPER_HOLE" in u:
                    reading = "NSET_UPPER"
                elif "N_CENTRAL_HOLE" in u:
                    reading = "NSET_CENTRAL"
                else:
                    reading = None
            else:
                reading = None
            continue

        if reading == "NODE":
            parts = [p.strip() for p in line_clean.split(",") if p.strip()]
            if len(parts) >= 3 and parts[0].isdigit():
                nid = int(parts[0])
                nodes[nid] = (float(parts[1]), float(parts[2]))
        elif reading == "ELEM_QUAD":
            parts = [p.strip() for p in line_clean.split(",") if p.strip()]
            if len(parts) >= 5 and parts[0].isdigit():
                eid = int(parts[0])
                quad_elems[eid] = [int(p) for p in parts[1:5]]
        elif reading == "ELEM_TRI":
            parts = [p.strip() for p in line_clean.split(",") if p.strip()]
            if len(parts) >= 4 and parts[0].isdigit():
                eid = int(parts[0])
                tri_elems[eid] = [int(p) for p in parts[1:4]]
        elif reading == "NSET_LOWER":
            parts = [p.strip() for p in line_clean.split(",") if p.strip()]
            lower_nodes.extend([int(p) for p in parts if p.isdigit()])
        elif reading == "NSET_UPPER":
            parts = [p.strip() for p in line_clean.split(",") if p.strip()]
            upper_nodes.extend([int(p) for p in parts if p.isdigit()])
        elif reading == "NSET_CENTRAL":
            parts = [p.strip() for p in line_clean.split(",") if p.strip()]
            central_nodes.extend([int(p) for p in parts if p.isdigit()])

num_phys_elems = len(quad_elems) + len(tri_elems)
num_nodes = len(nodes)
rp_nid = max(nodes.keys()) + 1

# If sets were not explicitly named in phys_inp, detect boundary holes geometrically
if not lower_nodes:
    for nid, (x, y) in nodes.items():
        if ((x - 20.0)**2 + (y - 20.0)**2) <= (5.05**2):
            lower_nodes.append(nid)
if not upper_nodes:
    for nid, (x, y) in nodes.items():
        if ((x - 20.0)**2 + (y - 100.0)**2) <= (5.05**2):
            upper_nodes.append(nid)
if not central_nodes:
    for nid, (x, y) in nodes.items():
        if ((x - 36.5)**2 + (y - 51.0)**2) <= (10.05**2):
            central_nodes.append(nid)

lower_nodes = sorted(list(set(lower_nodes)))
upper_nodes = sorted(list(set(upper_nodes)))
central_nodes = sorted(list(set(central_nodes)))

def write_formatted_nset(f, name, nlist):
    f.write(f"*NSET, NSET={name}\n")
    for i in range(0, len(nlist), 16):
        chunk = nlist[i:i+16]
        f.write(", ".join(str(n) for n in chunk) + "\n")

# Model parameters
E_mod = 210.0       # kN/mm^2 (210 GPa)
nu = 0.30
l0 = 0.2850         # mm
Gc = 0.00228        # kN/mm (2.28 N/mm)
k_res = 1.0e-7
num_phys_f = float(num_phys_elems)

with open(uel_inp, "w") as f:
    f.write("*HEADING\n")
    f.write("** Production Deck: PK_SEC43_STAGGERED_JOB1 (Pandey-Kumar 2025 Section 4.3 Staggered Control)\n")
    f.write(f"** Total physical elements: {num_phys_elems} ({len(quad_elems)} quads, {len(tri_elems)} tris), Nodes: {num_nodes}\n")
    f.write(f"** Total 3-layer elements: {3 * num_phys_elems} (Layer1 UEL Phase, Layer2 UEL Disp, Layer3 UMAT Companion)\n")
    f.write(f"** Parameters: E={E_mod:.1f} GPa, nu={nu:.2f}, l0={l0:.4f} mm, Gc={Gc:.5f} kN/mm, k={k_res:.1e}\n")
    f.write("** Subroutine: f42_staggered_variant_uel.for (Staggered Operator Split / Molnar & Gravouil 2017)\n")
    f.write("** Increment Scheme: *STATIC, DIRECT (Exact un-cutback single-iteration operator split)\n")
    f.write("** ----------------------------------------------------------\n")

    # UEL Interface Definitions
    f.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
    f.write("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")
    if tri_elems:
        f.write("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
        f.write("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")

    # Nodal Coordinates
    f.write("*NODE\n")
    for nid in sorted(nodes.keys()):
        x, y = nodes[nid]
        f.write(f"{nid}, {x:.9e}, {y:.9e}\n")
    f.write(f"{rp_nid}, 2.000000000e+01, 1.000000000e+02\n")

    # Layer 1: Phase field elements (Active DOF 3)
    if quad_elems:
        f.write("*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD\n")
        for eid in sorted(quad_elems.keys()):
            f.write(f"{eid}, " + ", ".join(str(n) for n in quad_elems[eid]) + "\n")
    if tri_elems:
        f.write("*ELEMENT, TYPE=U3, ELSET=PHASE_TRI\n")
        for eid in sorted(tri_elems.keys()):
            f.write(f"{eid}, " + ", ".join(str(n) for n in tri_elems[eid]) + "\n")

    # Layer 2: Mechanical displacement elements (Active DOFs 1, 2)
    offset_disp = num_phys_elems
    if quad_elems:
        f.write("*ELEMENT, TYPE=U2, ELSET=DISP_QUAD\n")
        for eid in sorted(quad_elems.keys()):
            f.write(f"{eid + offset_disp}, " + ", ".join(str(n) for n in quad_elems[eid]) + "\n")
    if tri_elems:
        f.write("*ELEMENT, TYPE=U4, ELSET=DISP_TRI\n")
        for eid in sorted(tri_elems.keys()):
            f.write(f"{eid + offset_disp}, " + ", ".join(str(n) for n in tri_elems[eid]) + "\n")

    # Layer 3: Companion UMAT elements (CPE4 / CPE3)
    offset_umat = 2 * num_phys_elems
    if quad_elems:
        f.write("*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS\n")
        for eid in sorted(quad_elems.keys()):
            f.write(f"{eid + offset_umat}, " + ", ".join(str(n) for n in quad_elems[eid]) + "\n")
    if tri_elems:
        f.write("*ELEMENT, TYPE=CPE3, ELSET=UMAT_TRIS\n")
        for eid in sorted(tri_elems.keys()):
            f.write(f"{eid + offset_umat}, " + ", ".join(str(n) for n in tri_elems[eid]) + "\n")

    # Element Sets
    f.write("*ELSET, ELSET=All_elem\nUMAT_QUADS\n")
    if tri_elems:
        f.write("UMAT_TRIS\n")
    f.write("*ELSET, ELSET=umatelem\nAll_elem\n")

    # Node Sets
    write_formatted_nset(f, "N_LOWER_HOLE", lower_nodes)
    write_formatted_nset(f, "N_UPPER_HOLE", upper_nodes)
    write_formatted_nset(f, "N_CENTRAL_HOLE", central_nodes)
    f.write(f"*NSET, NSET=N_RP\n{rp_nid}\n")

    # UEL Property Cards
    if quad_elems:
        f.write("*UEL PROPERTY, ELSET=PHASE_QUAD\n")
        f.write(f"{l0:.4f}, {Gc:.6f}, {E_mod:.1f}, {nu:.2f}, {k_res:.1e}, {num_phys_f:.1f}\n")
        f.write("*UEL PROPERTY, ELSET=DISP_QUAD\n")
        f.write(f"{l0:.4f}, {Gc:.6f}, {E_mod:.1f}, {nu:.2f}, {k_res:.1e}, {num_phys_f:.1f}\n")
    if tri_elems:
        f.write("*UEL PROPERTY, ELSET=PHASE_TRI\n")
        f.write(f"{l0:.4f}, {Gc:.6f}, {E_mod:.1f}, {nu:.2f}, {k_res:.1e}, {num_phys_f:.1f}\n")
        f.write("*UEL PROPERTY, ELSET=DISP_TRI\n")
        f.write(f"{l0:.4f}, {Gc:.6f}, {E_mod:.1f}, {nu:.2f}, {k_res:.1e}, {num_phys_f:.1f}\n")

    # Companion Material
    f.write("*SOLID SECTION, ELSET=All_elem, MATERIAL=DUMMY_MAT\n1.0\n")
    f.write("*MATERIAL, NAME=DUMMY_MAT\n")
    f.write("*USER MATERIAL, CONSTANTS=3\n")
    f.write(f"{E_mod:.1f}, {nu:.2f}, {num_phys_f:.1f}\n")
    f.write("*DEPVAR\n20\n")

    # Rigid Kinematic Equations: Upper hole tied to RP in DOF 2
    f.write("** ----------------------------------------------------------\n")
    f.write("** EQUATIONS (Rigid tensile pull of upper hole pin tied to RP in DOF 2)\n")
    f.write("** ----------------------------------------------------------\n")
    for nid in upper_nodes:
        f.write("*EQUATION\n2\n")
        f.write(f"{nid}, 2, 1.0, {rp_nid}, 2, -1.0\n")

    # Step 1: Pre-critical / Linear Loading to u_y = 1.0 mm (2000 incs, delta_u = 5e-4 mm)
    f.write("** ----------------------------------------------------------\n")
    f.write("** STEP 1: Linear Loading to u = 1.0 mm (2000 incs, delta_u = 5e-4 mm)\n")
    f.write("** ----------------------------------------------------------\n")
    f.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=10000\n")
    f.write("*STATIC, DIRECT\n0.0005, 1.0\n")
    f.write("*BOUNDARY\n")
    f.write("N_LOWER_HOLE, 1, 2, 0.0\n")
    f.write("N_UPPER_HOLE, 1, 1, 0.0\n")
    f.write("N_RP, 2, 2, 1.0\n")
    f.write("*RESTART, WRITE, FREQUENCY=20\n")
    f.write("*OUTPUT, FIELD, FREQUENCY=10\n")
    f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
    f.write("*ELEMENT OUTPUT, ELSET=umatelem\nMISESERI, MISESAVG, S, E, SDV\n")
    f.write("*NODE PRINT, FREQ=10, NSET=N_RP\nU2, RF2\n")
    f.write("*END STEP\n")

    # Step 2: Fracture Propagation to u_y = 1.5 mm (delta_u = 2e-4 mm, 2500 incs)
    f.write("** ----------------------------------------------------------\n")
    f.write("** STEP 2: Fracture Propagation to u = 1.5 mm (2500 incs, delta_u = 2e-4 mm)\n")
    f.write("** ----------------------------------------------------------\n")
    f.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=25000\n")
    f.write("*STATIC, DIRECT\n0.0002, 0.5\n")
    f.write("*BOUNDARY\n")
    f.write("N_RP, 2, 2, 1.5\n")
    f.write("*RESTART, WRITE, FREQUENCY=20\n")
    f.write("*OUTPUT, FIELD, FREQUENCY=10\n")
    f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
    f.write("*ELEMENT OUTPUT, ELSET=umatelem\nMISESERI, MISESAVG, S, E, SDV\n")
    f.write("*NODE PRINT, FREQ=10, NSET=N_RP\nU2, RF2\n")
    f.write("*END STEP\n")

print(f"Generated {uel_inp} successfully! ({num_phys_elems} phys elements, {3*num_phys_elems} layered elements)")
