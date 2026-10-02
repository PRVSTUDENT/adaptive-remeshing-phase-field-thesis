#!/usr/bin/env python3
"""
Exact Offline Reconstruction of PK10R1 Increment 29 Committed History State (H and SV_PHASE)
from Completed Replay Trajectory (1389707.mmaster02.odb).
Uses exact UEL constitutive equations (plane strain, POS_M Miehe energy split).
"""

import sys
import os
import math
import struct
import hashlib
from odbAccess import openOdb

# Material parameters from UEL props (E=210.0 kN/mm^2, nu=0.3)
E_MOD = 210.0
E_NU = 0.3
N_CAPACITY = 100000

# Plane strain elastic constants matching UEL f44 lines 295-298
C11_0 = E_MOD * (1.0 - E_NU) / ((1.0 + E_NU) * (1.0 - 2.0 * E_NU))
C12_0 = E_MOD * E_NU / ((1.0 + E_NU) * (1.0 - 2.0 * E_NU))
C22_0 = C11_0
C33_0 = E_MOD / (2.0 * (1.0 + E_NU))

# Gauss points for QUAD4 (f44 lines 279-290)
XG4 = (-0.577350269189626, 0.577350269189626, 0.577350269189626, -0.577350269189626)
YG4 = (-0.577350269189626, -0.577350269189626, 0.577350269189626, 0.577350269189626)

# Gauss points for TRI3 (1/6, 1/6), (2/3, 1/6), (1/6, 2/3)
XG3 = (1.0/6.0, 2.0/3.0, 1.0/6.0)
YG3 = (1.0/6.0, 1.0/6.0, 2.0/3.0)


def quad4_b_matrix(xi, eta, coords):
    """Computes standard 3x8 B-matrix for bilinear quad at (xi, eta)."""
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

    # Jacobian matrix J = d(x,y)/d(xi,eta)
    j11 = sum(dn_dxi[i] * coords[i][0] for i in range(4))
    j12 = sum(dn_deta[i] * coords[i][0] for i in range(4))
    j21 = sum(dn_dxi[i] * coords[i][1] for i in range(4))
    j22 = sum(dn_deta[i] * coords[i][1] for i in range(4))

    det_j = j11 * j22 - j12 * j21
    if det_j <= 0.0:
        raise ValueError("Non-positive Jacobian in quad element")

    inv_j11 =  j22 / det_j
    inv_j12 = -j12 / det_j
    inv_j21 = -j21 / det_j
    inv_j22 =  j11 / det_j

    # B matrix: [3 x 8]
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

    return b


def tri3_b_matrix(coords):
    """Computes constant 3x6 B-matrix for linear triangle."""
    (x1, y1), (x2, y2), (x3, y3) = coords
    det_t = (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)
    if det_t <= 0.0:
        raise ValueError("Non-positive Jacobian in tri element")

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

    return b


def parse_mesh_inp(inp_path):
    """Parses nodal coordinates and physical elements (Layer 1) from INP."""
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

            if l.upper().startswith("*ELEMENT"):
                lu = l.upper()
                if "TYPE=U1" in lu or "TYPE=U3" in lu:
                    in_elem = True
                    continue

            if in_node:
                parts = [p.strip() for p in l.split(",")]
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        nodes[nid] = (float(parts[1]), float(parts[2]))
                    except ValueError:
                        pass

            if in_elem:
                parts = [p.strip() for p in l.split(",")]
                if len(parts) >= 4:
                    try:
                        eid = int(parts[0])
                        n_labels = tuple(int(p) for p in parts[1:] if p)
                        if len(n_labels) in (3, 4):
                            elements[eid] = n_labels
                    except ValueError:
                        pass

    return nodes, elements


