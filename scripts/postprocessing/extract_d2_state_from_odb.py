from __future__ import print_function

import argparse
import csv
import os


N_ELEM = 8


def read_csv(path):
    with open(path, "r") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, fields, rows):
    handle = open(path, "w")
    try:
        handle.write(",".join(fields) + "\n")
        for row in rows:
            handle.write(",".join(str(row.get(f, "")) for f in fields) + "\n")
    finally:
        handle.close()


def target_phase(package_dir):
    rows = read_csv(os.path.join(package_dir, "target_transferred_nodal_d.csv"))
    return dict((int(r["target_node"]), float(r["d_bounded"])) for r in rows)


def target_h(package_dir):
    rows = read_csv(os.path.join(package_dir, "target_transferred_ip_H.csv"))
    return dict(((int(r["target_element"]), int(r["target_ip"])), float(r["H_bounded"])) for r in rows)


def target_elements(package_dir):
    rows = read_csv(os.path.join(package_dir, "target_elements.csv"))
    out = {}
    for r in rows:
        out[int(r["element"])] = [int(r["n1"]), int(r["n2"]), int(r["n3"]), int(r["n4"])]
    return out


def extract(odb_path, package_dir, out_dir):
    from odbAccess import openOdb

    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    d_target = target_phase(package_dir)
    h_target = target_h(package_dir)
    elems = target_elements(package_dir)

    odb = openOdb(path=str(odb_path), readOnly=True)
    step = list(odb.steps.values())[-1]
    frame = step.frames[-1]

    observed_nodes = {}
    u_field = frame.fieldOutputs["U"]
    for value in u_field.values:
        label = int(value.nodeLabel)
        if label in d_target:
            data = value.data
            if len(data) >= 3:
                observed_nodes[label] = float(data[2])
            elif len(data) == 1:
                observed_nodes[label] = float(data[0])

    node_rows = []
    for label in sorted(d_target):
        odb_d = observed_nodes.get(label)
        err = "" if odb_d is None else abs(odb_d - d_target[label])
        node_rows.append({"node": label, "d_transfer": d_target[label], "d_odb": odb_d, "abs_error": err})

    sdv15 = frame.fieldOutputs["SDV15"]
    sdv16 = frame.fieldOutputs["SDV16"]
    sdv15_by_key = {}
    sdv16_by_key = {}
    for value in sdv15.values:
        physical = int(value.elementLabel) - 2 * N_ELEM
        if physical >= 1 and physical <= N_ELEM:
            sdv15_by_key[(physical, int(value.integrationPoint))] = float(value.data)
    for value in sdv16.values:
        physical = int(value.elementLabel) - 2 * N_ELEM
        if physical >= 1 and physical <= N_ELEM:
            sdv16_by_key[(physical, int(value.integrationPoint))] = float(value.data)

    ip_rows = []
    combined = []
    for key in sorted(h_target):
        element, ip = key
        nodal_average = sum(d_target[n] for n in elems[element]) / float(len(elems[element]))
        odb15 = sdv15_by_key.get(key)
        odb16 = sdv16_by_key.get(key)
        err15 = "" if odb15 is None else abs(odb15 - nodal_average)
        err16 = "" if odb16 is None else abs(odb16 - h_target[key])
        row = {
            "element": element,
            "ip": ip,
            "d_interpolated_transfer": nodal_average,
            "sdv15_odb": odb15,
            "sdv15_abs_error": err15,
            "H_transfer": h_target[key],
            "sdv16_odb": odb16,
            "sdv16_abs_error": err16,
        }
        ip_rows.append(row)
        combined.append(row)

    odb.close()
    write_csv(os.path.join(out_dir, "D2A_NODE_COMPARISON.csv"), ["node", "d_transfer", "d_odb", "abs_error"], node_rows)
    write_csv(
        os.path.join(out_dir, "D2A_IP_COMPARISON.csv"),
        ["element", "ip", "d_interpolated_transfer", "sdv15_odb", "sdv15_abs_error", "H_transfer", "sdv16_odb", "sdv16_abs_error"],
        ip_rows,
    )
    write_csv(
        os.path.join(out_dir, "D2A_TRANSFERRED_VS_ODB.csv"),
        ["element", "ip", "d_interpolated_transfer", "sdv15_odb", "sdv15_abs_error", "H_transfer", "sdv16_odb", "sdv16_abs_error"],
        combined,
    )
    print("d2_extract_ok nodes=%d ips=%d" % (len(node_rows), len(ip_rows)))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Extract D2A transfer state from ODB")
    parser.add_argument("--odb", required=True)
    parser.add_argument("--package", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)
    extract(args.odb, args.package, args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
