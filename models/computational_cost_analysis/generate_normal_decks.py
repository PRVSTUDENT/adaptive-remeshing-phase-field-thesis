# -*- coding: utf-8 -*-
"""
generate_normal_decks.py
========================
Generates one-shot zone-refined normal baseline input decks for:
1. Novel Problem (Inclined Notch + Hole) -> PK_COST_NOVEL_NORMAL.inp
2. Complex Problem 1 (Notch + Two Holes) -> PK_COST_C1_NORMAL.inp
3. Complex Problem 2 (Double Notch)     -> PK_COST_C2_NORMAL.inp
4. Complex Problem 3 (Mixed Load)       -> PK_COST_C3_NORMAL.inp

Methodology:
- Extracts full mesh, element definitions (Layers 1, 2, 3), node sets, kinematic coupling (*EQUATION),
  and companion material definition from the terminal physical mesh of the validated campaigns.
- Removes *INITIAL CONDITIONS (ensuring analysis starts from pristine intact state d=0 at load=0).
- Inserts 2-step loading:
  Step 1: Precritical displacement control to onset (e.g. uy = 0.0045 mm)
  Step 2: Arc-length (RIKS) controlled advance to terminal displacement
- Generates PBS submission scripts strictly conforming to 1 CPU, 8 GB RAM, 72h walltime, /scratchtemp.
"""

import os
import re

PROBLEMS = [
    {
        "id": "novel",
        "name": "PK_COST_NOVEL_NORMAL",
        "pbs_name": "PK_COST_EXT_NOVEL_N",
        "source_deck": r"models/novel_inclined_notch_hole/run_campaign/PK_METHOD_C_NOVEL_CYCLE8.inp",
        "out_dir": r"models/computational_cost_analysis/novel/normal",
        "remote_dir": "/scratchtemp/pr21vyci/runs/cost_analysis_extended/novel_normal",
        "precritical_uy": 0.0045,
        "terminal_uy": 0.008584,
        "is_mixed": False,
    },
    {
        "id": "complex1",
        "name": "PK_COST_C1_NORMAL",
        "pbs_name": "PK_COST_EXT_C1_N",
        "source_deck": r"models/complex_two_hole/run_campaign/PK_METHOD_C_TWO_HOLE_CYCLE5.inp",
        "out_dir": r"models/computational_cost_analysis/complex1/normal",
        "remote_dir": "/scratchtemp/pr21vyci/runs/cost_analysis_extended/complex1_normal",
        "precritical_uy": 0.0045,
        "terminal_uy": 0.007064,
        "is_mixed": False,
    },
    {
        "id": "complex2",
        "name": "PK_COST_C2_NORMAL",
        "pbs_name": "PK_COST_EXT_C2_N",
        "source_deck": r"models/complex_double_notch/run_campaign/PK_METHOD_C_DOUBLE_NOTCH_CYCLE6.inp",
        "out_dir": r"models/computational_cost_analysis/complex2/normal",
        "remote_dir": "/scratchtemp/pr21vyci/runs/cost_analysis_extended/complex2_normal",
        "precritical_uy": 0.0045,
        "terminal_uy": 0.007710,
        "is_mixed": False,
    },
    {
        "id": "complex3",
        "name": "PK_COST_C3_NORMAL",
        "pbs_name": "PK_COST_EXT_C3_N",
        "source_deck": r"models/complex_mixed_load/run_campaign/PK_METHOD_C_MIXED_LOAD_CYCLE8.inp",
        "out_dir": r"models/computational_cost_analysis/complex3/normal",
        "remote_dir": "/scratchtemp/pr21vyci/runs/cost_analysis_extended/complex3_normal",
        "precritical_uy": 0.0045,
        "terminal_uy": 0.008586,
        "is_mixed": True,
        "precritical_ux": 0.00225,
        "terminal_ux": 0.004293,
    }
]

