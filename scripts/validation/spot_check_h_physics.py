import os
import math
from odbAccess import openOdb

E_MOD = 210.0
E_NU = 0.3

C11_0 = E_MOD * (1.0 - E_NU) / ((1.0 + E_NU) * (1.0 - 2.0 * E_NU))
C12_0 = E_MOD * E_NU / ((1.0 + E_NU) * (1.0 - 2.0 * E_NU))
C22_0 = C11_0
C33_0 = E_MOD / (2.0 * (1.0 + E_NU))

XG4 = (-0.577350269189626, 0.577350269189626, 0.577350269189626, -0.577350269189626)
YG4 = (-0.577350269189626, -0.577350269189626, 0.577350269189626, 0.577350269189626)

XG3 = (1.0/6.0, 2.0/3.0, 1.0/6.0)
YG3 = (1.0/6.0, 1.0/6.0, 2.0/3.0)


def quad4_b_matrix(xi, eta, coords):
    dn_dxi = (
        -0.25 * (1.0 - eta),
         0.25 * (1.0 - eta),
         0.25 * (1.0 + eta),
        -0.25 * (1.0 + eta)
    )
    dn_deta = (
        -0.25 * (1.0 - xi),
        -0.25 * (1.0 + xi),
         0.25 * (1.0 + xi),
         0.25 * (1.0 - xi)
    )

    j11 = sum(dn_dxi[i] * coords[i][0] for i in range(4))
    j12 = sum(dn_deta[i] * coords[i][0] for i in range(4))
    j21 = sum(dn_dxi[i] * coords[i][1] for i in range(4))
    j22 = sum(dn_deta[i] * coords[i][1] for i in range(4))

    det_j = j11 * j22 - j12 * j21
    inv_j11 =  j22 / det_j
    inv_j12 = -j12 / det_j
    inv_j21 = -j21 / det_j
    inv_j22 =  j11 / det_j

    b = [[0.0 for _ in range(8)] for _ in range(3)]
    for i in range(4):
        dn_dx = inv_j11 * dn_dxi[i] + inv_j12 * dn_deta[i]
        dn_dy = inv_j21 * dn_dxi[i] + inv_j22 * dn_deta[i]

        b[0][2 * i]     = dn_dx
        b[0][2 * i + 1] = 0.0
        b[1][2 * i]     = 0.0
        b[1][2 * i + 1] = dn_dy
        b[2][2 * i]     = dn_dy
        b[2][2 * i + 1] = dn_dx

    return b, det_j


def tri3_b_matrix(coords):
    (x1, y1), (x2, y2), (x3, y3) = coords
    det_t = (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)
    b = [[0.0 for _ in range(6)] for _ in range(3)]
    b[0][0] = (y2 - y3) / det_t
    b[0][2] = (y3 - y1) / det_t
    b[0][4] = (y1 - y2) / det_t
    b[1][1] = (x3 - x2) / det_t
    b[1][3] = (x1 - x3) / det_t
    b[1][5] = (x2 - x1) / det_t
    b[2][0] = (x3 - x2) / det_t
    b[2][1] = (y2 - y3) / det_t
    b[2][2] = (x1 - x3) / det_t
    b[2][3] = (y3 - y1) / det_t
    b[2][4] = (x2 - x1) / det_t
    b[2][5] = (y1 - y2) / det_t
    return b, det_t


