#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REF_INP = ROOT / "models/generated/mode_ii/h0_endpoint_corrected_serial/ModeII_H0_endpoint_corrected_serial.inp"

def main():
    nodes = {}
    with REF_INP.open("r", encoding="utf-8") as f:
        in_node = False
        for line in f:
            l = line.strip()
            if l.lower().startswith("*node") and not in_node:
                in_node = True
                continue
            if in_node:
                if l.startswith("*"):
                    in_node = False
                    continue
                parts = [p.strip() for p in l.split(",") if p.strip()]
                try:
                    nid = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    if nid <= 3998:
                        nodes[nid] = (x, y)
                except Exception:
                    pass

    notch = [nid for nid, (x, y) in nodes.items() if abs(y) <= 1e-5 and -1e-5 <= x <= 0.5 + 1e-5]
    print(f"Total Part-1 physical nodes parsed: {len(nodes)}")
    print(f"Notch nodes (|y|<=1e-5, 0<=x<=0.5): {len(notch)}")

if __name__ == "__main__":
    main()