def make_normal_deck(p):
    src = p["source_deck"]
    out_path = os.path.join(p["out_dir"], p["name"] + ".inp")
    
    with open(src, "r") as f:
        lines = f.readlines()
        
    out_lines = []
    skip_initial_conditions = False
    
    for line in lines:
        u = line.strip().upper()
        if u.startswith("*INITIAL CONDITIONS"):
            skip_initial_conditions = True
            continue
        if skip_initial_conditions:
            if u.startswith("*AMPLITUDE") or u.startswith("** ====") or u.startswith("*STEP"):
                skip_initial_conditions = False
            else:
                continue
        if u.startswith("** STEP 1") or u.startswith("*STEP, NAME=STEP-1"):
            break
        out_lines.append(line)
        
    # Append clean 2-step loading:
    # Step 1: Precritical loading
    out_lines.append("** ==========================================================\n")
    out_lines.append("** STEP 1: Pre-critical Baseline Loading to uy = %.6f mm\n" % p["precritical_uy"])
    out_lines.append("** ==========================================================\n")
    out_lines.append("*STEP, NAME=Step-1, NLGEOM=NO, INC=1000\n")
    out_lines.append("*STATIC\n")
    out_lines.append("0.02, 1.0, 1.0E-14, 0.05\n")
    out_lines.append("*BOUNDARY\n")
    if p["is_mixed"]:
        out_lines.append("N_BOTTOM, 1, 2, 0.0\n")
        out_lines.append("N_RP, 1, 1, %.8e\n" % p["precritical_ux"])
        out_lines.append("N_RP, 2, 2, %.8e\n" % p["precritical_uy"])
    else:
        out_lines.append("N_BOTTOM, 2, 2, 0.0\n")
        out_lines.append("N_PIN, 1, 1, 0.0\n")
        out_lines.append("N_RP, 2, 2, %.8e\n" % p["precritical_uy"])
    out_lines.append("*OUTPUT, FIELD, FREQUENCY=1\n")
    out_lines.append("*NODE OUTPUT\nU\n")
    out_lines.append("*NODE OUTPUT, NSET=N_RP\nRF\n")
    out_lines.append("*ELEMENT OUTPUT, ELSET=umatelem\nSDV\n")
    if p["is_mixed"]:
        out_lines.append("*NODE PRINT, FREQ=1, NSET=N_RP\nU1, U2, RF1, RF2\n")
    else:
        out_lines.append("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
    out_lines.append("*END STEP\n")
    
    # Step 2: Forward propagation with RIKS control
    out_lines.append("** ==========================================================\n")
    out_lines.append("** STEP 2: Forward Crack Propagation to terminal uy = %.6f mm\n" % p["terminal_uy"])
    out_lines.append("** ==========================================================\n")
    out_lines.append("*STEP, NAME=Step-2, NLGEOM=NO, INC=5000\n")
    out_lines.append("*STATIC, RIKS\n")
    out_lines.append("0.01, 1.0, 1.0E-14, 0.05, 1.0\n")
    out_lines.append("*BOUNDARY, OP=MOD\n")
    if p["is_mixed"]:
        out_lines.append("N_RP, 1, 1, %.8e\n" % p["terminal_ux"])
        out_lines.append("N_RP, 2, 2, %.8e\n" % p["terminal_uy"])
    else:
        out_lines.append("N_RP, 2, 2, %.8e\n" % p["terminal_uy"])
    out_lines.append("*OUTPUT, FIELD, FREQUENCY=1\n")
    out_lines.append("*NODE OUTPUT\nU\n")
    out_lines.append("*NODE OUTPUT, NSET=N_RP\nRF\n")
    out_lines.append("*ELEMENT OUTPUT, ELSET=umatelem\nSDV\n")
    if p["is_mixed"]:
        out_lines.append("*NODE PRINT, FREQ=1, NSET=N_RP\nU1, U2, RF1, RF2\n")
    else:
        out_lines.append("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
    out_lines.append("*END STEP\n")
    
    with open(out_path, "w") as f:
        f.writelines(out_lines)
    print("Generated deck: %s (%d lines)" % (out_path, len(out_lines)))
    
    # Generate PBS submission script
    pbs_path = os.path.join(p["out_dir"], "submit_" + p["id"] + "_normal.pbs")
    pbs_content = f"""#!/bin/bash
#PBS -N {p["pbs_name"]}
#PBS -l select=1:ncpus=1:mpiprocs=1:ompthreads=1:mem=8gb
#PBS -l walltime=72:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o {p["remote_dir"]}/pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail

RUN_DIR="{p["remote_dir"]}"
mkdir -p "${{RUN_DIR}}"
cd "${{RUN_DIR}}"

export JOB_NAME="{p["pbs_name"]}"
export NOTIFICATION_CONFIG="${{NOTIFICATION_CONFIG:-${{HOME}}/.config/adaptive-remeshing/notifications.env}}"

if [ -f "${{RUN_DIR}}/job_notifications.sh" ]; then
    source "${{RUN_DIR}}/job_notifications.sh"
elif [ -f "${{HOME}}/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh" ]; then
    source "${{HOME}}/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh"
fi

if type notification_load_config >/dev/null 2>&1; then
    notification_load_config
    notification_install_terminal_trap
    notify_start
fi

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "================================================================="
echo "{p["name"]} Baseline Analysis (One-Shot Zone-Refined)"
echo "Host: $(hostname)"
echo "Start time: $(date)"
echo "Run directory: ${{RUN_DIR}}"
echo "================================================================="

# Execute Abaqus solver on 1 CPU
rm -f {p["name"]}.lck
abaqus job={p["name"]} input={p["name"]} user=f42_mixed_uel.for cpus=1 interactive

echo "================================================================="
echo "{p["name"]} Baseline Analysis Solver Finished"
echo "End time: $(date)"
echo "================================================================="
"""
    with open(pbs_path, "w") as f:
        f.write(pbs_content)
    print("Generated PBS script: %s" % pbs_path)

if __name__ == "__main__":
    for p in PROBLEMS:
        make_normal_deck(p)
    print("All normal baseline decks and PBS scripts successfully generated!")