def parse_mesh(inp_path):
    nodes = {}
    elements = {}
    in_node = False
    in_elem = False
    with open(inp_path, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                in_node = False
                in_elem = False
            if l.upper().startswith("*NODE"):
                in_node = True
                continue
            if l.upper().startswith("*ELEMENT") and ("TYPE=U1" in l.upper() or "TYPE=U3" in l.upper()):
                in_elem = True
                continue
            if in_node:
                parts = [p.strip() for p in l.split(",")]
                if len(parts) >= 3:
                    try:
                        nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                    except ValueError:
                        pass
            if in_elem:
                parts = [p.strip() for p in l.split(",")]
                if len(parts) >= 4:
                    try:
                        eid = int(parts[0])
                        elements[eid] = tuple(int(p) for p in parts[1:] if p)
                    except ValueError:
                        pass
    return nodes, elements


inp_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.inp"
odb_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050_STATECAPTURE_R1/M2CORR_PK10R1_CONTINUOUS_U050_STATECAPTURE_R1.odb"

nodes, elements = parse_mesh(inp_path)
odb = openOdb(odb_path, readOnly=True)
step = odb.steps.values()[0]
frame29 = step.frames[29]
u_field = frame29.fieldOutputs['U']
u_by_node = {val.nodeLabel: val.data for val in u_field.values}

test_elements = [
    (4788, "Transition Triangle at Notch Region (Hmax location)"),
    (4780, "Near-Tip Process Zone Quad"),
    (5000, "Intermediate Zone Quad"),
    (100,  "Far-Field Quad (Bottom Boundary)")
]

print("=== PHYSICAL AUDIT OF STRAINS, STRESSES, AND DRIVING ENERGY (INCREMENT 29) ===")
for eid, desc in test_elements:
    if eid not in elements:
        print("Element %d NOT FOUND in Layer 1 mesh!" % eid)
        continue
    node_ids = elements[eid]
    coords = [nodes[nid] for nid in node_ids]
    u_vec = []
    for nid in node_ids:
        u_val = u_by_node.get(nid, (0.0, 0.0, 0.0))
        u_vec.append(u_val[0])
        u_vec.append(u_val[1])

    print("\n--- Element %d: %s (Nodes: %d) ---" % (eid, desc, len(node_ids)))
    print("  Node IDs:", node_ids)
    print("  Center Coord: (%.6f, %.6f)" % (sum(c[0] for c in coords)/len(coords), sum(c[1] for c in coords)/len(coords)))
    print("  Nodal U1:", [u_by_node.get(nid, (0.0, 0.0, 0.0))[0] for nid in node_ids])
    print("  Nodal U2:", [u_by_node.get(nid, (0.0, 0.0, 0.0))[1] for nid in node_ids])
    print("  Nodal U3 (Phase):", [u_by_node.get(nid, (0.0, 0.0, 0.0))[2] for nid in node_ids])

    if len(node_ids) == 4:
        for kpt in range(4):
            xi = XG4[kpt]
            eta = YG4[kpt]
            b, det_j = quad4_b_matrix(xi, eta, coords)
            e11 = sum(b[0][i] * u_vec[i] for i in range(8))
            e22 = sum(b[1][i] * u_vec[i] for i in range(8))
            e12 = 0.5 * sum(b[2][i] * u_vec[i] for i in range(8))

            tr_e = e11 + e22
            e_pos = max(0.0, tr_e)
            pos_m = 0.5 * C12_0 * (e_pos ** 2) + C33_0 * (e11 ** 2 + e22 ** 2 + 2.0 * (e12 ** 2))

            print("  GP %d: e11=%+.6e, e22=%+.6e, e12=%+.6e | tr(e)=%+.6e | psi_plus=%.6f kN/mm^2" % (
                kpt+1, e11, e22, e12, tr_e, pos_m
            ))
    elif len(node_ids) == 3:
        b, det_t = tri3_b_matrix(coords)
        e11 = sum(b[0][i] * u_vec[i] for i in range(6))
        e22 = sum(b[1][i] * u_vec[i] for i in range(6))
        e12 = 0.5 * sum(b[2][i] * u_vec[i] for i in range(6))
        tr_e = e11 + e22
        e_pos = max(0.0, tr_e)
        pos_m = 0.5 * C12_0 * (e_pos ** 2) + C33_0 * (e11 ** 2 + e22 ** 2 + 2.0 * (e12 ** 2))

        print("  Tri Const GP: e11=%+.6e, e22=%+.6e, e12=%+.6e | tr(e)=%+.6e | psi_plus=%.6f kN/mm^2" % (
            e11, e22, e12, tr_e, pos_m
        ))

odb.close()
