#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Update submit_job.pbs with exact module sequence and Strict Unix LF:
1. M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL
2. M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL
"""

import os

def create_pbs(target_dir, job_name):
    pbs_path = os.path.join(target_dir, "submit_job.pbs")
    pbs_content = """#!/bin/bash
#PBS -N %(short_name)s
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -o pbs.out
#PBS -e pbs.err

cd $PBS_O_WORKDIR

# Clean old lock files
rm -f *.lck

module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

python3 /home/pr21vyci/Adaptive_remeshing_clean/scripts/hpc/notify_hpc_event.py --mode start --job-name "%(job_name)s"

abaqus job=%(job_name)s input=%(job_name)s.inp user=f44_mixed_uel_restart_stateinit.for cpus=1 interactive
ABAQUS_RC=$?

python3 /home/pr21vyci/Adaptive_remeshing_clean/scripts/hpc/notify_hpc_event.py --mode end --job-name "%(job_name)s" --exit-code "$ABAQUS_RC"

exit ${ABAQUS_RC}
""" % {"short_name": job_name[:15], "job_name": job_name}

    with open(pbs_path, "wb") as f:
        f.write(pbs_content.replace("\r\n", "\n").encode('utf-8'))
    print("Wrote strict Unix LF submit_job.pbs to %s" % pbs_path)

def main():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    donor_dir = os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL")
    refined_dir = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL")
    
    create_pbs(donor_dir, "M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL")
    create_pbs(refined_dir, "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL")

if __name__ == "__main__":
    main()
