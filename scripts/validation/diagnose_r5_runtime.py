"""Diagnostic script for Package 148 R5 runtime and timeout analysis."""
import json
from pathlib import Path

def diagnose():
    runtime_path = Path("results/validation/package148_r5_terminal_runtime.json")
    if not runtime_path.exists():
        print("Missing runtime file")
        return
    data = json.loads(runtime_path.read_text(encoding="utf-8"))
    iterations = data.get("iterations", [])
    print(f"Total outer iteration records: {len(iterations)}")
    print("outer |  delta_d   |   delta_u (mm)  |   delta_h (MPa) |   free_error  | dual_error | phase_iters")
    print("-" * 85)
    for r in iterations:
        outer = r.get("outer")
        dd = r.get("delta_d")
        du = r.get("delta_u")
        dh = r.get("delta_h")
        pi = r.get("phase_iterations")
        free = r.get("free_error")
        dual = r.get("dual_error")
        du_str = f"{du:.4e}" if du is not None else "     None    "
        dh_str = f"{dh:.4e}" if dh is not None else "     None    "
        pi_str = str(pi) if pi is not None else "N/A (cutoff)"
        print(f" {outer:2d}   | {dd:.4e} | {du_str} | {dh_str} | {free:.4e} | {dual:.4e} | {pi_str}")

if __name__ == "__main__":
    diagnose()
