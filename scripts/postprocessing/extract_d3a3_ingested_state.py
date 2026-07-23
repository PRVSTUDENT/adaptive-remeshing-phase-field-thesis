#!/usr/bin/env python3
"""Extract D3A3 ingested/equilibrated/released state from an Abaqus ODB.

Run this with Abaqus Python on the cluster after the full D3A3-R2 job, not
with ordinary CPython.
"""

from __future__ import print_function

import argparse
import csv
import json
import math
import os


N_ELEM = 6400
N_IP = 4
NODE_OFFSET = 100000
CHECKPOINT_U2 = 0.003000000026077032
GC = 2.7e-3
LC = 0.015
THICKNESS = 1.0
GAUSS = [
    (-1.0 / math.sqrt(3.0), -1.0 / math.sqrt(3.0)),
    (1.0 / math.sqrt(3.0), -1.0 / math.sqrt(3.0)),
    (1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0)),
    (-1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0)),
]
ODB_TO_UEL_IP = {
    1: 1,
    2: 2,
    3: 4,
    4: 3,
}


def odb_data(value):
    try:
        return value.dataDouble
    except Exception:
        return value.data


def odb_scalar(value):
    data = odb_data(value)
    try:
        return float(data)
    except TypeError:
        return float(data[0])


def is_finite(value):
    try:
        return math.isfinite(value)
    except AttributeError:
        return not (math.isnan(value) or math.isinf(value))


def read_csv(path):
    with open(path, "r") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, fields, rows):
    with open(path, "w") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path, data):
    with open(path, "w") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def shape_values(ip):
    xi, eta = GAUSS[ip - 1]
    return [
        0.25 * (1.0 - xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 + eta),
        0.25 * (1.0 - xi) * (1.0 + eta),
    ]


def load_package(package_dir, model_dir):
    nodal = {}
    for row in read_csv(os.path.join(package_dir, "D3_TRANSFERRED_NODAL_D.csv")):
        nodal[int(row["node"])] = float(row["d"])
    history = {}
    energy = {}
    for row in read_csv(os.path.join(package_dir, "D3_TRANSFERRED_IP_H.csv")):
        key = (int(row["element"]), int(row["integration_point"]))
        history[key] = float(row["H"])
        energy[key] = float(row.get("stress_strain_energy_density", row["H"]))
    elements = {}
    for row in read_csv(os.path.join(model_dir, "target", "target_elements.csv")):
        elements[int(row["element"])] = [int(row["n1"]), int(row["n2"]), int(row["n3"]), int(row["n4"])]
    return nodal, history, energy, elements


def load_nodes(model_dir):
    nodes = {}
    for row in read_csv(os.path.join(model_dir, "target", "target_nodes.csv")):
        nodes[int(row["node"])] = (float(row["x"]), float(row["y"]))
    return nodes


def expected_phase(element, ip, nodal_d, elements):
    weights = shape_values(ip)
    return sum(weights[i] * nodal_d[elements[element][i]] for i in range(4))


def frame_tag(step_name, frame_index, total):
    if step_name == "INGEST_TRANSFERRED_STATE":
        return "F0_ingested"
    if step_name == "CHECKPOINT_EQUILIBRATION_PHASE_FIXED":
        return "F1_equilibrated"
    if step_name == "PHASE_RELEASE_HOLD" and frame_index == total - 1:
        return "F3_release_last"
    if step_name == "PHASE_RELEASE_HOLD":
        return "F2_release_first"
    return step_name


def selected_frames(odb):
    selected = []
    for name in ["INGEST_TRANSFERRED_STATE", "CHECKPOINT_EQUILIBRATION_PHASE_FIXED"]:
        step = odb.steps[name]
        selected.append((frame_tag(name, len(step.frames) - 1, len(step.frames)), name, len(step.frames) - 1, step.frames[-1]))
    step = odb.steps["PHASE_RELEASE_HOLD"]
    first = 1 if len(step.frames) > 1 else 0
    selected.append((frame_tag("PHASE_RELEASE_HOLD", first, len(step.frames)), "PHASE_RELEASE_HOLD", first, step.frames[first]))
    if len(step.frames) > 1:
        selected.append((frame_tag("PHASE_RELEASE_HOLD", len(step.frames) - 1, len(step.frames)), "PHASE_RELEASE_HOLD", len(step.frames) - 1, step.frames[-1]))
    return selected


