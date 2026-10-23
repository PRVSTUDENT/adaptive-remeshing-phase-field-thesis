import csv
import numpy as np

csv_path = "results/validation/mode1_f1597/c3_companion_miseseri_distribution.csv"
rows = list(csv.DictReader(open(csv_path, "r", encoding="utf-8")))

print(f"Total elements: {len(rows)}")

# 1. Absolute error filter
for thresh in [0.05, 0.10, 0.20, 0.50, 1.0]:
    matching = [r for r in rows if float(r["miseseri"]) >= thresh]
    if matching:
        xs = [float(r["x_mm"]) for r in matching]
        ys = [float(r["y_mm"]) for r in matching]
        print(f"MISESERI >= {thresh:.2f}: {len(matching)} elements. X: [{min(xs):.5f}, {max(xs):.5f}], Y: [{min(ys):.5f}, {max(ys):.5f}]")

print("\nTop 10 Peak MISESERI Elements:")
top_abs = sorted(rows, key=lambda r: float(r["miseseri"]), reverse=True)[:10]
for r in top_abs:
    eid = r["element_id"]
    x = float(r["x_mm"])
    y = float(r["y_mm"])
    err = float(r["miseseri"])
    avg = float(r["misesavg"])
    eta = float(r["eta_rel_error"])
    print(f"Elem {eid:>4}: (x={x:.5f}, y={y:.5f}), MISESERI={err:.4f}, MISESAVG={avg:.4f}, eta={eta*100:.1f}%")
