"""
Generates PK_F1720_COARSE_COUPLED.inp from PK_F1719_COARSE_PFM.inp
Enables:
  1. Direct UEL-to-UMAT coupling via PROPS(4) = 1.0 (SCALE_MODE = 1.0: dummy-scaled)
  2. Element output of S, MISESERI, MISESAVG, EVOL, SDV on Layer 3 (ELSET=umatelem)
  3. Seamless continuation across Step 1 (u=0.0050 mm) and Step 2 (u=0.0070 mm)
"""

import os

def generate_deck():
    src_inp = r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\210_f1719_five_hole_coarse_pfm\PK_F1719_COARSE_PFM.inp"
    dst_dir = r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\213_f1720_coarse_coupled"
    dst_inp = os.path.join(dst_dir, "PK_F1720_COARSE_COUPLED.inp")

    assert os.path.exists(src_inp), "Source input deck does not exist: " + src_inp
    os.makedirs(dst_dir, exist_ok=True)

    with open(src_inp, "r") as f:
        lines = f.readlines()

    out_lines = []
    i = 0
    n_lines = len(lines)

    while i < n_lines:
        line = lines[i]

        # Update Heading
        if line.startswith("*HEADING"):
            out_lines.append("*HEADING\n")
            out_lines.append("F1720 Coarse Five-Hole Simulation with Direct UEL-UMAT Coupling (Config B)\n")
            i += 2
            continue

        # Update USER MATERIAL to CONSTANTS=4 and PROPS(4)=1.0
        if line.strip().startswith("*USER MATERIAL"):
            out_lines.append("*USER MATERIAL, CONSTANTS=4\n")
            out_lines.append("210.00, 0.30, 2747.0, 1.0\n")
            i += 2
            continue

        # Update ELEMENT OUTPUT to request S, MISESERI, MISESAVG, EVOL, SDV on umatelem
        if line.strip().startswith("*ELEMENT OUTPUT"):
            out_lines.append("*ELEMENT OUTPUT, ELSET=umatelem\n")
            out_lines.append("S, MISESERI, MISESAVG, EVOL, SDV\n")
            i += 2
            continue

        out_lines.append(line)
        i += 1

    with open(dst_inp, "w") as f:
        f.writelines(out_lines)

    print("Generated %s (%d lines)" % (dst_inp, len(out_lines)))

if __name__ == "__main__":
    generate_deck()