def physical_label(label):
    label = int(label)
    if 2 * N_ELEM < label <= 3 * N_ELEM:
        return label - 2 * N_ELEM
    if 1 <= label <= N_ELEM:
        return label
    return None


def field_by_key(frame, field_name):
    out = {}
    if field_name not in frame.fieldOutputs:
        return out
    for value in frame.fieldOutputs[field_name].values:
        elem = physical_label(value.elementLabel)
        if elem is not None:
            odb_ip = int(value.integrationPoint)
            uel_ip = ODB_TO_UEL_IP[odb_ip]
            out[(elem, uel_ip)] = odb_scalar(value)
    return out


def top_region(odb):
    try:
        return odb.rootAssembly.nodeSets["TOP"]
    except KeyError:
        pass
    for instance in odb.rootAssembly.instances.values():
        try:
            return instance.nodeSets["TOP"]
        except KeyError:
            pass
    raise KeyError("TOP node set not found in ODB root assembly or instances")


def rf_u(frame, top_set):
    u2_vals = []
    rf2_sum = 0.0
    if "U" in frame.fieldOutputs:
        for value in frame.fieldOutputs["U"].getSubset(region=top_set).values:
            data = odb_data(value)
            if len(data) >= 2:
                u2_vals.append(float(data[1]))
    if "RF" in frame.fieldOutputs:
        for value in frame.fieldOutputs["RF"].getSubset(region=top_set).values:
            data = odb_data(value)
            if len(data) >= 2:
                rf2_sum += float(data[1])
    return {
        "top_node_count": len(u2_vals),
        "top_u2_mean": sum(u2_vals) / float(len(u2_vals)) if u2_vals else "",
        "top_u2_min": min(u2_vals) if u2_vals else "",
        "top_u2_max": max(u2_vals) if u2_vals else "",
        "top_rf2_sum": rf2_sum,
    }


def phase_nodal_u3(frame):
    out = {}
    if "U" not in frame.fieldOutputs:
        return out
    for value in frame.fieldOutputs["U"].values:
        label = int(value.nodeLabel)
        if 1 <= label <= NODE_OFFSET:
            data = odb_data(value)
            if len(data) >= 3:
                out[label] = float(data[2])
    return out


def solve_4x4(matrix, rhs):
    a = [[float(matrix[i][j]) for j in range(4)] + [float(rhs[i])] for i in range(4)]
    for col in range(4):
        pivot = col
        for row in range(col + 1, 4):
            if abs(a[row][col]) > abs(a[pivot][col]):
                pivot = row
        if abs(a[pivot][col]) < 1.0e-30:
            raise ValueError("singular 4x4 phase recovery matrix")
        if pivot != col:
            a[col], a[pivot] = a[pivot], a[col]
        scale = a[col][col]
        for j in range(col, 5):
            a[col][j] /= scale
        for row in range(4):
            if row == col:
                continue
            factor = a[row][col]
            for j in range(col, 5):
                a[row][j] -= factor * a[col][j]
    return [a[i][4] for i in range(4)]


PHASE_RECOVERY_MATRIX = [shape_values(ip) for ip in range(1, N_IP + 1)]


def recover_phase_nodes(tag, step_name, frame_index, sdv15, nodal_d, elements):
    by_node = {}
    rows = []
    complete_elements = 0
    finite = True
    in_range = True
    for element, conn in sorted(elements.items()):
        values = []
        complete = True
        for ip in range(1, N_IP + 1):
            value = sdv15.get((element, ip))
            if value is None:
                complete = False
                break
            values.append(float(value))
        if not complete:
            continue
        complete_elements += 1
        nodal = solve_4x4(PHASE_RECOVERY_MATRIX, values)
        for i, node in enumerate(conn):
            value = nodal[i]
            finite = finite and is_finite(value)
            in_range = in_range and (-1.0e-10 <= value <= 1.0 + 1.0e-10)
            by_node.setdefault(node, []).append(value)

    recovered = {}
    for node, values in sorted(by_node.items()):
        mean = sum(values) / float(len(values))
        vmin = min(values)
        vmax = max(values)
        transferred = nodal_d.get(node, "")
        delta = "" if transferred == "" else mean - float(transferred)
        recovered[node] = mean
        rows.append({
            "frame_tag": tag,
            "step": step_name,
            "frame_index": frame_index,
            "node": node,
            "recovered_d_mean": mean,
            "recovered_d_min": vmin,
            "recovered_d_max": vmax,
            "recovered_d_spread": vmax - vmin,
            "adjacent_element_values": len(values),
            "transferred_d": transferred,
            "recovered_minus_transferred": delta,
        })
    spreads = [float(row["recovered_d_spread"]) for row in rows]
    compare_errors = [
        abs(float(row["recovered_minus_transferred"]))
        for row in rows
        if row["recovered_minus_transferred"] != "" and tag in ("F0_ingested", "F1_equilibrated")
    ]
    audit = {
        "frame_tag": tag,
        "step": step_name,
        "frame_index": frame_index,
        "recovered_nodes": len(recovered),
        "elements_with_complete_IP_state": complete_elements,
        "missing_nodes": len(nodal_d) - len(recovered),
        "all_recovered_values_finite": finite,
        "values_within_0_1_tolerance": in_range,
        "maximum_shared_node_reconstruction_spread": max(spreads) if spreads else None,
        "maximum_recovered_minus_transferred_abs": max(compare_errors) if compare_errors else None,
    }
    return recovered, rows, audit


