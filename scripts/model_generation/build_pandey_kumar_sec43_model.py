# -*- coding: utf-8 -*-
"""
scripts/model_generation/build_pandey_kumar_sec43_model.py
==========================================================
Task: F1688 - Pandey & Kumar (2025) Section 4.3 Reproduction Control Test
Stage A: CAD Geometry Generation, Coarse Meshing, and Layered UEL Deck Build.

Specifications:
- Plate: 65.0 x 120.0 mm
- Notch: 10.0 x 0.4 mm cutout at y = 70.0 mm (y in [69.8, 70.2] mm)
- Lower Hole: (20.0, 20.0) mm, D = 10.0 mm (R = 5.0 mm) - Pinned
- Upper Hole: (20.0, 100.0) mm, D = 10.0 mm (R = 5.0 mm) - Prescribed Disp
- Central Hole: (36.5, 51.0) mm, D = 20.0 mm (R = 10.0 mm) - Eccentric Void
- Global Seed: 1.5 mm (yields ~3,500 elements)
- Material: E = 210 GPa (210 kN/mm^2), nu = 0.3, l0 = 0.285 mm, Gc = 2.28e-3 kN/mm
- 3-Layer Deck Structure:
    * Layer 1: Phase field elements (U1/U3, DOF 3)
    * Layer 2: Mechanical displacement elements (U2/U4, DOFs 1, 2)
    * Layer 3: Companion UMAT elements (CPE4/CPE3)
- Subroutine: models/pandey_kumar_mode1/f42_mixed_uel.for (Frozen SHA-256 verified)
"""
import os
import sys
import math
import hashlib
from pathlib import Path

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def verify_uel(uel_path):
    if not os.path.exists(uel_path):
        raise FileNotFoundError("Frozen UEL not found at: %s" % uel_path)
    h = hashlib.sha256()
    with open(uel_path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    actual_hash = h.hexdigest().upper()
    if actual_hash != FROZEN_UEL_SHA256:
        raise ValueError("Frozen UEL SHA-256 violation!\nExpected: %s\nActual:   %s" % (
            FROZEN_UEL_SHA256, actual_hash
        ))
    print("[PASS] Frozen UEL integrity verified: %s" % actual_hash)
    return True


def generate_cae_mesh(output_dir):
    """Generates CAD part, seeds at 1.5 mm, meshes, and exports PK_SEC43_COARSE_PHYS.inp."""
    cae_script = os.path.join(output_dir, "run_cae_build.py")
    script_content = """# -*- coding: mbcs -*-
from abaqus import *
from abaqusConstants import *
import mesh
import os

model_name = 'PK_SEC43_COARSE'
if model_name in mdb.models:
    del mdb.models[model_name]
m = mdb.Model(name=model_name)

# 1. Sketch profile with outer boundary, notch, and 3 holes
s = m.ConstrainedSketch(name='__profile__', sheetSize=300.0)

# Outer boundary and notch
s.Line(point1=(0.0, 0.0), point2=(65.0, 0.0))
s.Line(point1=(65.0, 0.0), point2=(65.0, 120.0))
s.Line(point1=(65.0, 120.0), point2=(0.0, 120.0))
s.Line(point1=(0.0, 120.0), point2=(0.0, 70.2))
s.Line(point1=(0.0, 70.2), point2=(10.0, 70.2))
s.Line(point1=(10.0, 70.2), point2=(10.0, 69.8))
s.Line(point1=(10.0, 69.8), point2=(0.0, 69.8))
s.Line(point1=(0.0, 69.8), point2=(0.0, 0.0))

# 3 Holes:
# Central eccentric void (Circle 1): center (36.5, 51.0), R = 10.0 mm
s.CircleByCenterPerimeter(center=(36.5, 51.0), point1=(46.5, 51.0))

# Lower pinned hole (Circle 2): center (20.0, 20.0), R = 5.0 mm
s.CircleByCenterPerimeter(center=(20.0, 20.0), point1=(25.0, 20.0))

# Upper loading hole (Circle 3): center (20.0, 100.0), R = 5.0 mm
s.CircleByCenterPerimeter(center=(20.0, 100.0), point1=(25.0, 100.0))

# 2. Create 2D Planar Part
p = m.Part(name='PlateWithHoles', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
p.BaseShell(sketch=s)
del m.sketches['__profile__']

# 3. Mesh controls and seeding
p.seedPart(size=1.5, deviationFactor=0.1, minSizeFactor=0.1)
p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)

# Set element type to CPE4 / CPE3 (plane strain)
elem_type_quad = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
elem_type_tri = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
p.setElementType(regions=(p.faces,), elemTypes=(elem_type_quad, elem_type_tri))

# 4. Generate Mesh
p.generateMesh()

print('Mesh generation complete:')
print('Total Elements:', len(p.elements))
print('Total Nodes:', len(p.nodes))

# 5. Create Assembly and Job to export physical INP
a = m.rootAssembly
a.DatumCsysByDefault(CARTESIAN)
inst = a.Instance(name='PlateWithHoles-1', part=p, dependent=ON)

job = mdb.Job(name='PK_SEC43_COARSE_PHYS', model=model_name, type=ANALYSIS)
job.writeInput(consistencyChecking=OFF)
print('Wrote PK_SEC43_COARSE_PHYS.inp successfully.')
"""
    with open(cae_script, "w") as f:
        f.write(script_content)

    print("Running Abaqus CAE mesh generation...")
    import subprocess
    cmd = ["abaqus", "cae", "noGUI=" + os.path.basename(cae_script)]
    res = subprocess.run(cmd, cwd=output_dir, capture_output=True, text=True)
    if res.returncode != 0:
        print("Abaqus CAE stderr:", res.stderr)
        raise RuntimeError("Abaqus CAE failed with exit code %d" % res.returncode)
    print("Abaqus CAE stdout:\n", res.stdout)


def parse_physical_mesh(phys_inp_path):
    """Parses nodes and element connectivity from physical input deck."""
    nodes = {}
    quad_elems = {}
    tri_elems = {}
    in_nodes = False
    in_elements = False
    elem_type = None

    with open(phys_inp_path, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                in_nodes = False
                in_elements = False
                upline = l.upper()
                if upline.startswith("*NODE"):
                    in_nodes = True
                elif upline.startswith("*ELEMENT"):
                    in_elements = True
                    if "CPE4" in upline or "CPS4" in upline:
                        elem_type = "QUAD"
                    elif "CPE3" in upline or "CPS3" in upline:
                        elem_type = "TRI"
                    else:
                        elem_type = "OTHER"
                continue

            parts = [p.strip() for p in l.split(",") if p.strip()]
            if in_nodes and len(parts) >= 3:
                try:
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                except ValueError:
                    pass
            elif in_elements and len(parts) >= 4:
                try:
                    int_parts = [int(p) for p in parts]
                    eid = int_parts[0]
                    conn = int_parts[1:]
                    if elem_type == "QUAD" or len(conn) == 4:
                        quad_elems[eid] = tuple(conn[:4])
                    else:
                        tri_elems[eid] = tuple(conn[:3])
                except ValueError:
                    pass

    return nodes, quad_elems, tri_elems


def identify_hole_nodes(nodes):
    """Identifies lower hole, upper hole, and central hole nodes by geometry."""
    tol = 0.08  # 80 um tolerance on radial distance
    lower_hole_nodes = []
    upper_hole_nodes = []
    central_hole_nodes = []

    for nid, (x, y) in nodes.items():
        # Lower hole: center (20.0, 20.0), R = 5.0
        d_lower = math.hypot(x - 20.0, y - 20.0)
        if abs(d_lower - 5.0) < tol:
            lower_hole_nodes.append(nid)

        # Upper hole: center (20.0, 100.0), R = 5.0
        d_upper = math.hypot(x - 20.0, y - 100.0)
        if abs(d_upper - 5.0) < tol:
            upper_hole_nodes.append(nid)

        # Central hole: center (36.5, 51.0), R = 10.0
        d_central = math.hypot(x - 36.5, y - 51.0)
        if abs(d_central - 10.0) < tol:
            central_hole_nodes.append(nid)

    lower_hole_nodes.sort()
    upper_hole_nodes.sort()
    central_hole_nodes.sort()

    print(f"Identified Hole Boundary Nodes:")
    print(f"  Lower Hole  (Pinned):  {len(lower_hole_nodes)} nodes")
    print(f"  Upper Hole  (Loaded):  {len(upper_hole_nodes)} nodes")
    print(f"  Central Hole (Void):   {len(central_hole_nodes)} nodes")

    if len(lower_hole_nodes) == 0 or len(upper_hole_nodes) == 0:
        raise ValueError("Failed to identify loading/support hole perimeter nodes!")

    return lower_hole_nodes, upper_hole_nodes, central_hole_nodes


def write_formatted_nset(f, nset_name, node_list):
    """Writes an NSET card formatted in rows of at most 16 node labels."""
    f.write(f"*NSET, NSET={nset_name}\n")
    for i in range(0, len(node_list), 16):
        chunk = node_list[i:i+16]
        f.write(", ".join(str(n) for n in chunk) + "\n")


def build_layered_uel_deck(phys_inp_path, output_uel_inp_path, uel_rel_path="f42_mixed_uel.for"):
    """Transforms physical 2D mesh into 3-layer UEL + companion UMAT input deck."""
    nodes, quad_elems, tri_elems = parse_physical_mesh(phys_inp_path)
    num_quads = len(quad_elems)
    num_tris = len(tri_elems)
    num_phys_elems = num_quads + num_tris
    num_nodes = len(nodes)

    lower_nodes, upper_nodes, central_nodes = identify_hole_nodes(nodes)
    rp_nid = 999999

    # Material properties matching Section 4.3:
    E_mod = 210.0      # kN/mm^2 (210 GPa)
    nu = 0.3           # Poisson's ratio
    l0 = 0.285         # mm
    Gc = 0.00228       # kN/mm (2.28 N/mm)
    k_res = 1.0e-7     # Residual stiffness parameter
    num_phys_f = float(num_phys_elems)

    with open(output_uel_inp_path, "w") as f:
        f.write("*HEADING\n")
        f.write("** Production Deck: PK_SEC43_COARSE_JOB1 (Pandey-Kumar 2025 Section 4.3 Control)\n")
        f.write(f"** Total physical elements: {num_phys_elems} ({num_quads} quads, {num_tris} tris), Nodes: {num_nodes}\n")
        f.write(f"** Total 3-layer elements: {3 * num_phys_elems} (Layer1 UEL Phase, Layer2 UEL Disp, Layer3 UMAT Companion)\n")
        f.write(f"** Parameters: E={E_mod:.1f} GPa, nu={nu:.2f}, l0={l0:.4f} mm, Gc={Gc:.5f} kN/mm, k={k_res:.1e}\n")
        f.write(f"** Subroutine: {uel_rel_path} (Frozen SHA256: {FROZEN_UEL_SHA256})\n")
        f.write("** ----------------------------------------------------------\n")

        # UEL Interface Definitions (f42_mixed_uel.for ABI)
        f.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
        f.write("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")
        if num_tris > 0:
            f.write("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
            f.write("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")

        # Nodal Coordinates
        f.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            f.write(f"{nid}, {x:.9e}, {y:.9e}\n")
        # Reference Node at upper hole center (20.0, 100.0)
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
        if num_tris > 0:
            f.write("UMAT_TRIS\n")
        f.write("*ELSET, ELSET=umatelem\nAll_elem\n")

        # Node Sets
        write_formatted_nset(f, "N_LOWER_HOLE", lower_nodes)
        write_formatted_nset(f, "N_UPPER_HOLE", upper_nodes)
        write_formatted_nset(f, "N_CENTRAL_HOLE", central_nodes)
        f.write(f"*NSET, NSET=N_RP\n{rp_nid}\n")

        # UEL Property Cards matching authentic ABI:
        # PROPS: (1)=l0, (2)=Gc, (3)=E, (4)=nu, (5)=k_res, (6)=N_phys
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

        # Companion Material (Visualizer UMAT)
        f.write("*SOLID SECTION, ELSET=All_elem, MATERIAL=DUMMY_MAT\n1.0\n")
        f.write("*MATERIAL, NAME=DUMMY_MAT\n")
        f.write("*USER MATERIAL, CONSTANTS=3\n")
        f.write(f"{E_mod:.1f}, {nu:.2f}, {num_phys_f:.1f}\n")
        f.write("*DEPVAR\n20\n")

        # Rigid Kinematic Equations: Upper hole nodes tied to N_RP in DOF 2
        f.write("** ----------------------------------------------------------\n")
        f.write("** EQUATIONS (Rigid tensile pull of upper hole pin tied to RP in DOF 2)\n")
        f.write("** ----------------------------------------------------------\n")
        for nid in upper_nodes:
            f.write("*EQUATION\n2\n")
            f.write(f"{nid}, 2, 1.0, {rp_nid}, 2, -1.0\n")

        # Step 1: Pre-critical / Linear Loading to u_y = 1.0 mm (2,000 increments)
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 1: Linear Loading to u = 1.0 mm (2000 incs, delta_u = 5e-4 mm)\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=10000\n")
        f.write("*STATIC\n0.0005, 1.0, 1.0e-7, 0.005\n")
        f.write("*BOUNDARY\n")
        f.write("N_LOWER_HOLE, 1, 2, 0.0\n")
        f.write("N_UPPER_HOLE, 1, 1, 0.0\n")
        f.write("N_RP, 2, 2, 1.0\n")
        f.write("*RESTART, WRITE, FREQUENCY=5\n")
        f.write("*OUTPUT, FIELD, FREQUENCY=5\n")
        f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=umatelem\nMISESERI, MISESAVG, S, E, SDV\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        f.write("*END STEP\n")

        # Step 2: Fracture Propagation to u_y = 1.5 mm (covering point s4 at u = 1.46 mm)
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 2: Fracture Propagation to u = 1.5 mm (delta_u = 2e-4 mm)\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=25000\n")
        f.write("*STATIC\n0.0004, 1.0, 1.0e-8, 0.002\n")
        f.write("*BOUNDARY\n")
        f.write("N_RP, 2, 2, 1.5\n")
        f.write("*RESTART, WRITE, FREQUENCY=5\n")
        f.write("*OUTPUT, FIELD, FREQUENCY=5\n")
        f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=umatelem\nMISESERI, MISESAVG, S, E, SDV\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        f.write("*END STEP\n")

    print(f"[PASS] Successfully generated 3-layer UEL deck: {output_uel_inp_path}")
    print(f"  Physical Elements: {num_phys_elems}")
    print(f"  Layered Elements:  {3 * num_phys_elems}")
    print(f"  Total Nodes:       {num_nodes + 1}")


def main():
    repo_root = Path(__file__).resolve().parents[2]
    out_dir = repo_root / "models" / "pandey_kumar_mode1" / "188_pk_sec43_hole_plate"
    out_dir.mkdir(parents=True, exist_ok=True)

    uel_src = repo_root / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
    verify_uel(str(uel_src))

    # Copy frozen UEL to local folder for standalone qualification
    local_uel = out_dir / "f42_mixed_uel.for"
    if not local_uel.exists() or local_uel.read_bytes() != uel_src.read_bytes():
        import shutil
        shutil.copyfile(str(uel_src), str(local_uel))
        print("Copied frozen UEL to local deck directory.")

    # 1. Generate CAD mesh
    phys_inp = out_dir / "PK_SEC43_COARSE_PHYS.inp"
    if not phys_inp.exists():
        generate_cae_mesh(str(out_dir))
    else:
        print(f"Using existing physical mesh: {phys_inp}")

    # 2. Build 3-layer UEL input deck
    uel_inp = out_dir / "PK_SEC43_COARSE_JOB1.inp"
    build_layered_uel_deck(str(phys_inp), str(uel_inp))


if __name__ == "__main__":
    main()