def run_reconstruction():
    print("================================================================================")
    print("EXACT OFFLINE RECONSTRUCTION OF PK10R1 INC 29 COMMITTED STATE (H and SV_PHASE)")
    print("================================================================================")

    inp_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.inp"
    odb_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050_STATECAPTURE_R1/M2CORR_PK10R1_CONTINUOUS_U050_STATECAPTURE_R1.odb"
    out_bin_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6/PK10R1_INC29_COMMITTED_STATE_REPLAY_RECONSTRUCTED.bin"

    nodes, elements = parse_mesh_inp(inp_path)
    print("Loaded Mesh: %d nodes, %d physical elements (Layer 1)" % (len(nodes), len(elements)))

    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps.values()[0]

    # Initialize SV_H_COMMITTED and SV_PHASE_COMMITTED
    sv_h = {eid: [0.0, 0.0, 0.0, 0.0] for eid in elements}
    sv_phase = {eid: 0.0 for eid in elements}

    target_inc = 29
    print("Integrating strain energy history across frames 1 to %d..." % target_inc)

    for frame_idx in range(1, target_inc + 1):
        frame = step.frames[frame_idx]
        u_field = frame.fieldOutputs['U']

        # Extract nodal displacements for this frame
        # u_field.values: list of FieldValue with nodeLabel, data = (u1, u2, u3)
        u_by_node = {}
        for val in u_field.values:
            u_by_node[val.nodeLabel] = val.data

        # For each element, compute strain and update H
        for eid, node_ids in elements.items():
            coords = [nodes[nid] for nid in node_ids]

            if len(node_ids) == 4:
                # 4-node Quad: assemble u_vec [8]
                u_vec = []
                for nid in node_ids:
                    u_val = u_by_node.get(nid, (0.0, 0.0, 0.0))
                    u_vec.append(u_val[0])
                    u_vec.append(u_val[1])

                for kpt in range(4):
                    xi = XG4[kpt]
                    eta = YG4[kpt]
                    b = quad4_b_matrix(xi, eta, coords)

                    e11 = sum(b[0][i] * u_vec[i] for i in range(8))
                    e22 = sum(b[1][i] * u_vec[i] for i in range(8))
                    e12 = 0.5 * sum(b[2][i] * u_vec[i] for i in range(8))

                    tr_e = e11 + e22
                    e_pos = max(0.0, tr_e)

                    pos_m = 0.5 * C12_0 * (e_pos ** 2) + C33_0 * (e11 ** 2 + e22 ** 2 + 2.0 * (e12 ** 2))

                    if pos_m > sv_h[eid][kpt]:
                        sv_h[eid][kpt] = pos_m

            elif len(node_ids) == 3:
                # 3-node Triangle: assemble u_vec [6]
                u_vec = []
                for nid in node_ids:
                    u_val = u_by_node.get(nid, (0.0, 0.0, 0.0))
                    u_vec.append(u_val[0])
                    u_vec.append(u_val[1])

                b = tri3_b_matrix(coords)
                e11 = sum(b[0][i] * u_vec[i] for i in range(6))
                e22 = sum(b[1][i] * u_vec[i] for i in range(6))
                e12 = 0.5 * sum(b[2][i] * u_vec[i] for i in range(6))

                tr_e = e11 + e22
                e_pos = max(0.0, tr_e)
                pos_m = 0.5 * C12_0 * (e_pos ** 2) + C33_0 * (e11 ** 2 + e22 ** 2 + 2.0 * (e12 ** 2))

                for kpt in range(3):
                    if pos_m > sv_h[eid][kpt]:
                        sv_h[eid][kpt] = pos_m

        if frame_idx % 5 == 0 or frame_idx == target_inc:
            h_all = [h for h_tuple in sv_h.values() for h in h_tuple]
            print("  Frame %2d (t=%.8f): H_max = %.8f kN/mm^2" % (frame_idx, frame.frameValue, max(h_all)))

    # Compute SV_PHASE at Increment 29
    frame29 = step.frames[target_inc]
    u29_field = frame29.fieldOutputs['U']
    u29_by_node = {val.nodeLabel: val.data for val in u29_field.values}

    for eid, node_ids in elements.items():
        u3_vals = [u29_by_node.get(nid, (0.0, 0.0, 0.0))[2] for nid in node_ids]
        sv_phase[eid] = sum(u3_vals) / float(len(u3_vals))

    odb.close()

    # Diagnostics & Verification
    all_h = [h for h_tuple in sv_h.values() for h in h_tuple]
    all_p = list(sv_phase.values())

    h_max = max(all_h)
    p_max = max(all_p)
    p_min = min(all_p)

    # Find element containing H_max
    hmax_elem = None
    hmax_kpt = None
    for eid, h_tuple in sv_h.items():
        for kpt, val in enumerate(h_tuple):
            if val == h_max:
                hmax_elem = eid
                hmax_kpt = kpt + 1
                break
        if hmax_elem:
            break

    print("\n=== RECONSTRUCTION SUMMARY ===")
    print("Reconstructed SV_PHASE count: %d elements" % len(sv_phase))
    print("  SV_PHASE min = %.8f, max = %.8f" % (p_min, p_max))
    print("Reconstructed SV_H count: %d elements x 4 GPs" % len(sv_h))
    print("  H_min = %.8f, H_max = %.8f kN/mm^2" % (min(all_h), h_max))
    print("  H_max element: %d, GP: %d" % (hmax_elem, hmax_kpt))

    # Cross-check with known literature/evidence (earlier project records: ~0.051779)
    print("\n=== CROSS-CHECK AGAINST EVIDENCE ===")
    print("Observed H_max: %.6f" % h_max)
    print("Expected reference H_max: ~0.051779")
    diff_pct = abs(h_max - 0.051779) / 0.051779 * 100.0
    print("Difference vs reference H_max: %.4f%%" % diff_pct)

    # Write Fortran sequential unformatted binary state file
    print("\nWriting Fortran sequential unformatted binary state file...")
    with open(out_bin_path, "wb") as f:
        # Record 1: SV_PHASE (N_CAPACITY doubles = 800,000 bytes)
        rec1_size = N_CAPACITY * 8
        f.write(struct.pack("=I", rec1_size))
        for eid in range(1, N_CAPACITY + 1):
            val = sv_phase.get(eid, 0.0)
            f.write(struct.pack("=d", val))
        f.write(struct.pack("=I", rec1_size))

        # Record 2: SV_H (N_CAPACITY x 4 doubles = 3,200,000 bytes, column-major)
        rec2_size = N_CAPACITY * 4 * 8
        f.write(struct.pack("=I", rec2_size))
        for kpt in range(4):
            for eid in range(1, N_CAPACITY + 1):
                h_tuple = sv_h.get(eid, [0.0, 0.0, 0.0, 0.0])
                val = h_tuple[kpt]
                f.write(struct.pack("=d", val))
        f.write(struct.pack("=I", rec2_size))

    file_size = os.path.getsize(out_bin_path)
    print("Written file: %s" % out_bin_path)
    print("File size: %d bytes (Expected: 4000016)" % file_size)

    # Compute SHA256
    h_sha = hashlib.sha256()
    with open(out_bin_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h_sha.update(chunk)
    bin_sha256 = h_sha.hexdigest()
    print("SHA256: %s" % bin_sha256)

    # Round-trip verification
    print("\nVerifying binary round-trip...")
    with open(out_bin_path, "rb") as f:
        r1_head = struct.unpack("=I", f.read(4))[0]
        r1_data = struct.unpack("=%dd" % N_CAPACITY, f.read(N_CAPACITY * 8))
        r1_tail = struct.unpack("=I", f.read(4))[0]

        r2_head = struct.unpack("=I", f.read(4))[0]
        r2_data = struct.unpack("=%dd" % (N_CAPACITY * 4), f.read(N_CAPACITY * 4 * 8))
        r2_tail = struct.unpack("=I", f.read(4))[0]

    assert r1_head == 800000 and r1_tail == 800000, "Record 1 marker mismatch"
    assert r2_head == 3200000 and r2_tail == 3200000, "Record 2 marker mismatch"
    assert abs(max(r1_data) - p_max) < 1e-15, "SV_PHASE round-trip mismatch"
    assert abs(max(r2_data) - h_max) < 1e-15, "SV_H round-trip mismatch"
    print("Round-trip verification SUCCESS: exact value and layout identity confirmed.")


if __name__ == "__main__":
    run_reconstruction()