def metric(values):
    if not values:
        return {"count": 0, "l2": None, "max_abs": None}
    return {
        "count": len(values),
        "l2": math.sqrt(sum(v * v for v in values) / float(len(values))),
        "max_abs": max(abs(v) for v in values),
    }


def shape_and_grad(xi, eta):
    n = [
        0.25 * (1.0 - xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 + eta),
        0.25 * (1.0 - xi) * (1.0 + eta),
    ]
    dndxi = [
        (-0.25 * (1.0 - eta), -0.25 * (1.0 - xi)),
        (0.25 * (1.0 - eta), -0.25 * (1.0 + xi)),
        (0.25 * (1.0 + eta), 0.25 * (1.0 + xi)),
        (-0.25 * (1.0 + eta), 0.25 * (1.0 - xi)),
    ]
    return n, dndxi


def jacobian(coords, dndxi):
    j11 = sum(coords[i][0] * dndxi[i][0] for i in range(4))
    j12 = sum(coords[i][0] * dndxi[i][1] for i in range(4))
    j21 = sum(coords[i][1] * dndxi[i][0] for i in range(4))
    j22 = sum(coords[i][1] * dndxi[i][1] for i in range(4))
    det = j11 * j22 - j12 * j21
    inv = [[j22 / det, -j12 / det], [-j21 / det, j11 / det]]
    return det, inv


def grad_shape(dndxi, inv_j):
    out = []
    for dxi, deta in dndxi:
        dx = dxi * inv_j[0][0] + deta * inv_j[1][0]
        dy = dxi * inv_j[0][1] + deta * inv_j[1][1]
        out.append((dx, dy))
    return out


