# Abaqus/CAE noGUI: extract MISESERI field from pre-analysis ODB (Stage C Job 3 extract stage).
#
# Environment:
#   MISESERI_CASE_ID
#   MISESERI_ODB_PATH
#   MISESERI_OUTPUT_DIR
#
# Writes miseseri_element_field.csv and EXTRACTION_MANIFEST.json
# No Abaqus/Standard solve. No remesh here (system Python remesher follows).

from __future__ import print_function

import csv
import json
import math
import os
import sys


def _env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError("Missing required environment variable: {0}".format(name))
    return value


def _ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def _sha256_file(path):
    import hashlib

    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        while True:
            block = stream.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def _field_keys(field_outputs):
    try:
        return list(field_outputs.keys())
    except Exception:
        try:
            return field_outputs.keys()
        except Exception:
            return []


def _scalar(value):
    data = value.data
    try:
        return float(data[0])
    except (TypeError, IndexError, ValueError):
        return float(data)


def _element_label(element):
    try:
        return int(element.label)
    except Exception:
        return int(str(element.label).split(".")[-1])


def main():
    print("Abaqus argv: {0}".format(repr(sys.argv)))
    case_id = _env("MISESERI_CASE_ID")
    odb_path = _env("MISESERI_ODB_PATH")
    outdir = _env("MISESERI_OUTPUT_DIR")
    print("case_id={0}".format(case_id))
    print("odb={0}".format(odb_path))
    print("outdir={0}".format(outdir))
    if not os.path.isfile(odb_path):
        raise RuntimeError("ODB does not exist: {0}".format(odb_path))
    _ensure_dir(outdir)

    from odbAccess import openOdb

    odb = openOdb(path=odb_path, readOnly=True)
    step_names = list(odb.steps.keys())
    step = odb.steps[step_names[-1]]
    frame = step.frames[-1]
    fields = frame.fieldOutputs
    keys = _field_keys(fields)
    for req in ("MISESERI", "MISESAVG", "S", "EVOL"):
        if req not in keys:
            odb.close()
            raise RuntimeError("Missing field {0}; available={1}".format(req, keys))

    elset = None
    try:
        for name, s in odb.rootAssembly.elementSets.items():
            up = str(name).upper()
            if up.endswith("UMATELEM") or up == "UMATELEM":
                elset = s
                break
    except Exception:
        elset = None

    miseseri_fo = fields["MISESERI"]
    misesavg_fo = fields["MISESAVG"]
    evol_fo = fields["EVOL"]
    if elset is not None:
        miseseri_fo = miseseri_fo.getSubset(region=elset)
        misesavg_fo = misesavg_fo.getSubset(region=elset)
        evol_fo = evol_fo.getSubset(region=elset)

    miseseri_by = {}
    for v in miseseri_fo.values:
        miseseri_by[_element_label(v.element)] = _scalar(v)
    misesavg_by = {}
    for v in misesavg_fo.values:
        misesavg_by[_element_label(v.element)] = _scalar(v)
    evol_by = {}
    for v in evol_fo.values:
        evol_by[_element_label(v.element)] = _scalar(v)

    try:
        instance = odb.rootAssembly.instances["PART-1-1"]
    except Exception:
        instance = list(odb.rootAssembly.instances.values())[0]

    nodes = {}
    for node in instance.nodes:
        nodes[int(node.label)] = (float(node.coordinates[0]), float(node.coordinates[1]))
    elements = {}
    for element in instance.elements:
        conn = [int(n) for n in element.connectivity]
        if len(conn) >= 4:
            elements[int(element.label)] = conn[:4]

    rows = []
    for lab, val in sorted(miseseri_by.items()):
        conn = elements.get(lab)
        if not conn:
            continue
        if any(n not in nodes for n in conn):
            continue
        pts = [nodes[n] for n in conn]
        edge_sum = 0.0
        for i in range(4):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % 4]
            edge_sum += math.hypot(x1 - x0, y1 - y0)
        h = edge_sum / 4.0
        rows.append(
            {
                "element_label": lab,
                "MISESERI": val,
                "MISESAVG": misesavg_by.get(lab, ""),
                "EVOL": evol_by.get(lab, ""),
                "h_mean": h,
                "xc": sum(p[0] for p in pts) / 4.0,
                "yc": sum(p[1] for p in pts) / 4.0,
                "n1": conn[0],
                "n2": conn[1],
                "n3": conn[2],
                "n4": conn[3],
            }
        )
    odb.close()

    csv_path = os.path.join(outdir, "miseseri_element_field.csv")
    with open(csv_path, "w") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "element_label",
                "MISESERI",
                "MISESAVG",
                "EVOL",
                "h_mean",
                "xc",
                "yc",
                "n1",
                "n2",
                "n3",
                "n4",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    # Quick suitability summary
    vals = [float(r["MISESERI"]) for r in rows]
    vals.sort()
    def pct(p):
        if not vals:
            return None
        i = int(p * (len(vals) - 1))
        return vals[i]

    near_notch = [r for r in rows if -0.05 <= float(r["xc"]) <= 0.2 and abs(float(r["yc"])) <= 0.05]
    support = [r for r in rows if abs(float(r["yc"])) > 0.4]
    mean_notch = (sum(float(r["MISESERI"]) for r in near_notch) / len(near_notch)) if near_notch else None
    mean_support = (sum(float(r["MISESERI"]) for r in support) / len(support)) if support else None

    manifest = {
        "case_id": case_id,
        "odb_path": odb_path,
        "odb_sha256": _sha256_file(odb_path),
        "step": step_names[-1],
        "frame": len(step.frames) - 1,
        "n_rows": len(rows),
        "field_keys": list(keys),
        "miseseri_min": vals[0] if vals else None,
        "miseseri_median": pct(0.5),
        "miseseri_max": vals[-1] if vals else None,
        "mean_near_notch": mean_notch,
        "mean_support_band": mean_support,
        "csv_path": csv_path,
        "status": "pass" if rows and (mean_notch is None or mean_support is None or mean_notch >= mean_support) else "warn_boundary_dominated",
    }
    with open(os.path.join(outdir, "EXTRACTION_MANIFEST.json"), "w") as stream:
        json.dump(manifest, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    if not rows:
        sys.exit(12)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("ERROR: {0}".format(exc))
        sys.exit(12)
