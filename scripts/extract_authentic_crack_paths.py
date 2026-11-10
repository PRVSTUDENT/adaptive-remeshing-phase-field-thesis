import json
import numpy as np

with open("results/validation/f1709_job2_damage_field.json", "r") as f:
    data = json.load(f)

adapt_inp = "models/pandey_kumar_mode1/203_pk_sec43_secondary_complete/PK_SEC43_F1703_SECONDARY_COMPLETE_ADAPT.inp"
nodes = {}
elements = {}
in_n, in_e = False, False
with open(adapt_inp) as f:
    for line in f:
        l = line.strip().upper()
        if l.startswith("*NODE") and not any(k in l for k in ["PRINT", "FILE", "OUTPUT"]):
            in_n, in_e = True, False
        elif l.startswith("*ELEMENT") and "OUTPUT" not in l:
            in_n, in_e = False, True
        elif l.startswith("*"):
            in_n, in_e = False, False
        elif in_n:
            p = [x.strip() for x in line.strip().split(",")]
            nodes[int(p[0])] = (float(p[1]), float(p[2]))
        elif in_e:
            p = [x.strip() for x in line.strip().split(",")]
            elements[int(p[0])] = [int(x) for x in p[1:] if x]

damage_dict = data["damage_states"]["state_4_severance"]["elem_damage"]

elem_info = []
for eid, conn in elements.items():
    pts = [nodes[n] for n in conn if n in nodes]
    if len(pts) >= 3:
        xc = sum(p[0] for p in pts) / len(pts)
        yc = sum(p[1] for p in pts) / len(pts)
        d = damage_dict.get(str(eid), damage_dict.get(eid, 0.0))
        elem_info.append({"eid": eid, "xc": xc, "yc": yc, "d": d})

def extract_ridge(x_start, x_end, n_bins, y_min, y_max, p_power=6, d_thresh=0.75):
    x_edges = np.linspace(x_start, x_end, n_bins + 1)
    ridge_points = []
    for i in range(n_bins):
        x0, x1 = x_edges[i], x_edges[i+1]
        bin_elems = [e for e in elem_info if x0 <= e["xc"] < x1 and y_min <= e["yc"] <= y_max and e["d"] >= d_thresh]
        if bin_elems:
            w = [e["d"]**p_power for e in bin_elems]
            w_sum = sum(w)
            xr = sum(e["xc"] * w[j] for j, e in enumerate(bin_elems)) / w_sum
            yr = sum(e["yc"] * w[j] for j, e in enumerate(bin_elems)) / w_sum
            best_e = max(bin_elems, key=lambda e: e["d"])
            ridge_points.append({
                "x": round(float(xr), 3),
                "y": round(float(yr), 3),
                "peak_d": round(float(best_e["d"]), 4),
                "peak_eid": best_e["eid"],
                "n_elements": len(bin_elems)
            })
    return ridge_points

prim_ridge = extract_ridge(10.0, 31.8, 25, 52.0, 71.5, p_power=6, d_thresh=0.75)
sec_ridge = extract_ridge(46.5, 65.0, 25, 49.0, 54.0, p_power=6, d_thresh=0.75)

result = {
    "simulation": "Job 1421915.mmaster02 (Package 205)",
    "mesh": "PK_SEC43_F1703_SECONDARY_COMPLETE_ADAPT.inp",
    "total_elements": len(elem_info),
    "primary_crack_ridge": prim_ridge,
    "secondary_crack_ridge": sec_ridge
}

print(f"Extracted {len(prim_ridge)} primary ridge points and {len(sec_ridge)} secondary ridge points.")
with open("results/validation/f1710_authentic_crack_paths.json", "w") as f:
    json.dump(result, f, indent=2)

print("Saved results/validation/f1710_authentic_crack_paths.json")