def reconstruct_energy(tag, nodes, elements, phase_nodes, sdv12, sdv13):
    bulk_sdv12 = 0.0
    undamaged_sdv13 = 0.0
    fracture_local = 0.0
    fracture_gradient = 0.0
    non_positive_detj = 0
    missing_phase_nodes = 0
    missing_sdv12 = 0
    missing_sdv13 = 0
    min_detj = None
    max_detj = None
    phase_values = []
    for element, conn in sorted(elements.items()):
        coords = [nodes[n] for n in conn]
        if any(n not in phase_nodes for n in conn):
            missing_phase_nodes += sum(1 for n in conn if n not in phase_nodes)
            continue
        nodal_d = [phase_nodes[n] for n in conn]
        for ip in range(1, N_IP + 1):
            xi, eta = GAUSS[ip - 1]
            nvals, dndxi = shape_and_grad(xi, eta)
            detj, inv_j = jacobian(coords, dndxi)
            if min_detj is None or detj < min_detj:
                min_detj = detj
            if max_detj is None or detj > max_detj:
                max_detj = detj
            if detj <= 0.0:
                non_positive_detj += 1
            dndx = grad_shape(dndxi, inv_j)
            d_ip = sum(nvals[i] * nodal_d[i] for i in range(4))
            grad_x = sum(dndx[i][0] * nodal_d[i] for i in range(4))
            grad_y = sum(dndx[i][1] * nodal_d[i] for i in range(4))
            phase_values.append(d_ip)
            jac_weight = detj * THICKNESS
            key = (element, ip)
            if key in sdv12:
                bulk_sdv12 += float(sdv12[key]) * jac_weight
            else:
                missing_sdv12 += 1
            if key in sdv13:
                undamaged_sdv13 += float(sdv13[key]) * jac_weight
            else:
                missing_sdv13 += 1
            local_density = GC * d_ip * d_ip / (2.0 * LC)
            gradient_density = GC * LC * (grad_x * grad_x + grad_y * grad_y) / 2.0
            fracture_local += local_density * jac_weight
            fracture_gradient += gradient_density * jac_weight
    total_fracture = fracture_local + fracture_gradient
    total_internal = bulk_sdv12 + total_fracture
    return {
        "frame_tag": tag,
        "bulk_energy_from_SDV12": bulk_sdv12,
        "undamaged_bulk_energy_from_SDV13": undamaged_sdv13,
        "fracture_energy_local_term": fracture_local,
        "fracture_energy_gradient_term": fracture_gradient,
        "total_fracture_energy": total_fracture,
        "total_reconstructed_internal_energy": total_internal,
        "non_positive_detJ_count": non_positive_detj,
        "minimum_detJ": min_detj,
        "maximum_detJ": max_detj,
        "missing_phase_node_values": missing_phase_nodes,
        "missing_sdv12_values": missing_sdv12,
        "missing_sdv13_values": missing_sdv13,
        "phase_min": min(phase_values) if phase_values else None,
        "phase_max": max(phase_values) if phase_values else None,
        "phase_l2": math.sqrt(sum(v * v for v in phase_values) / float(len(phase_values))) if phase_values else None,
        "phase_range": (max(phase_values) - min(phase_values)) if phase_values else None,
        "method": "target_Q4_2x2_bulk_SDV12_plus_AT2_fracture_energy",
        "Gc": GC,
        "lc": LC,
        "thickness": THICKNESS,
    }


