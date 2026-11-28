# -*- coding: utf-8 -*-
"""
prepare_method_c_directories.py
===============================
Prepares local directories and PBS scripts for the 4 extra Method C adaptive runs:
1. Novel Problem -> models/computational_cost_analysis/novel/method_c
2. Complex Problem 1 (two hole) -> models/computational_cost_analysis/complex1/method_c
3. Complex Problem 2 (double notch) -> models/computational_cost_analysis/complex2/method_c
4. Complex Problem 3 (mixed load) -> models/computational_cost_analysis/complex3/method_c
"""

import os
import shutil

CONFIGS = [
    {
        "id": "novel",
        "pbs_name": "PK_COST_EXT_NOVEL_MC",
        "src_dir": r"models/novel_inclined_notch_hole",
        "run_campaign_dir": r"models/novel_inclined_notch_hole/run_campaign",
        "dest_dir": r"models/computational_cost_analysis/novel/method_c",
        "remote_dir": "/scratchtemp/pr21vyci/runs/cost_analysis_extended/novel_method_c",
        "runner_py": "run_novel_campaign.py",
        "runner_args": "--run-dir . --publish-dir . --cpus 1 --max-cycles 10",
        "scripts": [
            "run_novel_campaign.py",
            "novel_runtime.py",
            "novel_single_job_orchestrator.py",
            "stall_watchdog.py",
            "generate_novel_inclined_notch_hole_mesh.py"
        ],
        "initial_meshes": [
            "PK_METHOD_C_NOVEL_COARSE_JOB1.inp",
            "PK_METHOD_C_NOVEL_COARSE_JOB1_PHYS.inp"
        ]
    },
    {
        "id": "complex1",
        "pbs_name": "PK_COST_EXT_C1_MC",
        "src_dir": r"models/complex_two_hole",
        "run_campaign_dir": r"models/complex_two_hole/run_campaign",
        "dest_dir": r"models/computational_cost_analysis/complex1/method_c",
        "remote_dir": "/scratchtemp/pr21vyci/runs/cost_analysis_extended/complex1_method_c",
        "runner_py": "run_two_hole_campaign.py",
        "runner_args": "--run-dir . --publish-dir . --cpus 1 --max-cycles 10",
        "scripts": [
            "run_two_hole_campaign.py",
            "two_hole_runtime.py",
            "two_hole_single_job_orchestrator.py",
            "stall_watchdog.py",
            "generate_two_hole_mesh.py"
        ],
        "initial_meshes": [
            "PK_METHOD_C_TWO_HOLE_COARSE_JOB1.inp",
            "PK_METHOD_C_TWO_HOLE_COARSE_JOB1_PHYS.inp"
        ]
    },
    {
        "id": "complex2",
        "pbs_name": "PK_COST_EXT_C2_MC",
        "src_dir": r"models/complex_double_notch",
        "run_campaign_dir": r"models/complex_double_notch/run_campaign",
        "dest_dir": r"models/computational_cost_analysis/complex2/method_c",
        "remote_dir": "/scratchtemp/pr21vyci/runs/cost_analysis_extended/complex2_method_c",
        "runner_py": "run_double_notch_campaign.py",
        "runner_args": "--run-dir . --publish-dir . --cpus 1 --max-cycles 10",
        "scripts": [
            "run_double_notch_campaign.py",
            "double_notch_runtime.py",
            "double_notch_single_job_orchestrator.py",
            "stall_watchdog.py",
            "generate_double_notch_mesh.py"
        ],
        "initial_meshes": [
            "PK_METHOD_C_DOUBLE_NOTCH_COARSE_JOB1.inp",
            "PK_METHOD_C_DOUBLE_NOTCH_COARSE_JOB1_PHYS.inp"
        ]
    },
    {
        "id": "complex3",
        "pbs_name": "PK_COST_EXT_C3_MC",
        "src_dir": r"models/complex_mixed_load",
        "run_campaign_dir": r"models/complex_mixed_load/run_campaign",
        "dest_dir": r"models/computational_cost_analysis/complex3/method_c",
        "remote_dir": "/scratchtemp/pr21vyci/runs/cost_analysis_extended/complex3_method_c",
        "runner_py": "run_mixed_load_campaign.py",
        "runner_args": "--run-dir . --publish-dir . --cpus 1 --max-cycles 10",
        "scripts": [
            "run_mixed_load_campaign.py",
            "mixed_load_runtime.py",
            "mixed_load_single_job_orchestrator.py",
            "stall_watchdog.py",
            "generate_mixed_load_mesh.py"
        ],
        "initial_meshes": [
            "PK_METHOD_C_MIXED_LOAD_COARSE_JOB1.inp",
            "PK_METHOD_C_MIXED_LOAD_COARSE_JOB1_PHYS.inp"
        ]
    }
]

def prepare_config(c):
    dest = c["dest_dir"]
    os.makedirs(dest, exist_ok=True)
    
    # Copy scripts
    for s in c["scripts"]:
        src_s = os.path.join(c["src_dir"], s)
        if os.path.isfile(src_s):
            shutil.copy2(src_s, dest)
            print("Copied %s -> %s" % (src_s, dest))
        else:
            print("Warning: script not found: %s" % src_s)
            
    # Copy initial coarse meshes
    for m in c["initial_meshes"]:
        src_m = os.path.join(c["run_campaign_dir"], m)
        if not os.path.isfile(src_m):
            src_m = os.path.join(c["src_dir"], m)
        if os.path.isfile(src_m):
            shutil.copy2(src_m, dest)
            print("Copied initial mesh %s -> %s" % (src_m, dest))
        else:
            print("Warning: initial mesh not found: %s" % src_m)
            
    # Write PBS script
    pbs_path = os.path.join(dest, "submit_" + c["id"] + "_method_c.pbs")
    pbs_content = f"""#!/bin/bash
#PBS -N {c["pbs_name"]}
#PBS -l select=1:ncpus=1:mpiprocs=1:ompthreads=1:mem=8gb
#PBS -l walltime=72:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o {c["remote_dir"]}/pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail

RUN_DIR="{c["remote_dir"]}"
mkdir -p "${{RUN_DIR}}"
cd "${{RUN_DIR}}"

export JOB_NAME="{c["pbs_name"]}"
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
echo "{c["pbs_name"]} Adaptive Analysis (Method C In-Job Campaign)"
echo "Host: $(hostname)"
echo "Start time: $(date)"
echo "Run directory: ${{RUN_DIR}}"
echo "================================================================="

# Execute in-allocation Python campaign runner on 1 CPU
python3 {c["runner_py"]} {c["runner_args"]}

echo "================================================================="
echo "{c["pbs_name"]} Adaptive Analysis Campaign Finished"
echo "End time: $(date)"
echo "================================================================="
"""
    with open(pbs_path, "w") as f:
        f.write(pbs_content)
    print("Generated PBS script: %s" % pbs_path)

if __name__ == "__main__":
    for c in CONFIGS:
        prepare_config(c)
    print("All Method C directories prepared successfully!")