def extract(odb_path, package_dir, model_dir, out_dir):
    from odbAccess import openOdb

    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    nodal_d, h_transfer, energy_transfer, elements = load_package(package_dir, model_dir)
    nodes = load_nodes(model_dir)
    odb = openOdb(path=str(odb_path), readOnly=True)
    try:
        top_set = top_region(odb)
        state_rows = []
        transfer_rows = []
        rf_rows = []
        energy_rows = []
        all_phase_rows = []
        recovery_rows = []
        recovery_audits = []
        recovered_by_tag = {}
        snapshots = {}
        for tag, step_name, frame_index, frame in selected_frames(odb):
            sdv15 = field_by_key(frame, "SDV15")
            sdv16 = field_by_key(frame, "SDV16")
            sdv12 = field_by_key(frame, "SDV12")
            sdv13 = field_by_key(frame, "SDV13")
            phase_nodes = phase_nodal_u3(frame)
            recovered_phase_nodes, recovered_rows, recovered_audit = recover_phase_nodes(tag, step_name, frame_index, sdv15, nodal_d, elements)
            recovery_rows.extend(recovered_rows)
            recovery_audits.append(recovered_audit)
            recovered_by_tag[tag] = recovered_phase_nodes
            snapshots[tag] = {"sdv15": sdv15, "sdv16": sdv16}
            ru = rf_u(frame, top_set)
            rf_rows.append(dict({"frame_tag": tag, "step": step_name, "frame_index": frame_index}, **ru))
            phase_rows = [
                {"frame_tag": tag, "step": step_name, "frame_index": frame_index, "node": node, "phase_u3": value}
                for node, value in sorted(phase_nodes.items())
            ]
            all_phase_rows.extend(phase_rows)
            sdv15_errors = []
            sdv16_errors = []
            for element in range(1, N_ELEM + 1):
                for ip in range(1, N_IP + 1):
                    key = (element, ip)
                    odb_ip = [k for k, v in ODB_TO_UEL_IP.items() if v == ip][0]
                    d_expected = expected_phase(element, ip, nodal_d, elements)
                    h_expected = h_transfer[key]
                    d_odb = sdv15.get(key, "")
                    h_odb = sdv16.get(key, "")
                    sdv12_odb = sdv12.get(key, "")
                    sdv13_odb = sdv13.get(key, "")
                    d_error = "" if d_odb == "" else float(d_odb) - d_expected
                    h_error = "" if h_odb == "" else float(h_odb) - h_expected
                    if d_error != "":
                        sdv15_errors.append(d_error)
                    if h_error != "":
                        sdv16_errors.append(h_error)
                    row = {
                        "frame_tag": tag,
                        "step": step_name,
                        "frame_index": frame_index,
                        "element": element,
                        "integration_point": ip,
                        "odb_integration_point": odb_ip,
                        "uel_integration_point": ip,
                        "expected_sdv15": d_expected,
                        "odb_sdv15": d_odb,
                        "sdv15_error": d_error,
                        "expected_sdv16": h_expected,
                        "odb_sdv16": h_odb,
                        "sdv16_error": h_error,
                        "odb_sdv12": sdv12_odb,
                        "odb_sdv13": sdv13_odb,
                    }
                    state_rows.append(row)
                    if tag == "F0_ingested":
                        transfer_rows.append(row)
            energy_rows.append({
                "frame_tag": tag,
                "step": step_name,
                "frame_index": frame_index,
                "sdv15_error_metric": metric(sdv15_errors),
                "sdv16_error_metric": metric(sdv16_errors),
                "transfer_H_sum": sum(energy_transfer.values()),
                "odb_H_sum": sum(v for v in sdv16.values()),
                "reconstructed_energy": reconstruct_energy(tag, nodes, elements, recovered_phase_nodes, sdv12, sdv13),
            })

        def compare_frames(name, left, right):
            rows = []
            diffs15 = []
            diffs16 = []
            a = snapshots[left]
            b = snapshots[right]
            for element in range(1, N_ELEM + 1):
                for ip in range(1, N_IP + 1):
                    key = (element, ip)
                    d0 = a["sdv15"].get(key, "")
                    d1 = b["sdv15"].get(key, "")
                    h0 = a["sdv16"].get(key, "")
                    h1 = b["sdv16"].get(key, "")
                    dd = "" if d0 == "" or d1 == "" else float(d1) - float(d0)
                    dh = "" if h0 == "" or h1 == "" else float(h1) - float(h0)
                    if dd != "":
                        diffs15.append(dd)
                    if dh != "":
                        diffs16.append(dh)
                    odb_ip = [k for k, v in ODB_TO_UEL_IP.items() if v == ip][0]
                    rows.append({"element": element, "integration_point": ip, "odb_integration_point": odb_ip, "uel_integration_point": ip, "left": left, "right": right, "sdv15_delta": dd, "sdv16_delta": dh})
            write_csv(os.path.join(out_dir, name), ["element", "integration_point", "odb_integration_point", "uel_integration_point", "left", "right", "sdv15_delta", "sdv16_delta"], rows)
            return {
                "sdv15_delta": metric(diffs15),
                "sdv16_delta": metric(diffs16),
                "d_healing_violations": sum(1 for v in diffs15 if v < -1.0e-10),
                "H_decrease_violations": sum(1 for v in diffs16 if v < -1.0e-10),
            }

        initial_eq = compare_frames("D3A3_INITIAL_VS_EQUILIBRATED.csv", "F0_ingested", "F1_equilibrated")
        eq_rel = compare_frames("D3A3_EQUILIBRATED_VS_RELEASED.csv", "F1_equilibrated", "F3_release_last" if "F3_release_last" in snapshots else "F2_release_first")
        write_csv(os.path.join(out_dir, "D3A3_STATE_BY_FRAME.csv"), list(state_rows[0].keys()), state_rows)
        write_csv(os.path.join(out_dir, "D3A3_TRANSFER_VS_ODB.csv"), list(transfer_rows[0].keys()), transfer_rows)
        write_csv(os.path.join(out_dir, "D3A3_RF_U.csv"), ["frame_tag", "step", "frame_index", "top_node_count", "top_u2_mean", "top_u2_min", "top_u2_max", "top_rf2_sum"], rf_rows)
        write_csv(os.path.join(out_dir, "D3A3_RF_U_CORRECTED.csv"), ["frame_tag", "step", "frame_index", "top_node_count", "top_u2_mean", "top_u2_min", "top_u2_max", "top_rf2_sum"], rf_rows)
        if all_phase_rows:
            write_csv(os.path.join(out_dir, "D3A3_PHASE_NODAL_U_BY_FRAME.csv"), list(all_phase_rows[0].keys()), all_phase_rows)
        write_csv(os.path.join(out_dir, "D3A3_PHASE_NODE_RECOVERY_BY_FRAME.csv"), list(recovery_rows[0].keys()), recovery_rows)
        write_json(os.path.join(out_dir, "D3A3_ENERGY_BY_FRAME.json"), {"classification": "stage_d3a3_energy_by_frame_extracted_corrected", "frames": energy_rows})
        reconstructed_payload = {
            "classification": "stage_d3a3_reconstructed_energy_by_frame_corrected",
            "method": "target_Q4_2x2_bulk_SDV12_plus_AT2_fracture_energy_from_recovered_phase_nodes",
            "frames": [row["reconstructed_energy"] for row in energy_rows],
        }
        write_json(os.path.join(out_dir, "D3A3_RECONSTRUCTED_ENERGY_BY_FRAME.json"), reconstructed_payload)
        write_json(os.path.join(out_dir, "D3A3_RECONSTRUCTED_ENERGY_BY_FRAME_CORRECTED.json"), reconstructed_payload)
        write_json(os.path.join(out_dir, "D3A3_IP_ORDER_AUDIT.json"), {
            "classification": "stage_d3a3_visualization_ip_order_corrected",
            "odb_to_uel_integration_point": ODB_TO_UEL_IP,
            "required_mapping": ["IP 1 -> 1", "IP 2 -> 2", "IP 3 -> 4", "IP 4 -> 3"],
        })
        top_failures = []
        for row in rf_rows:
            if row["frame_tag"] in ("F1_equilibrated", "F3_release_last"):
                mean = row["top_u2_mean"]
                umin = row["top_u2_min"]
                umax = row["top_u2_max"]
                rf2 = row["top_rf2_sum"]
                if mean == "" or abs(float(mean) - CHECKPOINT_U2) > 1.0e-8:
                    top_failures.append("%s top U2 mean mismatch" % row["frame_tag"])
                if umin == "" or umax == "" or abs(float(umax) - float(umin)) > 1.0e-8:
                    top_failures.append("%s top U2 range mismatch" % row["frame_tag"])
                if not is_finite(float(rf2)):
                    top_failures.append("%s top RF2 nonfinite" % row["frame_tag"])
        write_json(os.path.join(out_dir, "D3A3_TOP_SET_AUDIT.json"), {
            "classification": "stage_d3a3_top_set_u_rf_extracted",
            "checkpoint_U2": CHECKPOINT_U2,
            "frames": rf_rows,
            "failures": top_failures,
            "top_set_pass": not top_failures,
        })
        write_json(os.path.join(out_dir, "D3A3_PHASE_NODE_RECOVERY_AUDIT.json"), {
            "classification": "stage_d3a3_phase_nodes_recovered_from_sdv15",
            "frames": recovery_audits,
            "required_recovered_nodes": len(nodal_d),
            "required_complete_elements": len(elements),
        })
        jump = {
            "classification": "stage_d3a3_release_jump_extracted_corrected",
            "initial_vs_equilibrated": initial_eq,
            "equilibrated_vs_released": eq_rel,
        }
        write_json(os.path.join(out_dir, "D3A3_RELEASE_JUMP.json"), jump)
        write_json(os.path.join(out_dir, "D3A3_ENERGY_RELEASE_JUMP_CORRECTED.json"), {
            "classification": "stage_d3a3_corrected_energy_release_jump",
            "F1_to_F3_relative_total_internal_energy_jump": (
                abs(
                    reconstructed_payload["frames"][-1]["total_reconstructed_internal_energy"]
                    - reconstructed_payload["frames"][1]["total_reconstructed_internal_energy"]
                )
                / max(
                    abs(reconstructed_payload["frames"][-1]["total_reconstructed_internal_energy"]),
                    abs(reconstructed_payload["frames"][1]["total_reconstructed_internal_energy"]),
                    1.0e-30,
                )
            ),
            "F1_equilibrated": reconstructed_payload["frames"][1],
            "F3_release_last": reconstructed_payload["frames"][-1],
        })
        write_json(os.path.join(out_dir, "D3A3_EXTRACTION_STATUS.json"), {"classification": "stage_d3a3_extraction_complete_corrected", "odb": str(odb_path), "state_rows": len(state_rows)})
    finally:
        odb.close()
    print("d3a3_extract_ok out_dir=%s" % out_dir)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--odb", required=True)
    parser.add_argument("--package-dir", default="runs/hpc/stage_d3/interrupted_transfer/package")
    parser.add_argument("--model-dir", default="models/state_transfer/d3_interrupted_transfer")
    parser.add_argument("--out-dir", default="runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r2")
    args = parser.parse_args(argv)
    extract(args.odb, args.package_dir, args.model_dir, args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
